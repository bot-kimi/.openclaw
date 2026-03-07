#!/usr/bin/env bash
set -euo pipefail

# Schedule a one-shot delayed command execution wake event for this session.
# The agent should execute the decoded command when the DELAYRUN system event arrives.

AFTER=""
CMD=""
LABEL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --after)
      AFTER="${2:-}"; shift 2 ;;
    --cmd)
      CMD="${2:-}"; shift 2 ;;
    --label)
      LABEL="${2:-}"; shift 2 ;;
    *)
      echo "Unknown arg: $1" >&2
      echo "Usage: tools/delayrun.sh --after <duration> --cmd '<command>' [--label <name>]" >&2
      exit 1 ;;
  esac
done

if [[ -z "$AFTER" || -z "$CMD" ]]; then
  echo "Usage: tools/delayrun.sh --after <duration> --cmd '<command>' [--label <name>]" >&2
  exit 1
fi

if [[ -z "$LABEL" ]]; then
  LABEL="delayrun"
fi

CMD64="$(printf '%s' "$CMD" | base64 -w0)"
NAME="delayrun-${LABEL}-$(date +%s)"
TEXT="DELAYRUN label=${LABEL} cmd64=${CMD64}"

openclaw cron add \
  --name "$NAME" \
  --at "$AFTER" \
  --delete-after-run \
  --system-event "$TEXT" \
  --json
