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
import os
import signal
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

WORKSPACE = Path(__file__).resolve().parent.parent
DATA_DIR = WORKSPACE / ".openclaw" / "taskboard"
TASKS_FILE = DATA_DIR / "tasks.json"
LOGS_DIR = DATA_DIR / "logs"


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _load() -> list[dict[str, Any]]:
    if not TASKS_FILE.exists():
        return []
    tasks = json.loads(TASKS_FILE.read_text())
    return [_normalize_task(t) for t in tasks]


def _save(tasks: list[dict[str, Any]]) -> None:
    _ensure_dir()
    TASKS_FILE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n")


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _parse_tags(raw: str | None) -> list[str]:
    if raw is None:
        return []
    out: list[str] = []
    for part in raw.split(","):
        tag = part.strip()
        if tag and tag not in out:
            out.append(tag)
    return out


def _normalize_task(task: dict[str, Any]) -> dict[str, Any]:
    tags = task.get("tags")
    if isinstance(tags, list):
        norm_tags = [str(t).strip() for t in tags if str(t).strip()]
        task["tags"] = list(dict.fromkeys(norm_tags))
    else:
        task["tags"] = []
    return task


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
        "logFile": args.log_file or "",
        "pid": args.pid,
        "pgid": args.pgid,
        "tags": _parse_tags(args.tags),
        "pid": args.pid,
        "pgid": args.pgid,
        "timeoutSec": args.timeout_sec,
        "alarmAfterSec": args.alarm_after_sec,
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
    if getattr(args, "tags", None) is not None:
        t["tags"] = _parse_tags(args.tags)
    if getattr(args, "pid", None) is not None:
        t["pid"] = args.pid
    if getattr(args, "pgid", None) is not None:
        t["pgid"] = args.pgid
    if getattr(args, "timeout_sec", None) is not None:
        t["timeoutSec"] = args.timeout_sec
    if getattr(args, "alarm_after_sec", None) is not None:
        t["alarmAfterSec"] = args.alarm_after_sec
    _save(tasks)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    tasks = _load()
    if args.status:
        tasks = [t for t in tasks if t["status"] == args.status]
    if args.tag:
        tasks = [t for t in tasks if args.tag in (t.get("tags") or [])]
    if args.json_out:
        print(json.dumps(tasks, indent=2, ensure_ascii=False))
    else:
        for t in tasks:
            dur_v = t.get("duration")
            dur_s = f"{dur_v:>6}s" if dur_v is not None else "     —"
            tags_str = ",".join(t.get("tags") or [])
            extra = f"  [{tags_str}]" if tags_str else ""
            print(f'{t["id"]:>10}  {t["status"]:<10}  {dur_s}  {t["label"]}{extra}')
    return 0


def cmd_cleanup(args: argparse.Namespace) -> int:
    tasks = _load()
    now = dt.datetime.now(dt.timezone.utc)
    max_age = args.max_age
    changed = 0
    for t in tasks:
        if t["status"] != "running":
            continue
        start = t.get("start")
        if not start:
            continue
        try:
            started = dt.datetime.fromisoformat(start)
            if started.tzinfo is None:
                started = started.replace(tzinfo=dt.timezone.utc)
            elapsed = (now - started).total_seconds()
        except (ValueError, TypeError):
            continue
        if elapsed > max_age:
            t["status"] = "failed"
            t["end"] = _now_iso()
            t["lastOutput"] = f"stale-cleanup: running {int(elapsed)}s > {max_age}s limit"
            changed += 1
    if changed:
        _save(tasks)
    print(f"cleaned {changed} stale tasks")
    return 0


def cmd_check_mutex(args: argparse.Namespace) -> int:
    required = _parse_tags(args.tags)
    if not required:
        return 0
    tasks = _load()
    for t in tasks:
        if t["status"] != "running":
            continue
        task_tags = t.get("tags") or []
        if all(tag in task_tags for tag in required):
            sys.stderr.write(f"BLOCKED by {t['id']} ({t['label']}): tags {task_tags}\n")
            return 1
    return 0


def cmd_cancel(args: argparse.Namespace) -> int:
    import os
    import signal

    tasks = _load()
    found = [t for t in tasks if t["id"] == args.id]
    if not found:
        sys.stderr.write(f"task {args.id} not found\n")
        return 1

    t = found[0]
    if t.get("status") != "running" and not args.force:
        print(f"task {args.id} is not running (status={t.get('status')})")
        return 0

    killed = False
    pgid = t.get("pgid")
    pid = t.get("pid")
    try:
        if pgid:
            os.killpg(int(pgid), signal.SIGTERM)
            killed = True
        elif pid:
            os.kill(int(pid), signal.SIGTERM)
            killed = True
    except Exception:
        if args.force:
            try:
                if pgid:
                    os.killpg(int(pgid), signal.SIGKILL)
                    killed = True
                elif pid:
                    os.kill(int(pid), signal.SIGKILL)
                    killed = True
            except Exception:
                killed = False

    t["status"] = "cancelled"
    t["end"] = _now_iso()
    t["exitCode"] = -1
    t["lastOutput"] = "cancelled via taskboard" + ("; signal_sent" if killed else "; no_signal")
    _save(tasks)
    print(f"cancelled {args.id} (signal_sent={killed})")
    return 0


def cmd_cancel(args: argparse.Namespace) -> int:
    tasks = _load()
    target = next((t for t in tasks if t.get("id") == args.id), None)
    if not target:
        sys.stderr.write(f"task {args.id} not found\n")
        return 1

    killed = False
    err: str | None = None
    pgid = target.get("pgid")
    pid = target.get("pid")
    try:
        if pgid is not None:
            os.killpg(int(pgid), signal.SIGTERM)
            killed = True
        elif pid is not None:
            os.kill(int(pid), signal.SIGTERM)
            killed = True
    except Exception as exc:
        err = str(exc)

    now = _now_iso()
    target["status"] = "cancelled"
    target["end"] = now
    target["exitCode"] = -1
    msg = "cancel requested"
    if killed:
        msg = "cancel requested; signal sent"
    elif err:
        msg = f"cancel requested; signal error: {err}"
    target["lastOutput"] = msg
    _save(tasks)
    print(msg)
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
.c-tags{max-width:220px;overflow:hidden;text-overflow:ellipsis;color:#8b949e;font-size:12px}
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
.chip-cancelled{background:rgba(210,153,34,.15);color:#d29922}
.tag{
  display:inline-block;padding:0 6px;border-radius:6px;
  font-size:10px;background:rgba(139,148,158,.15);color:#8b949e;
  margin-right:3px;white-space:nowrap;
}
.tag-alarm{background:rgba(210,153,34,.25);color:#d29922}
.tag-sysalarm{background:rgba(136,132,216,.2);color:#8884d8}

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
  <div class="filters"><select id="tagFilter" class="fbtn" style="padding:4px 10px;border-radius:8px"></select></div>
  <table>
    <thead><tr>
      <th>ID</th><th>Label</th><th>Status</th><th>Tags</th>
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
var tagFilter = 'all';

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

function tagHtml(tags) {
  return (tags||[]).map(function(g){
    var c='tag';
    if(g==='alarm')c+=' tag-alarm';
    else if(g==='system-alarm')c+=' tag-sysalarm';
    return '<span class="'+c+'">'+esc(g)+'</span>';
  }).join(' ');
}

function counts() {
  var c = {all: T.length, running: 0, completed: 0, failed: 0, cancelled: 0};
  T.forEach(function(t) { if (c[t.status] !== undefined) c[t.status]++; });
  return c;
}

function renderFilters() {
  var c = counts(), el = document.getElementById('filters');
  el.innerHTML = '';
  ['all','running','completed','failed','cancelled'].forEach(function(f) {
    var b = document.createElement('button');
    b.className = 'fbtn' + (filter === f ? ' on' : '');
    b.innerHTML = f.charAt(0).toUpperCase() + f.slice(1)
      + '<span class="n">' + c[f] + '</span>';
    b.onclick = function() { filter = f; render(); };
    el.appendChild(b);
  });
}

function renderTagFilter() {
  var sel = document.getElementById('tagFilter');
  var tags = {};
  T.forEach(function(t) { (t.tags||[]).forEach(function(g) { tags[g] = (tags[g]||0)+1; }); });
  var keys = Object.keys(tags).sort();
  var html = '<option value="all">All tags</option>';
  keys.forEach(function(k) { html += '<option value="'+esc(k)+'"'+(tagFilter===k?' selected':'')+'>'+esc(k)+' ('+tags[k]+')</option>'; });
  sel.innerHTML = html;
  sel.onchange = function() { tagFilter = sel.value; render(); };
}

function render() {
  renderFilters();
  renderTagFilter();
  var list = filter === 'all' ? T.slice() : T.filter(function(t) { return t.status === filter; });
  if (tagFilter !== 'all') list = list.filter(function(t) { return (t.tags||[]).indexOf(tagFilter) >= 0; });
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
      '<td class="c-tags">' + tagHtml(t.tags) + '</td>' +
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

var modalTimer = null;
var modalTaskId = null;

function refreshModalLog() {
  if (!modalTaskId) return;
  fetch('/api/log?id=' + encodeURIComponent(modalTaskId))
    .then(function(r) { return r.ok ? r.text() : ''; })
    .then(function(txt) {
      var el = document.getElementById('m-live-log');
      if (el) el.textContent = txt || '(no output yet)';
    }).catch(function() {});
}

function openModal(t) {
  document.getElementById('m-title').textContent = t.label + ' \u2014 ' + t.id;
  modalTaskId = t.id;
  var rows = [
    ['Status',   chipHtml(t.status)],
    ['Tags',     tagHtml(t.tags) || '\u2014'],
    ['ID',       '<span class="mono">' + esc(t.id) + '</span>'],
    ['Started',  fullLocal(t.start) +
      ' <span style="color:#484f58">(' + esc(t.start) + ')</span>'],
    ['Ended',    t.end
      ? fullLocal(t.end) + ' <span style="color:#484f58">(' + esc(t.end) + ')</span>'
      : '\u2014'],
    ['Duration', fmtDur(t.duration) +
      (t.duration != null ? ' <span style="color:#484f58">(' + t.duration + 's)</span>' : '')],
    ['Exit',     t.exitCode != null ? String(t.exitCode) : '\u2014'],
    ['Timeout',  t.timeoutSec != null ? (String(t.timeoutSec) + 's') : '\u2014'],
    ['First check alarm', t.alarmAfterSec != null ? (String(t.alarmAfterSec) + 's') : '\u2014'],
    ['Command',  '<span class="mono">' + esc(t.cmd || '\u2014') + '</span>'],
  ];
  var h = '<div class="m-grid">';
  rows.forEach(function(r) {
    h += '<div class="m-lbl">' + r[0] + '</div><div class="m-val">' + r[1] + '</div>';
  });
  h += '</div>';
  h += '<div class="m-section">Live Output</div><div id="m-live-log" class="m-out">' + esc(t.lastOutput || '(loading...)') + '</div>';
  document.getElementById('m-body').innerHTML = h;
  document.getElementById('ov').classList.add('open');
  refreshModalLog();
  if (modalTimer) clearInterval(modalTimer);
  modalTimer = setInterval(refreshModalLog, 2000);
}

function closeModal() {
  document.getElementById('ov').classList.remove('open');
  if (modalTimer) { clearInterval(modalTimer); modalTimer = null; }
  modalTaskId = null;
}
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
            parsed = urlparse(self.path)
            if parsed.path == "/api/tasks":
                q = parse_qs(parsed.query)
                tag = (q.get("tag") or [""])[0].strip()
                if tag:
                    tasks = [t for t in tasks if tag in (t.get("tags") or [])]
                body = json.dumps(tasks, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(body)
            elif parsed.path == "/api/cancel":
                q = parse_qs(parsed.query)
                task_id = (q.get("id") or [""])[0]
                if not task_id:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"missing id")
                    return
                ns = argparse.Namespace(id=task_id, force=True)
                rc = cmd_cancel(ns)
                body = json.dumps({"ok": rc == 0, "id": task_id}, ensure_ascii=False).encode()
                self.send_response(200 if rc == 0 else 500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(body)
            elif parsed.path == "/api/log":
                q = parse_qs(parsed.query)
                task_id = (q.get("id") or [""])[0]
                if not task_id:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"missing id")
                    return
                log_path = LOGS_DIR / f"{task_id}.log"
                if not log_path.exists():
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"log not found")
                    return
                body = log_path.read_text(encoding="utf-8", errors="replace")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(body.encode("utf-8"))
            else:
                html = _build_html(tasks)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode())

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/api/cancel":
                self.send_response(404)
                self.end_headers()
                return
            q = parse_qs(parsed.query)
            task_id = (q.get("id") or [""])[0].strip()
            if not task_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"missing id")
                return
            rc = cmd_cancel(argparse.Namespace(id=task_id))
            self.send_response(200 if rc == 0 else 500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": rc == 0, "id": task_id}).encode("utf-8"))

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
    p_add.add_argument("--log-file", default="")
    p_add.add_argument("--tags", default="")
    p_add.add_argument("--pid", type=int, default=None)
    p_add.add_argument("--pgid", type=int, default=None)
    p_add.add_argument("--timeout-sec", type=int, default=None)
    p_add.add_argument("--alarm-after-sec", type=int, default=None)

    p_upd = sub.add_parser("update", help="Update an existing task")
    p_upd.add_argument("--id", required=True)
    p_upd.add_argument("--status", default=None)
    p_upd.add_argument("--end", default=None)
    p_upd.add_argument("--duration", type=int, default=None)
    p_upd.add_argument("--exit-code", type=int, default=None)
    p_upd.add_argument("--output", default=None)
    p_upd.add_argument("--tags", default=None)
    p_upd.add_argument("--pid", type=int, default=None)
    p_upd.add_argument("--pgid", type=int, default=None)
    p_upd.add_argument("--timeout-sec", type=int, default=None)
    p_upd.add_argument("--alarm-after-sec", type=int, default=None)

    p_ls = sub.add_parser("list", help="List tasks")
    p_ls.add_argument("--status", default=None)
    p_ls.add_argument("--tag", default=None)
    p_ls.add_argument("--json", dest="json_out", action="store_true")

    p_srv = sub.add_parser("serve", help="Start HTTP dashboard")
    p_srv.add_argument("--host", default="0.0.0.0")
    p_srv.add_argument("--port", type=int, default=9876)

    p_clean = sub.add_parser("cleanup", help="Mark stale running tasks as failed")
    p_clean.add_argument("--max-age", type=int, default=3600,
                         help="Seconds before a running task is considered stale")

    p_mut = sub.add_parser("check-mutex", help="Exit non-zero if a running task matches all given tags")
    p_mut.add_argument("--tags", required=True, help="Comma-separated tags to check")

    p_cancel = sub.add_parser("cancel", help="Cancel a running task by id")
    p_cancel.add_argument("--id", required=True)
    p_cancel.add_argument("--force", action="store_true", help="Use SIGKILL fallback if needed")

    args = ap.parse_args()
    if not args.command:
        ap.print_help()
        return 1

    cmds = {"add": cmd_add, "update": cmd_update, "list": cmd_list,
            "serve": cmd_serve, "cleanup": cmd_cleanup,
            "check-mutex": cmd_check_mutex, "cancel": cmd_cancel}
    return cmds[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
