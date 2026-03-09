# exp_sheet.py – Experiment Tracker (Google Sheets)

CLI tool that logs ML experiments to a shared Google Sheet via `gog`.
Each **project** maps to a **tab** (sheet name).

## Setup

Requires `gog` with a service account that has editor access to the sheet.

```bash
gog auth add zhh-spreadsheet@he-vision-group.iam.gserviceaccount.com \
  --services sheets --service-account google_secret.json
```

Default sheet: `1vsic-xRGf6uzWJ58SUGNEE116FnInfAiWKePLj0bA34`

Create tabs for each project in the sheet (e.g. `resnet`, `vit`).
The tool auto-inserts a header row if the tab is empty.

## Columns

| Col | Field | Notes |
|-----|-------|-------|
| A | timestamp_utc | Auto-filled on `start` |
| B | run_id | Auto-generated or `--run-id` |
| C | project | Same as tab name |
| D | exp_name | Free text |
| E | repo | Git repo or path |
| F | model | Architecture name |
| G | epochs | Integer |
| H | batch_size | Integer |
| I | dataset_root | Path |
| J | staging_dir | Path |
| K | log_dir | Path |
| L | task_id | Links to taskboard for `reconcile` |
| M | status | running / done / failed |
| N | note | Free text |

## Commands

### start – Log a new experiment

`--staging-dir` 和 `--log-dir` 是**必填**（enforce `one experiment, one code, one log`）。

```bash
python3 tools/exp_sheet.py start --project resnet \
  --exp-name resnet50-bs64 --model resnet50 --epochs 90 \
  --batch-size 64 --dataset-root /data/imagenet \
  --staging-dir /staging/resnet/20260309_123000_abcd123 \
  --log-dir /logs/resnet50-run1 --note "baseline"
```

Prints the `run_id` for use in later commands.

### done / fail – Mark experiment finished

```bash
python3 tools/exp_sheet.py done --project resnet --run-id abc123 \
  --note "93.2% top-1 acc"

python3 tools/exp_sheet.py fail --project resnet --run-id abc123 \
  --note "OOM at epoch 42"
```

### status – Set arbitrary status

```bash
python3 tools/exp_sheet.py status --project resnet --run-id abc123 \
  --new-status paused --note "waiting for TPU"
```

### reconcile – Sync from taskboard

Reads `.openclaw/taskboard/tasks.json` and updates the status column
for any rows whose `task_id` matches a taskboard entry.

```bash
python3 tools/exp_sheet.py reconcile --project resnet
```

### dry-run

All commands accept `--dry-run` to preview without writing:

```bash
python3 tools/exp_sheet.py --dry-run start --project resnet --exp-name test
```

## Integration with wakebridge

Use `--task-id` from wakebridge to link experiments for auto-reconcile.

### Typical workflow

```bash
# 1. Start the experiment and capture the wakebridge task ID
TASK_ID=$(python3 tools/wakebridge.py \
  --cmd "python3 train.py --model resnet50 --epochs 90" \
  --label "resnet50-bs64" \
  --tags "training,resnet" \
  --timeout-sec 86400 \
  --alarm-after-sec 7200 2>&1 | grep -oP 'task_id=\K\w+' || echo "")

# 2. Log to experiment sheet (wakebridge prints task_id to stderr)
python3 tools/exp_sheet.py start --project resnet \
  --exp-name resnet50-bs64 --model resnet50 --epochs 90 \
  --batch-size 64 --task-id "$TASK_ID" \
  --log-dir /logs/resnet50-run1

# 3. When wakebridge finishes, reconcile or manually mark done
python3 tools/exp_sheet.py reconcile --project resnet
```

### One-liner with wakebridge

```bash
RUN_ID=$(python3 tools/exp_sheet.py start --project resnet \
  --exp-name resnet50-lr01 --model resnet50 --epochs 90 \
  | grep -oP 'run_id=\K\S+')

python3 tools/wakebridge.py \
  --cmd "python3 train.py --epochs 90" \
  --label "resnet50-lr01" \
  --tags "training" \
  --timeout-sec 86400

python3 tools/exp_sheet.py done --project resnet --run-id "$RUN_ID" \
  --note "finished normally"
```

### Wrapper script pattern

```bash
#!/usr/bin/env bash
set -euo pipefail
PROJECT=resnet
EXP_NAME="$1"; shift

RUN_ID=$(python3 tools/exp_sheet.py start \
  --project "$PROJECT" --exp-name "$EXP_NAME" \
  --model resnet50 "$@" | grep -oP 'run_id=\K\S+')

cleanup() {
  local rc=$?
  if [ $rc -eq 0 ]; then
    python3 tools/exp_sheet.py done --project "$PROJECT" --run-id "$RUN_ID"
  else
    python3 tools/exp_sheet.py fail --project "$PROJECT" --run-id "$RUN_ID" \
      --note "exit code $rc"
  fi
}
trap cleanup EXIT

python3 tools/wakebridge.py \
  --cmd "python3 train.py --exp $EXP_NAME" \
  --label "$EXP_NAME" --tags training
```

## Overrides

| Flag | Default | Description |
|------|---------|-------------|
| `--sheet-id` | `1vsic-xRGf6uzWJ58SUGNEE116FnInfAiWKePLj0bA34` | Target spreadsheet |
| `--account` | `zhh-spreadsheet@he-vision-group.iam.gserviceaccount.com` | gog account |
| `--taskboard-json` | `.openclaw/taskboard/tasks.json` | For reconcile |
