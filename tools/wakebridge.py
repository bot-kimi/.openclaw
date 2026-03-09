#!/usr/bin/env python3
"""
WakeBridge: run a command and fire OpenClaw system events (start/exit).
Designed for webchat/session wakeups without subagents.
Now also registers tasks on the TaskBoard for monitoring.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import signal
import subprocess
import sys
import threading
import urllib.request
import uuid
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
TASKBOARD_PY = TOOLS_DIR / "taskboard.py"
TASKBOARD_URL = "http://127.0.0.1:9876/api/tasks"
TASKBOARD_LOG_DIR = TOOLS_DIR.parent / ".openclaw" / "taskboard" / "logs"


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


def _taskboard_add(task_id: str, label: str, cmd_str: str, start_iso: str,
                   log_file: str, tags: str | None = None,
                   pid: int | None = None, pgid: int | None = None) -> None:
    if not TASKBOARD_PY.exists():
        return
    try:
        cmd = [sys.executable, str(TASKBOARD_PY), "add",
               "--id", task_id, "--label", label, "--cmd", cmd_str,
               "--status", "running", "--start", start_iso,
               "--log-file", log_file]
        if tags:
            cmd += ["--tags", tags]
        if pid is not None:
            cmd += ["--pid", str(pid)]
        if pgid is not None:
            cmd += ["--pgid", str(pgid)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            sys.stderr.write(f"[wakebridge] taskboard add rc={p.returncode}: {p.stderr}\n")
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
    ap.add_argument("--tags", default=None, help="Comma-separated tags for taskboard")
    ap.add_argument("--no-taskboard", action="store_true", help="Skip taskboard registration")
    ap.add_argument("--timeout-sec", type=int, default=None,
                    help="Kill process after N seconds and mark as timed-out")
    ap.add_argument("--no-system-alarm", action="store_true",
                    help="Skip automatic system-alarm for long tasks")
    args = ap.parse_args()

    task_id = uuid.uuid4().hex[:8]
    start_at = dt.datetime.now(dt.timezone.utc)
    start_iso = start_at.isoformat(timespec="seconds")
    TASKBOARD_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = TASKBOARD_LOG_DIR / f"{task_id}.log"
    log_path.write_text("", encoding="utf-8")

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


    # ── System-alarm setup ──────────────────────────────────────────
    alarm_id: str | None = None
    alarm_proc: subprocess.Popen | None = None
    alarm_done = threading.Event()
    alarm_start_iso = ""

    task_tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    is_alarm_task = "alarm" in task_tags or "system-alarm" in task_tags
    should_alarm = (
        not args.no_system_alarm
        and not args.no_taskboard
        and not is_alarm_task
        and args.timeout_sec is not None
        and args.timeout_sec > 20
    )

    # Immediate warning when starting a non-alarm task without system-alarm protection
    if not args.no_taskboard and not is_alarm_task and not should_alarm:
        run_system_event(
            f"WB_WARN label={args.label} reason=missing_system_alarm "
            f"hint='set --timeout-sec > 20 or run a paired alarm task'"
        )

    if should_alarm:
        alarm_id = uuid.uuid4().hex[:8]
        alarm_delay = args.timeout_sec + 10
        alarm_label = f"sysalarm-{args.label}"
        alarm_tags_str = f"system-alarm,parent:{task_id}"
        alarm_start_iso = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        alarm_log = TASKBOARD_LOG_DIR / f"{alarm_id}.log"
        alarm_log.write_text("", encoding="utf-8")
        _taskboard_add(alarm_id, alarm_label, f"sleep {alarm_delay}",
                       alarm_start_iso, str(alarm_log), alarm_tags_str)
        alarm_proc = subprocess.Popen(
            f"sleep {alarm_delay}", shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        _aid, _atid, _albl, _aiso = alarm_id, task_id, args.label, alarm_start_iso

        def _alarm_watcher() -> None:
            assert alarm_proc is not None
            rc = alarm_proc.wait()
            if rc == 0 and not alarm_done.is_set():
                alarm_done.set()
                end = dt.datetime.now(dt.timezone.utc)
                end_iso = end.isoformat(timespec="seconds")
                dur = int((end - dt.datetime.fromisoformat(_aiso)).total_seconds())
                _taskboard_update(_aid, "completed", end_iso, dur, 0,
                                  f"system-alarm fired for {_atid}")
                run_system_event(
                    f"WB_ALARM parent={_atid} label={_albl} "
                    f"msg=System alarm fired — task may need attention"
                )

        threading.Thread(target=_alarm_watcher, daemon=True).start()

    # ── Run command ─────────────────────────────────────────────────
    proc = subprocess.Popen(
        args.cmd,
        shell=True,
        cwd=args.cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        preexec_fn=os.setsid,
    )

    proc_pgid = None
    try:
        proc_pgid = os.getpgid(proc.pid)
    except OSError:
        proc_pgid = None

    if not args.no_taskboard:
        _taskboard_add(task_id, args.label, args.cmd, start_iso, str(log_path), args.tags,
                       pid=proc.pid, pgid=proc_pgid)

    timed_out = False
    timeout_timer: threading.Timer | None = None
    if args.timeout_sec and args.timeout_sec > 0:
        def _on_timeout() -> None:
            nonlocal timed_out
            timed_out = True
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except OSError:
                try:
                    proc.kill()
                except OSError:
                    pass

        timeout_timer = threading.Timer(args.timeout_sec, _on_timeout)
        timeout_timer.start()

    tail: list[str] = []
    assert proc.stdout is not None
    for raw in proc.stdout:
        with log_path.open("a", encoding="utf-8") as lf:
            lf.write(raw)
        line = raw.rstrip("\n")
        if line:
            tail.append(line)
            if len(tail) > max(1, args.tail_lines):
                tail.pop(0)

    code = proc.wait()
    end_at = dt.datetime.now(dt.timezone.utc)
    sec = int((end_at - start_at).total_seconds())

    if timeout_timer:
        timeout_timer.cancel()

    tail_block = "\n".join(tail) if tail else "(no output)"
    if timed_out:
        tail_block = f"TIMEOUT after {args.timeout_sec}s — process killed\n{tail_block}"
        code = 124

    status = "TIMEOUT" if timed_out else ("SUCCESS" if code == 0 else "FAILED")
    compact_tail = tail_block.replace("\n", "\\n")
    run_system_event(
        f"WB_DONE label={args.label} status={status} exit={code} duration_s={sec} "
        f"cmd={args.cmd} log={log_path} tail={compact_tail}"
    )

    if not args.no_taskboard:
        tb_status = "completed" if code == 0 and not timed_out else "failed"
        _taskboard_update(task_id, tb_status, end_at.isoformat(timespec="seconds"),
                          sec, code, tail_block)

    # ── Cancel system-alarm if still running ────────────────────────
    if alarm_proc is not None and not alarm_done.is_set():
        alarm_done.set()
        try:
            alarm_proc.kill()
            alarm_proc.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            pass
        end = dt.datetime.now(dt.timezone.utc)
        end_iso = end.isoformat(timespec="seconds")
        dur = int((end - dt.datetime.fromisoformat(alarm_start_iso)).total_seconds())
        _taskboard_update(alarm_id, "cancelled", end_iso, dur, -1,
                          f"auto-cancelled: parent {task_id} finished ({status})")

    return code


if __name__ == "__main__":
    raise SystemExit(main())
