---
name: coding-session-router
description: Route coding tasks between cursor-agent and opencode with a session-first strategy. Use for any non-trivial coding work (feature work, multi-file edits, refactors, debugging loops, tests, long-running tasks). Prefer cursor-agent for quick one-shot coding and opencode for long-lived resumable sessions. Do not use for trivial one-liner edits.
---

# coding-session-router

Use this as the default coding skill unless the task is truly trivial.

## Routing policy

- **Trivial task** (one-liner/simple single-file tiny fix): do direct edit, no agent CLI needed.
- **Quick coding task** (small-medium, short context): use `cursor-agent`.
- **Long-lived coding session** (iterative work, resume needed, project track): use `opencode`.

## Why

- `cursor-agent` is fast and ergonomic for quick execution.
- `opencode` has cleaner session lifecycle controls for long-term work:
  - `--continue`
  - `--session <id>`
  - `session list`
  - `--fork`

## Standard commands

### Quick mode (cursor-agent)

```bash
cursor-agent --trust -p "<task>"
```

Continue latest:

```bash
cursor-agent --trust --continue -p "<next step>"
```

Continue specific chat:

```bash
cursor-agent --trust --resume <chat_id> -p "<next step>"
```

### Deep mode (opencode)

```bash
opencode run "<task>"
```

Continue latest:

```bash
opencode run --continue "<next step>"
```

Continue explicit session:

```bash
opencode run --session <session_id> "<next step>"
```

List sessions:

```bash
opencode session list
```

## OpenClaw execution note

When invoking these CLIs through OpenClaw `exec`, use `pty:true`.

## Default behavior commitment

For coding requests, if not explicitly trivial:
1. choose this skill,
2. route to cursor/opencode per policy,
3. keep resumability in mind from the first run (record session id when relevant).
