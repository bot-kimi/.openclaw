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
- Treat `openclaw cron run --expect-final` timeouts as potentially ambiguous; verify with `openclaw cron runs --id <job>` before concluding failure.
- Align schedules to the user’s local timezone instead of server UTC defaults when the task is day-bound.
- For non-trivial coding, prefer resumable session workflows (opencode) and keep session IDs for feedback-driven iteration.
- For long-running shell tasks in chat sessions, use WakeBridge (`tools/wakebridge.py` / `tools/runlong.sh`) to send start/finish wake events and avoid silent completions.
- For delayed one-shot execution requests (e.g., "30s later run X"), use DelayRun (`tools/delayrun.sh`) instead of handcrafting cron each time.
