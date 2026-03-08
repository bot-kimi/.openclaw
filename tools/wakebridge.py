#!/usr/bin/env python3
"""
WakeBridge: run a command and fire OpenClaw system events (start/exit).
Designed for webchat/session wakeups without subagents.
Now also registers tasks on the TaskBoard for monitoring.
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
import urllib.request
import uuid
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
TASKBOARD_PY = TOOLS_DIR / "taskboard.py"
TASKBOARD_URL = "http://127.0.0.1:9876/api/tasks"


def run_system_event(text: str, mode: str = "now") -> None:
    cmd = ["openclaw", "system", "event", "--mode", mode, "--text", text]
    p = subprocess.run(cmd, text=True, capture_output=True)
    if p.returncode != 0:
        sys.stderr.write(f"[wakebridge] system event failed rc={p.returncode}: {p.stderr}\n")


def _taskboard_running() -> bool:
    try:
        with urllib.request.urlopen(TASKBOARD_URL, timeout=1.2) as resp:
            return resp.status == 200
    except Exception:
        return False


def _taskboard_add(task_id: str, label: str, cmd_str: str, start_iso: str) -> None:
    if not TASKBOARD_PY.exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(TASKBOARD_PY), "add",
             "--id", task_id, "--label", label, "--cmd", cmd_str,
             "--status", "running", "--start", start_iso],
            capture_output=True, text=True,
        )
    except Exception as exc:
        sys.stderr.write(f"[wakebridge] taskboard add failed: {exc}\n")


def _taskboard_update(task_id: str, status: str, end_iso: str,
                      duration: int, exit_code: int, output: str) -> None:
    if not TASKBOARD_PY.exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(TASKBOARD_PY), "update",
             "--id", task_id, "--status", status, "--end", end_iso,
             "--duration", str(duration), "--exit-code", str(exit_code),
             "--output", output],
            capture_output=True, text=True,
        )
    except Exception as exc:
        sys.stderr.write(f"[wakebridge] taskboard update failed: {exc}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Run command and trigger OpenClaw system events on start/exit.")
    ap.add_argument("--cmd", required=True, help="Shell command to run")
    ap.add_argument("--label", default="任务", help="Display label")
    ap.add_argument("--cwd", default=None, help="Working directory")
    ap.add_argument("--emit-start", action="store_true", help="Also emit start event")
    ap.add_argument("--tail-lines", type=int, default=12, help="Tail lines in exit event")
    ap.add_argument("--no-taskboard", action="store_true", help="Skip taskboard registration")
    args = ap.parse_args()

    task_id = uuid.uuid4().hex[:8]
    start_at = dt.datetime.now(dt.timezone.utc)
    start_iso = start_at.isoformat(timespec="seconds")

    if not args.no_taskboard and not _taskboard_running():
        msg = (
            "WB_ERROR reason=taskboard_down "
            f"label={args.label} hint='start taskboard: python3 tools/taskboard.py serve --host 0.0.0.0 --port 9876'"
        )
        run_system_event(msg)
        sys.stderr.write("[wakebridge] TaskBoard is not running on :9876; refusing long task.\n")
        return 97

    if args.emit_start:
        run_system_event(
            f"WB_START label={args.label} ts={start_iso} cmd={args.cmd}"
        )

    if not args.no_taskboard:
        _taskboard_add(task_id, args.label, args.cmd, start_iso)

    proc = subprocess.Popen(
        args.cmd,
        shell=True,
        cwd=args.cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    tail: list[str] = []
    assert proc.stdout is not None
    for raw in proc.stdout:
        line = raw.rstrip("\n")
        if line:
            tail.append(line)
            if len(tail) > max(1, args.tail_lines):
                tail.pop(0)

    code = proc.wait()
    end_at = dt.datetime.now(dt.timezone.utc)
    sec = int((end_at - start_at).total_seconds())
    tail_block = "\n".join(tail) if tail else "(no output)"

    status = "SUCCESS" if code == 0 else "FAILED"
    compact_tail = tail_block.replace("\n", "\\n")
    run_system_event(
        f"WB_DONE label={args.label} status={status} exit={code} duration_s={sec} "
        f"cmd={args.cmd} tail={compact_tail}"
    )

    if not args.no_taskboard:
        tb_status = "completed" if code == 0 else "failed"
        _taskboard_update(task_id, tb_status, end_at.isoformat(timespec="seconds"),
                          sec, code, tail_block)

    return code


if __name__ == "__main__":
    raise SystemExit(main())
