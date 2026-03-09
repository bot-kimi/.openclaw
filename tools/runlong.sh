#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: tools/runlong.sh '<command>' [label] [tags] [timeout-sec] [alarm-after-sec] [notify-channel] [notify-target]"
  exit 1
fi

CMD="$1"
LABEL="${2:-long-task}"
TAGS="${3:-}"
TIMEOUT="${4:-}"
ALARM_AFTER="${5:-}"
NOTIFY_CHANNEL="${6:-}"
NOTIFY_TARGET="${7:-}"
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

if [[ -n "$TIMEOUT" ]]; then
  ARGS+=(--timeout-sec "$TIMEOUT")
fi

if [[ -n "$ALARM_AFTER" ]]; then
  ARGS+=(--alarm-after-sec "$ALARM_AFTER")
fi

if [[ -n "$NOTIFY_CHANNEL" ]]; then
  ARGS+=(--notify-channel "$NOTIFY_CHANNEL")
fi

if [[ -n "$NOTIFY_TARGET" ]]; then
  ARGS+=(--notify-target "$NOTIFY_TARGET")
fi

python3 tools/wakebridge.py "${ARGS[@]}"
