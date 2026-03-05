#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   run-coding-task.sh quick "task..."
#   run-coding-task.sh deep "task..."
#   run-coding-task.sh quick "task..." --continue
#   run-coding-task.sh deep "task..." --session <id>

MODE="${1:-}"
TASK="${2:-}"
shift 2 || true

if [[ -z "$MODE" || -z "$TASK" ]]; then
  echo "Usage: $0 <quick|deep> \"task\" [extra args]" >&2
  exit 1
fi

case "$MODE" in
  quick)
    exec cursor-agent --trust -p "$TASK" "$@"
    ;;
  deep)
    exec opencode run "$TASK" "$@"
    ;;
  *)
    echo "Invalid mode: $MODE (use quick|deep)" >&2
    exit 2
    ;;
esac
