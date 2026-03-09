#!/usr/bin/env python3
"""
exp_sheet.py – Experiment tracking to Google Sheets via gog CLI.

Each project maps to a tab (sheet) name.  Commands:
  start      – append a new row with status=running
  status     – update status of the latest matching run_id
  done       – shorthand for status → done
  fail       – shorthand for status → failed
  reconcile  – bulk-sync statuses from the local taskboard JSON
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
TASKBOARD_JSON = TOOLS_DIR.parent / ".openclaw" / "taskboard" / "tasks.json"

DEFAULT_SHEET_ID = "1vsic-xRGf6uzWJ58SUGNEE116FnInfAiWKePLj0bA34"
DEFAULT_ACCOUNT = "zhh-spreadsheet@he-vision-group.iam.gserviceaccount.com"

COLUMNS = [
    "timestamp_utc", "run_id", "project", "exp_name", "repo", "model",
    "epochs", "batch_size", "dataset_root", "staging_dir", "log_dir",
    "task_id", "status", "note",
]
NUM_COLS = len(COLUMNS)
COL_LETTERS = [chr(ord("A") + i) for i in range(NUM_COLS)]
LAST_COL = COL_LETTERS[-1]

RUN_ID_IDX = COLUMNS.index("run_id")
TASK_ID_IDX = COLUMNS.index("task_id")
STATUS_IDX = COLUMNS.index("status")
NOTE_IDX = COLUMNS.index("note")

STATUS_LETTER = COL_LETTERS[STATUS_IDX]
NOTE_LETTER = COL_LETTERS[NOTE_IDX]

# ── gog helpers ──────────────────────────────────────────────────────

def _check_gog() -> None:
    if shutil.which("gog") is None:
        print("ERROR: 'gog' CLI not found in PATH. Install it first.", file=sys.stderr)
        sys.exit(1)


def _gog(args: list[str], account: str) -> subprocess.CompletedProcess[str]:
    cmd = ["gog", *args, "--account", account, "--no-input"]
    return subprocess.run(cmd, capture_output=True, text=True)


def _sheets_get(sheet_id: str, tab: str, rng: str, account: str) -> list[list[str]]:
    """Read a range and return rows (list of lists)."""
    p = _gog(["sheets", "get", sheet_id, f"{tab}!{rng}", "--json"], account)
    if p.returncode != 0:
        stderr = p.stderr.strip()
        if "Unable to parse range" in stderr or "not found" in stderr.lower():
            return []
        print(f"ERROR: gog sheets get failed (rc={p.returncode}): {stderr}", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(p.stdout)
    except json.JSONDecodeError:
        print(f"ERROR: cannot parse gog output: {p.stdout[:300]}", file=sys.stderr)
        sys.exit(1)
    if isinstance(data, dict):
        return data.get("values", [])
    if isinstance(data, list):
        return data
    return []


def _sheets_append(sheet_id: str, tab: str, rows: list[list[str]],
                   account: str, dry_run: bool) -> None:
    rng = f"{tab}!A:{LAST_COL}"
    payload = json.dumps(rows)
    if dry_run:
        print(f"[dry-run] append {rng}: {payload}")
        return
    p = _gog(["sheets", "append", sheet_id, rng,
              "--values-json", payload,
              "--insert", "INSERT_ROWS", "--json"], account)
    if p.returncode != 0:
        print(f"ERROR: gog sheets append failed (rc={p.returncode}): {p.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def _sheets_update(sheet_id: str, tab: str, rng: str,
                   values: list[list[str]], account: str, dry_run: bool) -> None:
    full = f"{tab}!{rng}"
    payload = json.dumps(values)
    if dry_run:
        print(f"[dry-run] update {full}: {payload}")
        return
    p = _gog(["sheets", "update", sheet_id, full,
              "--values-json", payload,
              "--input", "USER_ENTERED", "--json"], account)
    if p.returncode != 0:
        print(f"ERROR: gog sheets update failed (rc={p.returncode}): {p.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

# ── sheet-level helpers ──────────────────────────────────────────────

def _ensure_header(sheet_id: str, tab: str, account: str, dry_run: bool) -> None:
    """Append header row if the tab is empty."""
    existing = _sheets_get(sheet_id, tab, "A1:A1", account)
    if existing:
        return
    _sheets_append(sheet_id, tab, [COLUMNS], account, dry_run)
    if not dry_run:
        print(f"Created header row in tab '{tab}'")


def _find_latest_row(sheet_id: str, tab: str, col_idx: int,
                     value: str, account: str) -> int | None:
    """Return 1-based row number of the *last* row where col_idx == value."""
    letter = COL_LETTERS[col_idx]
    rows = _sheets_get(sheet_id, tab, f"{letter}:{letter}", account)
    match: int | None = None
    for i, row in enumerate(rows):
        if row and row[0] == value:
            match = i + 1
    return match

# ── commands ─────────────────────────────────────────────────────────

def cmd_start(args: argparse.Namespace) -> None:
    _check_gog()
    _ensure_header(args.sheet_id, args.project, args.account, args.dry_run)

    run_id = args.run_id or uuid.uuid4().hex[:10]
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    row = [
        ts,
        run_id,
        args.project,
        args.exp_name or "",
        args.repo or "",
        args.model or "",
        str(args.epochs) if args.epochs is not None else "",
        str(args.batch_size) if args.batch_size is not None else "",
        args.dataset_root or "",
        args.staging_dir or "",
        args.log_dir or "",
        args.task_id or "",
        "running",
        args.note or "",
    ]

    _sheets_append(args.sheet_id, args.project, [row], args.account, args.dry_run)
    print(f"run_id={run_id}")


def _update_status(args: argparse.Namespace, new_status: str) -> None:
    _check_gog()
    row_num = _find_latest_row(args.sheet_id, args.project, RUN_ID_IDX,
                               args.run_id, args.account)
    if row_num is None:
        print(f"ERROR: no row with run_id={args.run_id} in tab '{args.project}'",
              file=sys.stderr)
        sys.exit(1)

    note = args.note or ""
    rng = f"{STATUS_LETTER}{row_num}:{NOTE_LETTER}{row_num}"
    _sheets_update(args.sheet_id, args.project, rng,
                   [[new_status, note]], args.account, args.dry_run)
    print(f"row {row_num}: status → {new_status}" +
          (f"  note={note}" if note else "") +
          f"  (run_id={args.run_id})")


def cmd_status(args: argparse.Namespace) -> None:
    _update_status(args, args.new_status)


def cmd_done(args: argparse.Namespace) -> None:
    _update_status(args, "done")


def cmd_fail(args: argparse.Namespace) -> None:
    _update_status(args, "failed")


_TB_STATUS_MAP = {"completed": "done", "failed": "failed", "running": "running"}


def cmd_reconcile(args: argparse.Namespace) -> None:
    _check_gog()
    tb_path = Path(args.taskboard_json)
    if not tb_path.exists():
        print(f"ERROR: taskboard JSON not found: {tb_path}", file=sys.stderr)
        sys.exit(1)

    tasks = json.loads(tb_path.read_text(encoding="utf-8"))
    task_map = {t["id"]: t for t in tasks if "id" in t}
    if not task_map:
        print("No tasks in taskboard; nothing to reconcile.")
        return

    tid_letter = COL_LETTERS[TASK_ID_IDX]
    rows = _sheets_get(args.sheet_id, args.project,
                       f"{tid_letter}:{NOTE_LETTER}", args.account)

    updated = 0
    for i, row in enumerate(rows):
        if i == 0 and row and row[0] == COLUMNS[TASK_ID_IDX]:
            continue
        if not row or not row[0]:
            continue
        tid = row[0]
        if tid not in task_map:
            continue

        sheet_status = row[1] if len(row) > 1 else ""
        tb_status = _TB_STATUS_MAP.get(task_map[tid].get("status", ""), "")
        if not tb_status or tb_status == sheet_status:
            continue

        row_num = i + 1
        rng = f"{STATUS_LETTER}{row_num}"
        _sheets_update(args.sheet_id, args.project, rng,
                       [[tb_status]], args.account, args.dry_run)
        updated += 1
        print(f"  row {row_num}: task_id={tid}  {sheet_status} → {tb_status}")

    print(f"Reconciled {updated} row(s) in tab '{args.project}'")

# ── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        prog="exp_sheet",
        description="Experiment tracking to Google Sheets via gog CLI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Log a new experiment
  python3 tools/exp_sheet.py start --project resnet \\
      --exp-name resnet50-bs64 --model resnet50 --epochs 90

  # Mark it done
  python3 tools/exp_sheet.py done --project resnet --run-id abc123

  # Sync from taskboard
  python3 tools/exp_sheet.py reconcile --project resnet
""",
    )
    ap.add_argument("--sheet-id", default=DEFAULT_SHEET_ID,
                    help="Google Sheet ID (default: experiments sheet)")
    ap.add_argument("--account", default=DEFAULT_ACCOUNT,
                    help="gog service account")
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would be written without touching the sheet")

    sub = ap.add_subparsers(dest="command", required=True)

    # start
    p_s = sub.add_parser("start", help="Append a new row (status=running)")
    p_s.add_argument("--project", required=True, help="Project / tab name")
    p_s.add_argument("--run-id", default=None, help="Custom run ID (auto if omitted)")
    p_s.add_argument("--exp-name", default=None)
    p_s.add_argument("--repo", default=None)
    p_s.add_argument("--model", default=None)
    p_s.add_argument("--epochs", type=int, default=None)
    p_s.add_argument("--batch-size", type=int, default=None)
    p_s.add_argument("--dataset-root", default=None)
    p_s.add_argument("--staging-dir", required=True,
                     help="Required: immutable code snapshot dir for this run")
    p_s.add_argument("--log-dir", required=True,
                     help="Required: dedicated log/output dir for this run")
    p_s.add_argument("--task-id", default=None, help="Taskboard task ID for reconcile")
    p_s.add_argument("--note", default=None)

    # status
    p_st = sub.add_parser("status", help="Set arbitrary status on a run")
    p_st.add_argument("--project", required=True)
    p_st.add_argument("--run-id", required=True)
    p_st.add_argument("--new-status", required=True)
    p_st.add_argument("--note", default=None)

    # done
    p_d = sub.add_parser("done", help="Mark run done")
    p_d.add_argument("--project", required=True)
    p_d.add_argument("--run-id", required=True)
    p_d.add_argument("--note", default=None)

    # fail
    p_f = sub.add_parser("fail", help="Mark run failed")
    p_f.add_argument("--project", required=True)
    p_f.add_argument("--run-id", required=True)
    p_f.add_argument("--note", default=None)

    # reconcile
    p_r = sub.add_parser("reconcile", help="Sync statuses from taskboard JSON")
    p_r.add_argument("--project", required=True)
    p_r.add_argument("--taskboard-json", default=str(TASKBOARD_JSON),
                     help="Path to tasks.json")

    args = ap.parse_args()
    dispatch = {
        "start": cmd_start, "status": cmd_status,
        "done": cmd_done, "fail": cmd_fail, "reconcile": cmd_reconcile,
    }
    try:
        dispatch[args.command](args)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
