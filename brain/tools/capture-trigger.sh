#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   brain/tools/capture-trigger.sh "记住这个：明天交水电费"
#   brain/tools/capture-trigger.sh "记住这个 明天交水电费"

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"trigger text\"" >&2
  exit 1
fi

RAW="$1"
TEXT="$RAW"

# Strip common trigger prefixes in Chinese
TEXT="${TEXT#记住这个：}"
TEXT="${TEXT#记住这个:}"
TEXT="${TEXT#记住这个 }"
TEXT="${TEXT#记住这个}"

# trim leading/trailing spaces
TEXT="$(echo "$TEXT" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

if [ -z "$TEXT" ]; then
  echo "EMPTY_CONTENT"
  exit 2
fi

/home/jasm/.openclaw/workspace/brain/tools/capture-note.sh "$TEXT" "user-memory,quick-capture" "P1"
