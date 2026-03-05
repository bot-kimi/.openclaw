#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"query\" [fast|semantic|hybrid] [collection]" >&2
  exit 1
fi

QUERY="$1"
MODE="${2:-hybrid}"
COLLECTION="${3:-brain}"

case "$MODE" in
  fast)
    qmd search "$QUERY" -c "$COLLECTION" --json -n 10
    ;;
  semantic)
    qmd vsearch "$QUERY" -c "$COLLECTION" --json -n 10
    ;;
  hybrid)
    qmd query "$QUERY" --json -n 10
    ;;
  *)
    echo "Invalid mode: $MODE" >&2
    exit 2
    ;;
esac
