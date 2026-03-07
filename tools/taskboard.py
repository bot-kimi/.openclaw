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


# ── HTML dashboard ──────────────────────────────────────────────────

_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>TaskBoard</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{height:100%}
body{
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
  background:#0d1117;color:#c9d1d9;line-height:1.5;min-height:100%;
}
.wrap{max-width:1440px;margin:0 auto;padding:20px 24px}

/* ── header ── */
.hdr{display:flex;align-items:center;gap:12px;margin-bottom:20px}
.hdr h1{font-size:18px;font-weight:600;color:#f0f6fc;letter-spacing:-.01em}
.dot{width:7px;height:7px;border-radius:50%;background:#3fb950;
  box-shadow:0 0 6px rgba(63,185,80,.45);animation:pulse 2s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.hdr .meta{font-size:12px;color:#484f58;margin-left:auto;white-space:nowrap}

/* ── filters ── */
.filters{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap}
.fbtn{
  padding:3px 14px;border:1px solid #30363d;border-radius:16px;
  background:transparent;color:#8b949e;font-size:12px;font-family:inherit;
  cursor:pointer;transition:all .15s ease;user-select:none;outline:none;
}
.fbtn:hover{border-color:#58a6ff;color:#58a6ff}
.fbtn.on{background:#1f6feb;border-color:#1f6feb;color:#fff}
.fbtn .n{
  display:inline-block;min-width:16px;text-align:center;
  margin-left:4px;padding:0 5px;border-radius:8px;
  font-size:10px;font-weight:600;background:rgba(255,255,255,.08);
}
.fbtn.on .n{background:rgba(255,255,255,.2)}

/* ── table ── */
table{width:100%;border-collapse:collapse;font-size:13px}
thead th{
  text-align:left;padding:6px 12px;font-size:11px;font-weight:600;
  text-transform:uppercase;letter-spacing:.05em;color:#484f58;
  border-bottom:1px solid #21262d;position:sticky;top:0;background:#0d1117;
  z-index:2;
}
tbody tr{border-bottom:1px solid rgba(33,38,45,.6);cursor:pointer;transition:background .12s}
tbody tr:hover{background:#161b22}
td{padding:7px 12px;white-space:nowrap;vertical-align:middle}

.c-id{
  font-family:'SF Mono',SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace;
  font-size:12px;color:#58a6ff;
}
.c-label{color:#c9d1d9;font-weight:500;max-width:280px;overflow:hidden;text-overflow:ellipsis}
.c-cmd{
  color:#484f58;font-size:12px;max-width:200px;overflow:hidden;text-overflow:ellipsis;
  font-family:'SF Mono',SFMono-Regular,Consolas,monospace;
}
.c-dur,.c-exit{text-align:right;font-family:monospace;font-size:12px;color:#8b949e}
.c-time{font-size:12px;color:#8b949e}
.c-time .rel{color:#c9d1d9;font-weight:500}
.c-time .abs{color:#484f58;font-size:11px;margin-left:6px}

/* ── chips ── */
.chip{
  display:inline-block;padding:1px 10px;border-radius:10px;
  font-size:11px;font-weight:600;letter-spacing:.02em;white-space:nowrap;
}
.chip-running{background:rgba(56,139,253,.15);color:#58a6ff}
.chip-completed{background:rgba(63,185,80,.15);color:#3fb950}
.chip-failed{background:rgba(248,81,73,.15);color:#f85149}

/* ── empty state ── */
.empty{text-align:center;padding:48px 0;color:#484f58;font-size:14px}

/* ── modal overlay ── */
.overlay{
  display:none;position:fixed;inset:0;
  background:rgba(1,4,9,.7);backdrop-filter:blur(4px);
  z-index:100;justify-content:center;align-items:center;
}
.overlay.open{display:flex}

/* ── modal ── */
.modal{
  background:#161b22;border:1px solid #30363d;border-radius:10px;
  width:92%;max-width:680px;max-height:82vh;overflow-y:auto;
  padding:20px 24px;box-shadow:0 16px 48px rgba(0,0,0,.4);
}
.m-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.m-head h2{font-size:15px;color:#f0f6fc;font-weight:600}
.m-close{
  background:none;border:none;color:#484f58;font-size:22px;
  cursor:pointer;padding:2px 8px;line-height:1;border-radius:4px;
}
.m-close:hover{color:#f0f6fc;background:#21262d}
.m-grid{display:grid;grid-template-columns:90px 1fr;gap:6px 14px;font-size:13px}
.m-lbl{color:#484f58;font-weight:600;text-align:right}
.m-val{color:#c9d1d9;word-break:break-word}
.m-val.mono{font-family:'SF Mono',SFMono-Regular,Consolas,monospace;font-size:12px}
.m-section{
  margin-top:16px;font-size:11px;font-weight:600;color:#484f58;
  text-transform:uppercase;letter-spacing:.05em;
}
.m-out{
  margin-top:6px;background:#0d1117;border:1px solid #21262d;border-radius:6px;
  padding:10px 12px;font-family:'SF Mono',SFMono-Regular,Consolas,monospace;
  font-size:12px;white-space:pre-wrap;word-break:break-all;
  max-height:260px;overflow-y:auto;color:#c9d1d9;line-height:1.5;
}

/* ── scrollbar ── */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:#30363d;border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#484f58}
</style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <div class="dot"></div>
    <h1>TaskBoard</h1>
    <span class="meta" id="meta"></span>
  </div>
  <div class="filters" id="filters"></div>
  <table>
    <thead><tr>
      <th>ID</th><th>Label</th><th>Status</th>
      <th>Started</th><th>Duration</th><th>Exit</th><th>Command</th>
    </tr></thead>
    <tbody id="tb"></tbody>
  </table>
  <div class="empty" id="empty" style="display:none">No tasks match this filter.</div>
</div>

<div class="overlay" id="ov">
  <div class="modal" id="mdl">
    <div class="m-head">
      <h2 id="m-title"></h2>
      <button class="m-close" id="m-x">&times;</button>
    </div>
    <div id="m-body"></div>
  </div>
</div>

<script>
(function(){
var T = __TASKS_JSON__;
var filter = 'all';

function esc(s) {
  if (s == null) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;')
                   .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function relTime(iso) {
  if (!iso) return '\u2014';
  var s = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 0) return 'just now';
  if (s < 60) return s + 's ago';
  var m = Math.floor(s / 60);
  if (m < 60) return m + 'm ago';
  var h = Math.floor(m / 60);
  if (h < 24) return h + 'h ago';
  return Math.floor(h / 24) + 'd ago';
}

function localT(iso) {
  if (!iso) return '';
  var d = new Date(iso);
  return d.toLocaleDateString(undefined, {month:'short', day:'numeric'})
    + ' ' + d.toLocaleTimeString(undefined, {hour:'2-digit', minute:'2-digit'});
}

function fullLocal(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString(undefined, {
    year:'numeric', month:'short', day:'numeric',
    hour:'2-digit', minute:'2-digit', second:'2-digit'
  });
}

function fmtDur(v) {
  if (v == null) return '\u2014';
  v = Math.round(v);
  if (v < 1) return '<1s';
  if (v < 60) return v + 's';
  var m = Math.floor(v / 60), s = v % 60;
  if (m < 60) return m + 'm' + (s ? ' ' + s + 's' : '');
  var h = Math.floor(m / 60); m = m % 60;
  return h + 'h' + (m ? ' ' + m + 'm' : '');
}

function chipHtml(st) {
  return '<span class="chip chip-' + esc(st || 'running') + '">' + esc(st) + '</span>';
}

function counts() {
  var c = {all: T.length, running: 0, completed: 0, failed: 0};
  T.forEach(function(t) { if (c[t.status] !== undefined) c[t.status]++; });
  return c;
}

function renderFilters() {
  var c = counts(), el = document.getElementById('filters');
  el.innerHTML = '';
  ['all','running','completed','failed'].forEach(function(f) {
    var b = document.createElement('button');
    b.className = 'fbtn' + (filter === f ? ' on' : '');
    b.innerHTML = f.charAt(0).toUpperCase() + f.slice(1)
      + '<span class="n">' + c[f] + '</span>';
    b.onclick = function() { filter = f; render(); };
    el.appendChild(b);
  });
}

function render() {
  renderFilters();
  var list = filter === 'all' ? T.slice() : T.filter(function(t) { return t.status === filter; });
  list.sort(function(a, b) { return (b.start || '').localeCompare(a.start || ''); });
  document.getElementById('meta').textContent =
    list.length + ' of ' + T.length + ' tasks \u00b7 live';
  var tb = document.getElementById('tb'), emp = document.getElementById('empty');
  tb.innerHTML = '';
  if (!list.length) { emp.style.display = 'block'; return; }
  emp.style.display = 'none';
  list.forEach(function(t) {
    var tr = document.createElement('tr');
    tr.innerHTML =
      '<td class="c-id">' + esc(t.id) + '</td>' +
      '<td class="c-label">' + esc(t.label) + '</td>' +
      '<td>' + chipHtml(t.status) + '</td>' +
      '<td class="c-time" title="' + esc(t.start) + '">' +
        '<span class="rel">' + relTime(t.start) + '</span>' +
        '<span class="abs">' + localT(t.start) + '</span></td>' +
      '<td class="c-dur">' + fmtDur(t.duration) + '</td>' +
      '<td class="c-exit">' + (t.exitCode != null ? t.exitCode : '\u2014') + '</td>' +
      '<td class="c-cmd" title="' + esc(t.cmd) + '">' + esc(t.cmd || '\u2014') + '</td>';
    tr.onclick = function() { openModal(t); };
    tb.appendChild(tr);
  });
}

function openModal(t) {
  document.getElementById('m-title').textContent = t.label + ' \u2014 ' + t.id;
  var rows = [
    ['Status',   chipHtml(t.status)],
    ['ID',       '<span class="mono">' + esc(t.id) + '</span>'],
    ['Started',  fullLocal(t.start) +
      ' <span style="color:#484f58">(' + esc(t.start) + ')</span>'],
    ['Ended',    t.end
      ? fullLocal(t.end) + ' <span style="color:#484f58">(' + esc(t.end) + ')</span>'
      : '\u2014'],
    ['Duration', fmtDur(t.duration) +
      (t.duration != null ? ' <span style="color:#484f58">(' + t.duration + 's)</span>' : '')],
    ['Exit',     t.exitCode != null ? String(t.exitCode) : '\u2014'],
    ['Command',  '<span class="mono">' + esc(t.cmd || '\u2014') + '</span>'],
  ];
  var h = '<div class="m-grid">';
  rows.forEach(function(r) {
    h += '<div class="m-lbl">' + r[0] + '</div><div class="m-val">' + r[1] + '</div>';
  });
  h += '</div>';
  if (t.lastOutput) {
    h += '<div class="m-section">Output</div><div class="m-out">' + esc(t.lastOutput) + '</div>';
  }
  document.getElementById('m-body').innerHTML = h;
  document.getElementById('ov').classList.add('open');
}

function closeModal() { document.getElementById('ov').classList.remove('open'); }
document.getElementById('m-x').onclick = closeModal;
document.getElementById('ov').onclick = function(e) { if (e.target === this) closeModal(); };
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeModal(); });

setInterval(function() {
  fetch('/api/tasks').then(function(r) { return r.json(); })
    .then(function(d) { T = d; render(); }).catch(function() {});
}, 5000);

render();
})();
</script>
</body>
</html>"""


def _build_html(tasks: list[dict[str, Any]]) -> str:
    safe = json.dumps(tasks, ensure_ascii=False).replace("</", "<\\/")
    return _HTML_TEMPLATE.replace("__TASKS_JSON__", safe)


def cmd_serve(args: argparse.Namespace) -> int:
    host = args.host
    port = args.port

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            tasks = _load()
            if self.path == "/api/tasks":
                body = json.dumps(tasks, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(body)
            else:
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
