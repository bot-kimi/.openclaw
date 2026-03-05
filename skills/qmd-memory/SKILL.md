---
name: qmd-memory
description: QMD-based hierarchical memory operations for Kimi. Use when handling memory capture, recall, prioritization, or consolidation tasks. Triggers include user phrases like "记住这个", "帮我记一下", "回忆一下", "之前我们说过", "查一下我记过什么", and any request to store/retrieve structured notes in hierarchical memory.
---

# qmd-memory

Use this skill as the default memory workflow.

## Execute capture

When user asks to remember something (especially `记住这个`):

1. If content is provided, capture immediately.
2. If content is missing, ask one short follow-up: `要记什么？`
3. Default capture params:
   - tags: `user-memory,quick-capture`
   - priority: `P1`

Run:

```bash
skills/qmd-memory/scripts/capture-trigger.sh "<user text>"
```

Or explicit capture:

```bash
skills/qmd-memory/scripts/capture-note.sh "<note>" "tag1,tag2" "P1"
```

## Execute recall

For retrieval requests, use:

```bash
skills/qmd-memory/scripts/recall.sh "<query>" [fast|semantic|hybrid] [collection]
```

Modes:
- `fast` -> `qmd search`
- `semantic` -> `qmd vsearch`
- `hybrid` -> `qmd query` (default)

Default collection: `brain`

## Hierarchy & prioritization

Follow `references/hierarchy.md`.

- P0: critical constraints, hard requirements, imminent deadlines
- P1: important reusable facts/decisions
- P2: contextual background

Capture first, reorganize during daily consolidation.

## Daily consolidation

Run:

```bash
skills/qmd-memory/scripts/daily-consolidate.sh
```

This script should:
1. sweep inbox entries
2. append daily summary
3. suggest promotions to top/domain/project layers
4. keep raw session traces intact
