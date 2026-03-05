#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/jasm/.openclaw/workspace"
DAY="$(date -u +"%Y-%m-%d")"
OUT="$ROOT/brain/50-daily/${DAY}.md"
INBOX_DIR="$ROOT/brain/40-inbox/entries"

mkdir -p "$ROOT/brain/50-daily"

{
  echo "# Daily Consolidation - ${DAY}"
  echo
  echo "Generated at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo
  echo "## Inbox entries captured today"
  ls "$INBOX_DIR"/${DAY}-*.md 2>/dev/null | sed 's#^.*/#- #' || echo "- none"
  echo
  echo "## Suggested promotions"
  echo "- Promote stable user preferences/constraints to 00-top/MASTER_MEMORY.md"
  echo "- Promote task-specific items to 20-projects/<project>/"
  echo "- Keep unresolved quick notes in inbox"
} > "$OUT"

echo "Wrote: $OUT"
