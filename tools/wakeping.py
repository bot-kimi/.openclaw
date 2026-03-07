#!/usr/bin/env python3
"""
WakePing: OpenClaw-connected long-command notifier (start + exit).

No output pattern required. Sends one message when command starts,
and one message when it exits.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import subprocess
import sys
from typing import Deque


def send_openclaw_message(channel: str, target: str, text: str) -> int:
    cmd = [
        "openclaw",
        "message",
        "send",
        "--channel",
        channel,
        "--target",
        target,
        "--message",
        text,
    ]
    p = subprocess.run(cmd, text=True, capture_output=True)
    if p.returncode != 0:
        sys.stderr.write(f"[wakeping] send failed rc={p.returncode}: {p.stderr}\n")
    return p.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run command and notify start/exit via OpenClaw message send.")
    parser.add_argument("--cmd", required=True, help="Shell command to run, e.g. 'bash ./command.sh'")
    parser.add_argument("--channel", required=True, help="OpenClaw channel, e.g. telegram/discord/signal")
    parser.add_argument("--target", required=True, help="OpenClaw message target for channel")
    parser.add_argument("--label", default="任务", help="Display label in notifications")
    parser.add_argument("--cwd", default=None, help="Working directory")
    parser.add_argument("--tail-lines", type=int, default=8, help="How many last output lines to include on exit")

    args = parser.parse_args()

    start_at = dt.datetime.now(dt.timezone.utc)
    start_msg = f"⏳ {args.label} 已开始执行\n命令: {args.cmd}\n时间(UTC): {start_at.isoformat()}"
    send_openclaw_message(args.channel, args.target, start_msg)

    proc = subprocess.Popen(
        args.cmd,
        shell=True,
        cwd=args.cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    tail: Deque[str] = collections.deque(maxlen=max(1, args.tail_lines))

    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.rstrip("\n")
        if line:
            tail.append(line)
            print(line)

    code = proc.wait()
    end_at = dt.datetime.now(dt.timezone.utc)
    duration = int((end_at - start_at).total_seconds())

    status = "✅ 成功" if code == 0 else f"❌ 失败 (exit={code})"
    tail_text = "\n".join(f"- {x}" for x in tail) if tail else "- (无输出)"
    end_msg = (
        f"{status} {args.label} 执行结束\n"
        f"命令: {args.cmd}\n"
        f"耗时: {duration}s\n"
        f"最后输出:\n{tail_text}"
    )
    send_openclaw_message(args.channel, args.target, end_msg)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
