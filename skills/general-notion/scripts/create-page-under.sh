#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Usage: $0 <parent_page_id> \"<title>\" \"<content>\"" >&2
  exit 1
fi

PARENT_RAW="$1"
TITLE="$2"
CONTENT="$3"

fmt_id() {
  local raw="$1"
  raw="${raw//-/}"
  if [ ${#raw} -eq 32 ]; then
    echo "${raw:0:8}-${raw:8:4}-${raw:12:4}-${raw:16:4}-${raw:20:12}"
  else
    echo "$1"
  fi
}
PARENT_ID="$(fmt_id "$PARENT_RAW")"

get_key() {
  if [ -n "${NOTION_API_KEY:-}" ]; then echo "$NOTION_API_KEY"; return; fi
  if [ -f "$HOME/.config/notion/api_key" ]; then cat "$HOME/.config/notion/api_key"; return; fi
  python3 - << 'PY'
import json
p='/home/jasm/.openclaw/openclaw.json'
try:
    with open(p,'r',encoding='utf-8') as f:
        j=json.load(f)
    print(j.get('skills',{}).get('entries',{}).get('notion',{}).get('apiKey',''))
except Exception:
    print('')
PY
}
KEY="$(get_key | tr -d '\n')"
[ -n "$KEY" ] || { echo "No Notion API key" >&2; exit 2; }
export KEY PARENT_ID TITLE CONTENT

python3 - << 'PY'
import json, os, urllib.request
key=os.environ['KEY']
parent=os.environ['PARENT_ID']
title=os.environ['TITLE']
content=os.environ['CONTENT']
payload={
  "parent":{"page_id":parent},
  "properties":{"title":{"title":[{"type":"text","text":{"content":title}}]}},
  "children":[{"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":content}}]}}]
}
req=urllib.request.Request('https://api.notion.com/v1/pages', data=json.dumps(payload).encode(), method='POST', headers={
  'Authorization': f'Bearer {key}',
  'Notion-Version': '2025-09-03',
  'Content-Type': 'application/json'
})
with urllib.request.urlopen(req, timeout=30) as r:
  out=json.loads(r.read().decode())
print(out.get('id','unknown'))
PY
