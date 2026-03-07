#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: tools/runlong.sh '<command>' [label]"
  exit 1
fi

CMD="$1"
LABEL="${2:-long-task}"
CWD="$(pwd)"

python3 tools/wakebridge.py \
  --cmd "$CMD" \
  --label "$LABEL" \
  --cwd "$CWD" \
  --emit-start
