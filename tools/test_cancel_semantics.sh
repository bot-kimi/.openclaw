#!/usr/bin/env bash
# Deterministic self-test: cancel semantics end-to-end.
# Verifies that taskboard cancel sets status=cancelled and that
# wakebridge WB_DONE reports status=CANCELLED, exit=-1.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="$(dirname "$SCRIPT_DIR")"
TASKBOARD="$SCRIPT_DIR/taskboard.py"
WAKEBRIDGE="$SCRIPT_DIR/wakebridge.py"
TASKS_FILE="$WORKSPACE/.openclaw/taskboard/tasks.json"
TB_PORT=19876
PASS=0
FAIL=0

cleanup() {
  if [[ -n "${TB_PID:-}" ]]; then
    kill "$TB_PID" 2>/dev/null || true
    wait "$TB_PID" 2>/dev/null || true
  fi
  if [[ -n "${WB_PID:-}" ]]; then
    kill "$WB_PID" 2>/dev/null || true
    wait "$WB_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

assert_eq() {
  local desc="$1" expected="$2" actual="$3"
  if [[ "$expected" == "$actual" ]]; then
    echo "  PASS: $desc (got '$actual')"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $desc — expected '$expected', got '$actual'"
    FAIL=$((FAIL + 1))
  fi
}

assert_contains() {
  local desc="$1" needle="$2" haystack="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    echo "  PASS: $desc (contains '$needle')"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $desc — expected to contain '$needle', got: $haystack"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Cancel Semantics Test ==="
echo ""

# ── 1. Start taskboard server ──────────────────────────────────────
echo "[1] Starting taskboard server on port $TB_PORT …"
python3 "$TASKBOARD" serve --port "$TB_PORT" &
TB_PID=$!
sleep 1
echo "    taskboard PID=$TB_PID"

# ── 2. Direct taskboard cancel test (no wakebridge) ───────────────
echo ""
echo "[2] Test: taskboard cancel sets status=cancelled"
TASK_ID=$(python3 "$TASKBOARD" add --id "test-cancel-1" --label "direct-cancel-test" --cmd "sleep 999" --pid 1)
python3 "$TASKBOARD" cancel --id "$TASK_ID" >/dev/null
STATUS=$(python3 "$TASKBOARD" list --json | python3 -c "
import sys, json
for t in json.load(sys.stdin):
    if t['id'] == '$TASK_ID':
        print(t['status'])
        break
")
assert_eq "taskboard cancel sets status" "cancelled" "$STATUS"

EXIT_CODE=$(python3 "$TASKBOARD" list --json | python3 -c "
import sys, json
for t in json.load(sys.stdin):
    if t['id'] == '$TASK_ID':
        print(t['exitCode'])
        break
")
assert_eq "taskboard cancel sets exitCode" "-1" "$EXIT_CODE"

# ── 3. Update must not overwrite cancelled ────────────────────────
echo ""
echo "[3] Test: taskboard update refuses to overwrite cancelled"
python3 "$TASKBOARD" update --id "$TASK_ID" --status "failed" 2>/dev/null
STATUS=$(python3 "$TASKBOARD" list --json | python3 -c "
import sys, json
for t in json.load(sys.stdin):
    if t['id'] == '$TASK_ID':
        print(t['status'])
        break
")
assert_eq "update did not overwrite cancelled" "cancelled" "$STATUS"

# ── 4. Wakebridge cancel flow (WB_DONE must say CANCELLED) ───────
echo ""
echo "[4] Test: wakebridge WB_DONE reports CANCELLED after taskboard cancel"

# Override TASKBOARD_URL so wakebridge talks to our test server
export TASKBOARD_URL="http://127.0.0.1:$TB_PORT/api/tasks"

# Capture wakebridge + system event output
WB_LOG=$(mktemp /tmp/wb_cancel_test.XXXXXX)

# We need to intercept the system event.  Stub openclaw command.
STUB_DIR=$(mktemp -d /tmp/wb_stub.XXXXXX)
cat > "$STUB_DIR/openclaw" << 'STUBEOF'
#!/usr/bin/env bash
echo "STUB_EVENT: $*" >> "${WB_EVENT_LOG}"
STUBEOF
chmod +x "$STUB_DIR/openclaw"
export PATH="$STUB_DIR:$PATH"
export WB_EVENT_LOG="$WB_LOG"

# Start wakebridge with a long sleep (we'll cancel it)
python3 "$WAKEBRIDGE" \
  --cmd "sleep 300" \
  --label "wb-cancel-test" \
  --no-system-alarm \
  --tail-lines 5 \
  > /dev/null 2>&1 &
WB_PID=$!
sleep 2

# Find the wakebridge task ID from tasks.json
WB_TASK_ID=$(python3 -c "
import json, sys
tasks = json.load(open('$TASKS_FILE'))
for t in tasks:
    if t.get('label') == 'wb-cancel-test' and t.get('status') == 'running':
        print(t['id'])
        break
")

if [[ -z "$WB_TASK_ID" ]]; then
  echo "  FAIL: could not find wb-cancel-test task in taskboard"
  FAIL=$((FAIL + 1))
else
  echo "    wakebridge task ID=$WB_TASK_ID, PID=$WB_PID"

  # Cancel via taskboard
  python3 "$TASKBOARD" cancel --id "$WB_TASK_ID" >/dev/null
  echo "    cancel issued, waiting for wakebridge to exit…"
  # Wait for wakebridge to finish (signal delivered, process exits)
  wait "$WB_PID" 2>/dev/null || true
  WB_PID=""
  sleep 1

  # Check tasks.json — status must still be cancelled (not overwritten)
  TB_STATUS=$(python3 -c "
import json
tasks = json.load(open('$TASKS_FILE'))
for t in tasks:
    if t['id'] == '$WB_TASK_ID':
        print(t['status'])
        break
")
  assert_eq "tasks.json status after WB exit" "cancelled" "$TB_STATUS"

  TB_EXIT=$(python3 -c "
import json
tasks = json.load(open('$TASKS_FILE'))
for t in tasks:
    if t['id'] == '$WB_TASK_ID':
        print(t['exitCode'])
        break
")
  assert_eq "tasks.json exitCode after WB exit" "-1" "$TB_EXIT"

  # Check WB_DONE event text
  if [[ -f "$WB_LOG" ]]; then
    WB_DONE_LINE=$(grep "WB_DONE" "$WB_LOG" || echo "")
    if [[ -n "$WB_DONE_LINE" ]]; then
      assert_contains "WB_DONE contains status=CANCELLED" "status=CANCELLED" "$WB_DONE_LINE"
      assert_contains "WB_DONE contains exit=-1" "exit=-1" "$WB_DONE_LINE"
    else
      echo "  FAIL: no WB_DONE event found in log"
      FAIL=$((FAIL + 1))
      FAIL=$((FAIL + 1))
    fi
  else
    echo "  FAIL: WB event log not found"
    FAIL=$((FAIL + 1))
    FAIL=$((FAIL + 1))
  fi
fi

# ── cleanup temp files ────────────────────────────────────────────
rm -f "$WB_LOG"
rm -rf "$STUB_DIR"

# ── Summary ───────────────────────────────────────────────────────
echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
exit 0
