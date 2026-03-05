---
id: domain-assistant-operations
title: Assistant Operations Patterns
level: domain
priority: P1
status: active
tags: [operations, lessons, workflow]
source: reflection
created_at: 2026-03-05T02:46:00Z
updated_at: 2026-03-05T02:46:00Z
related: []
---

# Assistant Operations Patterns

- Use reflective consolidation as a two-layer process: mechanical collection + agent judgment.
- For agent-participating scheduled tasks, prefer OpenClaw cron `agentTurn` payloads over plain system cron.
- Validate cron behavior with explicit run/status checks after creation to avoid silent failures.
