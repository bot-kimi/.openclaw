#!/usr/bin/env python3
"""
WakeBridge: run a command and fire OpenClaw system events (start/exit).
Designed for webchat/session wakeups without subagents.
"""

from __future__ import annotations

import argparse
import datetime as dt
import shlex
import subprocess
import sys


def run_system_event(text: str, mode: str = "now") -> None:
    cmd = ["openclaw", "system", "event", "--mode", mode, "--text", text]
    p = subprocess.run(cmd, text=True, capture_output=True)
    if p.returncode != 0:
        sys.stderr.write(f"[wakebridge] system event failed rc={p.returncode}: {p.stderr}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Run command and trigger OpenClaw system events on start/exit.")
    ap.add_argument("--cmd", required=True, help="Shell command to run")
    ap.add_argument("--label", default="任务", help="Display label")
    ap.add_argument("--cwd", default=None, help="Working directory")
    ap.add_argument("--emit-start", action="store_true", help="Also emit start event")
    ap.add_argument("--tail-lines", type=int, default=12, help="Tail lines in exit event")
    args = ap.parse_args()

    start_at = dt.datetime.now(dt.timezone.utc)
    if args.emit_start:
        run_system_event(
            f"[WakeBridge] {args.label} started. cmd={args.cmd} at {start_at.isoformat()} UTC. "
            "Send a short user-facing update in Chinese: 任务已开始执行。"
        )

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
    tail_block = "\\n".join(tail) if tail else "(no output)"

    status = "SUCCESS" if code == 0 else "FAILED"
    run_system_event(
        f"[WakeBridge] {args.label} finished. status={status} exit={code} duration={sec}s. "
        f"cmd={args.cmd}. Tail output:\n{tail_block}\n"
        "Please send a concise user-facing completion update in Chinese with result summary."
    )

    return code


if __name__ == "__main__":
    raise SystemExit(main())
