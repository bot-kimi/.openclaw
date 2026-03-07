# TaskBoard

Lightweight task monitoring board for background jobs. Stdlib only, no external dependencies.

## Data

Tasks stored at `.openclaw/taskboard/tasks.json` (created automatically).

Each task has: `id`, `label`, `cmd`, `status`, `start`, `end`, `duration`, `exitCode`, `lastOutput`.

Status values: `running`, `completed`, `failed`.

## Commands

### Add a task

```bash
python3 tools/taskboard.py add --label 'my-job' --cmd 'sleep 10'
# prints the generated task ID

# with explicit ID:
python3 tools/taskboard.py add --id abc123 --label 'my-job' --cmd 'sleep 10'
```

### Update a task

```bash
python3 tools/taskboard.py update \
  --id abc123 \
  --status completed \
  --end 2026-03-07T12:00:00+00:00 \
  --duration 10 \
  --exit-code 0 \
  --output 'final output lines here'
```

### List tasks

```bash
python3 tools/taskboard.py list              # table format
python3 tools/taskboard.py list --json       # JSON output
python3 tools/taskboard.py list --status running
```

### Serve dashboard

```bash
python3 tools/taskboard.py serve                 # http://0.0.0.0:9876
python3 tools/taskboard.py serve --port 8080     # custom port
```

The dashboard auto-refreshes every 5 seconds and shows all tasks in a color-coded table.

## Integration

WakeBridge automatically registers tasks on the board (see `WAKEBRIDGE.md`). Use `--no-taskboard` on wakebridge to skip registration.
