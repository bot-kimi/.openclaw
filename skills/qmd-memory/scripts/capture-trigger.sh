#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"trigger text\"" >&2
  exit 1
fi

RAW="$1"
TEXT="$RAW"
TEXT="${TEXT#记住这个：}"
TEXT="${TEXT#记住这个:}"
TEXT="${TEXT#记住这个 }"
TEXT="${TEXT#记住这个}"
TEXT="$(echo "$TEXT" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

if [ -z "$TEXT" ]; then
  echo "EMPTY_CONTENT"
  exit 2
fi

"$(dirname "$0")/capture-note.sh" "$TEXT" "user-memory,quick-capture" "P1"
