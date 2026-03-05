# Hierarchical Memory Reference

Primary tree (under `brain/`):

- `00-top/`: highest-priority persistent memory
- `10-domains/`: durable topic memory
- `20-projects/`: project/task specific memory
- `30-sessions/`: raw session traces
- `40-inbox/`: quick capture queue
- `50-daily/`: daily consolidation outputs
- `90-archive/`: cold storage

Promotion rule:
- Inbox/session notes are raw.
- Promote only stable or decision-level information.
- Keep links between promoted notes and raw source files.
