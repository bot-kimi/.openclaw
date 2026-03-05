#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/jasm/.openclaw/workspace"
OPENCLAW_ROOT="/kmh-nfs-ssd-us-mount/code/siri/.openclaw"
SESSIONS_DIR="$OPENCLAW_ROOT/agents/main/sessions"
DAY="$(date -u +"%Y-%m-%d")"
MONTH="$(date -u +"%Y-%m")"
NOW="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

SESSION_OUT_DIR="$ROOT/brain/30-sessions/$MONTH"
DAILY_OUT="$ROOT/brain/50-daily/${DAY}.md"
INBOX_DIR="$ROOT/brain/40-inbox/entries"
MASTER="$ROOT/brain/00-top/MASTER_MEMORY.md"

mkdir -p "$SESSION_OUT_DIR" "$ROOT/brain/50-daily"

# 1) Snapshot today's session messages into per-session markdown
python3 - << 'PY'
import json,glob,os,datetime
root='/kmh-nfs-ssd-us-mount/code/siri/.openclaw/agents/main/sessions'
out_root='/home/jasm/.openclaw/workspace/brain/30-sessions/' + datetime.datetime.utcnow().strftime('%Y-%m')
day=datetime.datetime.utcnow().strftime('%Y-%m-%d')
os.makedirs(out_root, exist_ok=True)

def extract_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts=[]
        for p in content:
            if isinstance(p, dict):
                t=p.get('text') or p.get('content') or ''
                if isinstance(t,str): parts.append(t)
            elif isinstance(p,str):
                parts.append(p)
        return ' '.join(parts)
    return ''

for fp in glob.glob(os.path.join(root,'*.jsonl')):
    sid=os.path.basename(fp).replace('.jsonl','')
    out=os.path.join(out_root, f'{day}-{sid}.md')
    rows=[]
    try:
        with open(fp,'r',encoding='utf-8') as f:
            for line in f:
                line=line.strip()
                if not line: continue
                try:
                    obj=json.loads(line)
                except Exception:
                    continue
                ts=(obj.get('timestamp') or obj.get('createdAt') or obj.get('time') or '')
                ts_s=str(ts)
                if day not in ts_s:
                    continue
                role=obj.get('role') or obj.get('type') or 'unknown'
                text=extract_text(obj.get('content'))
                if not text:
                    # fallback for nested message structures
                    msg=obj.get('message')
                    if isinstance(msg, dict):
                        text=extract_text(msg.get('content'))
                text=' '.join(text.split())
                if text:
                    rows.append((ts_s, role, text[:800]))
    except FileNotFoundError:
        continue

    if not rows:
        continue

    with open(out,'w',encoding='utf-8') as w:
        w.write('---\n')
        w.write(f'id: session-{day}-{sid}\n')
        w.write(f'title: Session Snapshot {sid} {day}\n')
        w.write('level: session\npriority: P2\nstatus: active\n')
        w.write('tags: [session,raw]\nsource: system\n')
        w.write(f'created_at: {datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}\n')
        w.write(f'updated_at: {datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}\n')
        w.write('related: []\n---\n\n')
        w.write(f'# Session Snapshot ({day})\n\n')
        for ts,role,text in rows:
            w.write(f'- [{ts}] **{role}**: {text}\n')
PY

# 2) Build daily consolidation report
{
  echo "---"
  echo "id: daily-${DAY}"
  echo "title: Daily Consolidation ${DAY}"
  echo "level: daily"
  echo "priority: P1"
  echo "status: active"
  echo "tags: [daily,consolidation]"
  echo "source: system"
  echo "created_at: ${NOW}"
  echo "updated_at: ${NOW}"
  echo "related: []"
  echo "---"
  echo
  echo "# Daily Consolidation - ${DAY}"
  echo
  echo "Generated at: ${NOW}"
  echo
  echo "## Session snapshots"
  ls "$SESSION_OUT_DIR"/${DAY}-*.md 2>/dev/null | sed 's#^.*/#- #' || echo "- none"
  echo
  echo "## Inbox entries captured today"
  ls "$INBOX_DIR"/${DAY}-*.md 2>/dev/null | sed 's#^.*/#- #' || echo "- none"
  echo
  echo "## Promotion checklist"
  echo "- [ ] Promote hard constraints/preferences to 00-top/MASTER_MEMORY.md (P0)"
  echo "- [ ] Move project-specific items into 20-projects/<project>/ (P1)"
  echo "- [ ] Keep unresolved small notes in 40-inbox/ (P2)"
  echo
  echo "## Integrity checks"
  echo "- [ ] No session file missing for today"
  echo "- [ ] No inbox note left unreferenced"
  echo "- [ ] qmd index refreshed"
} > "$DAILY_OUT"

# 3) Refresh QMD index/embeddings (best effort)
qmd update >/tmp/qmd_daily_update.log 2>&1 || true
qmd embed >/tmp/qmd_daily_embed.log 2>&1 || true

# 4) Stamp master memory with last consolidation timestamp
if grep -q "Last daily consolidation:" "$MASTER"; then
  sed -i "s#Last daily consolidation: .*#Last daily consolidation: ${NOW}#" "$MASTER"
else
  printf "\n- Last daily consolidation: %s\n" "$NOW" >> "$MASTER"
fi

echo "Wrote: $DAILY_OUT"
