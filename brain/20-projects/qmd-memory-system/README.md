---
id: proj-qmd-memory-system-readme
title: QMD Hierarchical Memory System
level: project
priority: P1
status: active
tags: [memory, qmd, architecture]
source: reflection
created_at: 2026-03-05T02:46:00Z
updated_at: 2026-03-05T02:46:00Z
related: []
---

# QMD Hierarchical Memory System

## Goal
Build a hierarchical memory workflow where capture, recall, and daily consolidation are operational and maintainable.

## Scope
- `brain/` hierarchy (top/domains/projects/sessions/inbox/daily/archive)
- `skills/qmd-memory/` for standardized memory actions
- cron-based daily reflection trigger and consolidation pipeline

## Current State
- Skeleton + QMD retrieval + capture hooks + skill packaging are complete.
- Daily consolidation is scheduled; reflective pass is prompted via OpenClaw cron.
