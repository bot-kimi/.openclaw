#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: tools/runlong.sh '<command>' [label] [tags]"
  exit 1
fi

CMD="$1"
LABEL="${2:-long-task}"
TAGS="${3:-}"
CWD="$(pwd)"

ARGS=(
  --cmd "$CMD"
  --label "$LABEL"
  --cwd "$CWD"
  --emit-start
)

if [[ -n "$TAGS" ]]; then
  ARGS+=(--tags "$TAGS")
fi

python3 tools/wakebridge.py "${ARGS[@]}"
