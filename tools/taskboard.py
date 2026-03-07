#!/usr/bin/env python3
"""
TaskBoard: lightweight task monitoring for background jobs.
Stdlib only. Data stored in .openclaw/taskboard/tasks.json.
"""

from __future__ import annotations

import argparse
import datetime as dt
import http.server
import json
import sys
import uuid
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE / ".openclaw" / "taskboard"
TASKS_FILE = DATA_DIR / "tasks.json"


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load() -> list[dict[str, Any]]:
    if not TASKS_FILE.exists():
        return []
    return json.loads(TASKS_FILE.read_text())


def _save(tasks: list[dict[str, Any]]) -> None:
    _ensure_dir()
    TASKS_FILE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n")


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# ── commands ────────────────────────────────────────────────────────

def cmd_add(args: argparse.Namespace) -> int:
    tasks = _load()
    task_id = args.id or uuid.uuid4().hex[:8]
    task: dict[str, Any] = {
        "id": task_id,
        "label": args.label,
        "cmd": args.cmd or "",
        "status": args.status or "running",
        "start": args.start or _now_iso(),
        "end": None,
        "duration": None,
        "exitCode": None,
        "lastOutput": args.output or "",
    }
    tasks.append(task)
    _save(tasks)
    print(task_id)
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    tasks = _load()
    found = [t for t in tasks if t["id"] == args.id]
    if not found:
        sys.stderr.write(f"task {args.id} not found\n")
        return 1
    t = found[0]
    if args.status:
        t["status"] = args.status
    if args.end:
        t["end"] = args.end
    if args.duration is not None:
        t["duration"] = args.duration
    if args.exit_code is not None:
        t["exitCode"] = args.exit_code
    if args.output is not None:
        t["lastOutput"] = args.output
    _save(tasks)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    tasks = _load()
    if args.status:
        tasks = [t for t in tasks if t["status"] == args.status]
    if args.json_out:
        print(json.dumps(tasks, indent=2, ensure_ascii=False))
    else:
        for t in tasks:
            dur = t.get("duration") if t.get("duration") is not None else ""
            print(f'{t["id"]:>10}  {t["status"]:<10}  {dur:>6}s  {t["label"]}')
    return 0


def _build_html(tasks: list[dict[str, Any]]) -> str:
    rows = ""
    for t in tasks:
        sc = {"running": "#2196F3", "completed": "#4CAF50", "failed": "#f44336"}.get(
            t.get("status", ""), "#999"
        )
        last = (t.get("lastOutput") or "").replace("&", "&amp;").replace("<", "&lt;").replace("\n", "<br>")
        rows += (
            "<tr>"
            f'<td>{t.get("id","")}</td>'
            f'<td>{t.get("label","")}</td>'
            f'<td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{t.get("cmd","")}</td>'
            f'<td><span style="color:{sc};font-weight:700">{t.get("status","")}</span></td>'
            f'<td>{t.get("start","")}</td>'
            f'<td>{t.get("end","") or ""}</td>'
            f'<td>{t.get("duration") if t.get("duration") is not None else ""}</td>'
            f'<td>{t.get("exitCode","") if t.get("exitCode") is not None else ""}</td>'
            f'<td style="max-width:340px;overflow:auto;white-space:pre-wrap;font-size:12px">{last}</td>'
            "</tr>\n"
        )
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        "<title>TaskBoard</title>"
        '<meta http-equiv="refresh" content="5">'
        "<style>"
        "body{font-family:system-ui,sans-serif;margin:20px;background:#1a1a2e;color:#e0e0e0}"
        "h1{color:#e94560}"
        "table{border-collapse:collapse;width:100%}"
        "th,td{border:1px solid #333;padding:6px 10px;text-align:left}"
        "th{background:#16213e}"
        "tr:nth-child(even){background:#0f3460}"
        "tr:hover{background:#1a1a4e}"
        "</style></head><body>"
        "<h1>TaskBoard</h1>"
        f'<p style="color:#888">Auto-refreshes every 5s &middot; {len(tasks)} task(s)</p>'
        "<table>"
        "<tr><th>ID</th><th>Label</th><th>Command</th><th>Status</th>"
        "<th>Start</th><th>End</th><th>Duration(s)</th><th>Exit</th><th>Last Output</th></tr>\n"
        f"{rows}</table></body></html>"
    )


def cmd_serve(args: argparse.Namespace) -> int:
    host = args.host
    port = args.port

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            tasks = _load()
            html = _build_html(tasks)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())

        def log_message(self, fmt: str, *a: Any) -> None:
            pass

    srv = http.server.HTTPServer((host, port), Handler)
    print(f"TaskBoard serving at http://{host}:{port}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


# ── CLI ─────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="TaskBoard - lightweight task monitor")
    sub = ap.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="Register a new task")
    p_add.add_argument("--id", default=None)
    p_add.add_argument("--label", required=True)
    p_add.add_argument("--cmd", default="")
    p_add.add_argument("--status", default="running")
    p_add.add_argument("--start", default=None)
    p_add.add_argument("--output", default="")

    p_upd = sub.add_parser("update", help="Update an existing task")
    p_upd.add_argument("--id", required=True)
    p_upd.add_argument("--status", default=None)
    p_upd.add_argument("--end", default=None)
    p_upd.add_argument("--duration", type=int, default=None)
    p_upd.add_argument("--exit-code", type=int, default=None)
    p_upd.add_argument("--output", default=None)

    p_ls = sub.add_parser("list", help="List tasks")
    p_ls.add_argument("--status", default=None)
    p_ls.add_argument("--json", dest="json_out", action="store_true")

    p_srv = sub.add_parser("serve", help="Start HTTP dashboard")
    p_srv.add_argument("--host", default="0.0.0.0")
    p_srv.add_argument("--port", type=int, default=9876)

    args = ap.parse_args()
    if not args.command:
        ap.print_help()
        return 1

    return {"add": cmd_add, "update": cmd_update, "list": cmd_list, "serve": cmd_serve}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
