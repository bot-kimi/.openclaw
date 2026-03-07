#!/usr/bin/env python3
"""
WakeWatch: run a command, watch output, emit JSONL events on regex matches.
Stdlib-only prototype for event-driven wakeups.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import threading
from dataclasses import dataclass
from queue import Empty, Queue
from string import Template
from typing import List, Pattern


@dataclass
class Rule:
    name: str
    pattern_text: str
    pattern: Pattern[str]


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def append_event(path: str, event: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def parse_rule(raw: str) -> Rule:
    if "::" not in raw:
        raise ValueError(f"Invalid --rule format: {raw!r}. Expected 'name::regex'.")
    name, regex = raw.split("::", 1)
    name = name.strip()
    regex = regex.strip()
    if not name or not regex:
        raise ValueError(f"Invalid --rule: {raw!r}")
    return Rule(name=name, pattern_text=regex, pattern=re.compile(regex))


def reader_thread(stream, source: str, out_queue: Queue):
    try:
        for line in iter(stream.readline, ""):
            out_queue.put((source, line.rstrip("\n")))
    finally:
        stream.close()


def run_hook(command_template: str | None, payload: dict) -> None:
    if not command_template:
        return

    flat = {
        "type": str(payload.get("type", "")),
        "rule": str(payload.get("rule", "")),
        "source": str(payload.get("source", "")),
        "line": str(payload.get("line", "")),
        "group1": "",
        "group2": "",
        "group3": "",
        "group4": "",
        "group5": "",
        "exitCode": str(payload.get("exitCode", "")),
        "ts": str(payload.get("ts", "")),
    }
    groups = payload.get("groups") or []
    for i in range(1, 6):
        if i <= len(groups):
            flat[f"group{i}"] = str(groups[i - 1])

    cmd = Template(command_template).safe_substitute(flat)
    completed = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if completed.returncode != 0:
        print(f"[wakewatch] hook failed rc={completed.returncode}: {cmd}")
        if completed.stderr:
            print(f"[wakewatch] hook stderr: {completed.stderr.strip()}")


def emit_match_event(line: str, source: str, rules: List[Rule], events_path: str, on_match_cmd: str | None) -> None:
    for r in rules:
        m = r.pattern.search(line)
        if not m:
            continue
        event = {
            "ts": utc_now_iso(),
            "type": "match",
            "rule": r.name,
            "source": source,
            "line": line,
            "groups": list(m.groups()),
        }
        append_event(events_path, event)
        print(f"[wakewatch] matched rule={r.name} groups={event['groups']}")
        run_hook(on_match_cmd, event)


def run_watch(
    cmd: str,
    rules: List[Rule],
    events_path: str,
    cwd: str | None = None,
    on_start_cmd: str | None = None,
    on_match_cmd: str | None = None,
    on_exit_cmd: str | None = None,
) -> int:
    start_event = {
        "ts": utc_now_iso(),
        "type": "start",
        "cmd": cmd,
        "cwd": cwd or os.getcwd(),
        "rules": [{"name": r.name, "regex": r.pattern_text} for r in rules],
    }
    append_event(events_path, start_event)
    run_hook(on_start_cmd, start_event)
    print(f"[wakewatch] started: {cmd}")

    proc = subprocess.Popen(
        cmd,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    q: Queue = Queue()
    t_out = threading.Thread(target=reader_thread, args=(proc.stdout, "stdout", q), daemon=True)
    t_err = threading.Thread(target=reader_thread, args=(proc.stderr, "stderr", q), daemon=True)
    t_out.start()
    t_err.start()

    while True:
        try:
            source, line = q.get(timeout=0.1)
            print(f"[{source}] {line}")
            emit_match_event(line, source, rules, events_path, on_match_cmd)
        except Empty:
            if proc.poll() is not None:
                break

    while not q.empty():
        source, line = q.get_nowait()
        print(f"[{source}] {line}")
        emit_match_event(line, source, rules, events_path, on_match_cmd)

    code = proc.wait()
    exit_event = {"ts": utc_now_iso(), "type": "exit", "exitCode": code}
    append_event(events_path, exit_event)
    run_hook(on_exit_cmd, exit_event)
    print(f"[wakewatch] exited with code {code}")
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description="Run command and emit JSONL events for regex matches.")
    parser.add_argument("--cmd", required=True, help="Shell command to run, e.g. 'bash ./command.sh'")
    parser.add_argument("--rule", action="append", default=[], help="Rule format: name::regex (repeatable)")
    parser.add_argument("--events", required=True, help="Path to JSONL events file")
    parser.add_argument("--cwd", default=None, help="Working directory for command")
    parser.add_argument("--on-start-cmd", default=None, help="Shell hook on start event (Template vars: $type $ts)")
    parser.add_argument("--on-match-cmd", default=None, help="Shell hook on match event (vars: $rule $line $group1..$group5)")
    parser.add_argument("--on-exit-cmd", default=None, help="Shell hook on exit event (vars: $exitCode)")

    args = parser.parse_args()
    rules = [parse_rule(r) for r in args.rule]
    return run_watch(
        args.cmd,
        rules,
        args.events,
        args.cwd,
        args.on_start_cmd,
        args.on_match_cmd,
        args.on_exit_cmd,
    )


if __name__ == "__main__":
    sys.exit(main())
