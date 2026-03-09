#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: tools/notify_telegram.sh '<message>' [target]" >&2
  exit 1
fi

MSG="$1"
TARGET="${2:-telegram:8204583385}"

openclaw message send \
  --channel telegram \
  --target "$TARGET" \
  --message "$MSG"
