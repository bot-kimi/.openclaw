#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: tools/tpu_runlong.sh '<command>' '<label>'"
  exit 1
fi

CMD="$1"
LABEL="$2"
TASKS_JSON="/home/jasm/.openclaw/workspace/.openclaw/taskboard/tasks.json"

python3 - <<'PY'
import json, sys
from pathlib import Path
p=Path('/home/jasm/.openclaw/workspace/.openclaw/taskboard/tasks.json')
if not p.exists():
    sys.exit(0)
arr=json.loads(p.read_text())
r=[t for t in arr if t.get('status')=='running' and str(t.get('label','')).startswith('tpu-')]
if r:
    print('BLOCKED: running TPU tasks exist:')
    for t in r:
        print(f"- {t.get('id')} {t.get('label')}")
    sys.exit(42)
PY

exec /home/jasm/.openclaw/workspace/tools/runlong.sh "$CMD" "$LABEL"
