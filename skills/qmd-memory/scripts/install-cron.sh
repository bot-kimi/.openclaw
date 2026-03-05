#!/usr/bin/env bash
set -euo pipefail

# Default: run daily at 23:55 UTC
SCHEDULE="${1:-55 23 * * *}"
CMD="/home/jasm/.openclaw/workspace/skills/qmd-memory/scripts/daily-consolidate.sh >> /home/jasm/.openclaw/workspace/brain/50-daily/cron.log 2>&1"
TAG="# qmd-memory-daily-consolidation"

TMP=$(mktemp)
crontab -l 2>/dev/null | grep -v "$TAG" > "$TMP" || true
printf "%s %s %s\n" "$SCHEDULE" "$CMD" "$TAG" >> "$TMP"
crontab "$TMP"
rm -f "$TMP"

echo "Installed cron: $SCHEDULE"
crontab -l | grep "$TAG" || true
