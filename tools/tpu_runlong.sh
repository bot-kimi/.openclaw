#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: tools/tpu_runlong.sh '<command>' '<label>' '<vm-name>'"
  echo ""
  echo "VM-level mutex: blocks only when the same vm:<name> already has"
  echo "an op:init task running.  Different VMs run concurrently."
  exit 1
fi

CMD="$1"
LABEL="$2"
VM="$3"
TAGS="vm:${VM},op:init"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# VM-level mutex check via taskboard tags
if ! python3 "${SCRIPT_DIR}/taskboard.py" check-mutex --tags "$TAGS"; then
  echo "BLOCKED: a running task already holds tags [$TAGS]"
  exit 42
fi

exec python3 "${SCRIPT_DIR}/wakebridge.py" \
  --cmd "$CMD" \
  --label "$LABEL" \
  --cwd "$(pwd)" \
  --emit-start \
  --tags "$TAGS"
