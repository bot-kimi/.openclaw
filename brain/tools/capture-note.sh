#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/jasm/.openclaw/workspace"
INBOX_DIR="$ROOT/brain/40-inbox/entries"
INBOX_INDEX="$ROOT/brain/40-inbox/INBOX.md"

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"note text\" [tags-comma-separated] [priority:P0|P1|P2]" >&2
  exit 1
fi

NOTE_TEXT="$1"
TAGS="${2:-quick-note}"
PRIORITY="${3:-P2}"

NOW_UTC="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
DAY="$(date -u +"%Y-%m-%d")"
STAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
ID="mem-${STAMP}-$(openssl rand -hex 2)"
FILE="$INBOX_DIR/${DAY}-${STAMP}.md"

cat > "$FILE" <<DOC
---
id: ${ID}
title: Inbox Note ${STAMP}
level: inbox
priority: ${PRIORITY}
status: draft
tags: [${TAGS}]
source: chat
created_at: ${NOW_UTC}
updated_at: ${NOW_UTC}
related: []
---

# Note

${NOTE_TEXT}
DOC

# Append entry to INBOX index
printf -- "- [%s] %s (%s) -> entries/%s\n" "$NOW_UTC" "$NOTE_TEXT" "$PRIORITY" "$(basename "$FILE")" >> "$INBOX_INDEX"

echo "Captured: $FILE"
