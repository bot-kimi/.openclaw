#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/jasm/.openclaw/workspace"
DAY="${1:-$(date -u +"%Y-%m-%d")}"
DAILY_FILE="$ROOT/brain/50-daily/${DAY}.md"
DB_ID_RAW="31a84f61933e80358481f064fe64b58c"
HOME_PAGE_RAW="31a84f61933e80f08d97cb99973a725a"

fmt_id() {
  local raw="$1"
  raw="${raw//-/}"
  if [ ${#raw} -eq 32 ]; then
    echo "${raw:0:8}-${raw:8:4}-${raw:12:4}-${raw:16:4}-${raw:20:12}"
  else
    echo "$1"
  fi
}

DB_ID="$(fmt_id "$DB_ID_RAW")"
HOME_PAGE_ID="$(fmt_id "$HOME_PAGE_RAW")"

get_notion_key() {
  if [ -n "${NOTION_API_KEY:-}" ]; then
    echo "$NOTION_API_KEY"; return
  fi
  if [ -f "$HOME/.config/notion/api_key" ]; then
    cat "$HOME/.config/notion/api_key"; return
  fi
  python3 - << 'PY'
import json, os
p='/home/jasm/.openclaw/openclaw.json'
try:
    with open(p,'r',encoding='utf-8') as f:
        j=json.load(f)
    k=j.get('skills',{}).get('entries',{}).get('notion',{}).get('apiKey')
    if k: print(k)
except Exception:
    pass
PY
}

NOTION_KEY="$(get_notion_key | tr -d '\n')"
if [ -z "$NOTION_KEY" ]; then
  echo "Notion API key not found" >&2
  exit 2
fi
if [ ! -f "$DAILY_FILE" ]; then
  echo "Daily file missing: $DAILY_FILE" >&2
  exit 3
fi

SECTION=$(awk '/^## Reflection Summary/{flag=1;next}/^## /{if(flag)exit}flag' "$DAILY_FILE" || true)
if [ -z "$SECTION" ]; then
  SECTION="- No reflection summary found yet."
fi

export DAY DAILY_FILE NOTION_KEY DB_ID HOME_PAGE_ID SECTION
python3 - << 'PY'
import json, os, re, urllib.request, urllib.error

day=os.environ['DAY']
daily_file=os.environ['DAILY_FILE']
notion_key=os.environ['NOTION_KEY']
db_id=os.environ['DB_ID']
home_page_id=os.environ['HOME_PAGE_ID']
section=os.environ.get('SECTION','')

lines=[l.strip('- ').strip() for l in section.splitlines() if l.strip().startswith('-')]
if not lines:
    lines=["No reflection summary found."]

# "今天做了什么"优先完整覆盖，避免遗漏关键主题（如 onboarding/复盘要点）
today_done=list(lines)
well=[]
improve=[]
for ln in lines:
    l=ln.lower()
    if ('well' in l or 'good' in l or 'success' in l
        or '成功' in ln or '升级' in ln or '完成' in ln or '修复' in ln or '优化' in ln):
        well.append(ln)
    if ('unresolved' in l or 'improve' in l or 'loop' in l or 'risk' in l
        or '改进' in ln or '待' in ln or '问题' in ln or '风险' in ln):
        improve.append(ln)

if not well:
    well=lines[:2] if len(lines) >= 2 else lines
if not improve:
    improve=["继续补齐未闭环事项，并把关键规则固化为可执行检查项。"]

headers={
    'Authorization': f'Bearer {notion_key}',
    'Notion-Version': '2025-09-03',
    'Content-Type': 'application/json'
}

def req(method,url,payload=None):
    data=None if payload is None else json.dumps(payload).encode('utf-8')
    r=urllib.request.Request(url,data=data,headers=headers,method=method)
    with urllib.request.urlopen(r,timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))

# find title property name
prop_name='Name'
try:
    db=req('GET', f'https://api.notion.com/v1/databases/{db_id}')
    props=db.get('properties',{})
    for k,v in props.items():
        if isinstance(v,dict) and v.get('type')=='title':
            prop_name=k
            break
except Exception:
    pass

children=[
  {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"1) 今天做了什么"}}]}},
  *[{"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":t[:1800]}}]}} for t in today_done],
  {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"2) 做得比较好的地方"}}]}},
  *[{"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":t[:1800]}}]}} for t in well],
  {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":"3) 值得改进的事情"}}]}},
  *[{"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":t[:1800]}}]}} for t in improve],
  {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":f"Source: {daily_file}"}}]}}
]

payload={
  "parent":{"database_id":db_id},
  "properties":{
    prop_name:{"title":[{"type":"text","text":{"content":f"Kimi Daily Report {day}"}}]}
  },
  "children":children
}

try:
    out=req('POST','https://api.notion.com/v1/pages',payload)
    print('CREATED_IN_DATABASE', out.get('id','unknown'))
except Exception as e:
    # fallback to home page child page to avoid total loss
    fallback={
      "parent":{"page_id":home_page_id},
      "properties":{"title":{"title":[{"type":"text","text":{"content":f"Kimi Daily Report {day} (fallback)"}}]}},
      "children":children
    }
    out=req('POST','https://api.notion.com/v1/pages',fallback)
    print('CREATED_FALLBACK_PAGE', out.get('id','unknown'))
PY
