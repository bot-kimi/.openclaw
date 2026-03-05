# Kimi Hierarchical Memory (v1)

This is Kimi's primary memory workspace, inspired by QMD-friendly markdown design.

## Structure

- `00-top/` — highest-priority long-term memory (identity, user profile, core rules)
- `10-domains/` — durable thematic knowledge (work, personal, health, finance, etc.)
- `20-projects/` — task/project-specific memory (active + completed)
- `30-sessions/` — raw session logs by month/day/source
- `40-inbox/` — quick-capture notes (unsorted, timestamped)
- `50-daily/` — daily consolidation outputs
- `90-archive/` — cold storage

## Priority System

- `P0` Critical: must be surfaced first (constraints, deadlines, non-negotiables)
- `P1` Important: strong relevance, regularly reused
- `P2` Contextual: useful but optional/background

## Metadata (frontmatter)

Every memory doc should include:

```yaml
---
id: mem-YYYYMMDD-xxxx
title: 
level: top|domain|project|session|inbox|daily|archive
priority: P0|P1|P2
status: active|draft|resolved|archived
tags: []
source: chat|manual|system|import
created_at: 2026-03-05T00:00:00Z
updated_at: 2026-03-05T00:00:00Z
related: []
---
```

## Rules

1. Capture quickly into `40-inbox/` without friction.
2. Never lose raw details from sessions (`30-sessions/`).
3. Consolidate daily into `50-daily/` and route durable knowledge upward.
4. Promote stable knowledge to `00-top/`, `10-domains/`, or `20-projects/`.
5. Keep docs QMD-searchable: small markdown files, explicit titles/tags, rich context.

## QMD Setup (Step 2)

Collections:
- `brain` -> `./brain/**/*.md`
- `legacy-memory` -> `./memory/**/*.md`

Useful commands:

```bash
# index refresh
qmd update

# embeddings refresh
qmd embed

# fast keyword search
qmd search "<query>" -c brain --json -n 10

# semantic search
qmd vsearch "<query>" -c brain --json -n 10

# best quality hybrid retrieval
qmd query "<query>" --json -n 10
```

Note: On this host, QMD currently runs in CPU mode (CUDA toolkit missing).
