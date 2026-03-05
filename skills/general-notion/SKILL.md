---
name: general-notion
description: General-purpose Notion operations for Kimi (create pages, append notes, query databases). Use when user asks to write/read/update content in Notion pages or databases, including daily logs, project notes, and ad-hoc captures.
---

# general-notion

## Create a page under a parent page

```bash
skills/general-notion/scripts/create-page-under.sh <parent_page_id> "<title>" "<content>"
```

## Create a page in a database

```bash
skills/general-notion/scripts/create-db-page.sh <database_id> "<title>" "<content>"
```

## Notes

- API key resolution order:
  1) `NOTION_API_KEY` env
  2) `~/.config/notion/api_key`
  3) `~/.openclaw/openclaw.json` -> `skills.entries.notion.apiKey`
- Uses Notion-Version `2025-09-03`
