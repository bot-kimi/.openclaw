# Quick Capture (Step 3)

Use this to jot notes instantly; organize later during daily consolidation.

## Command

```bash
brain/tools/capture-note.sh "<note text>" "tag1,tag2" "P2"
```

Examples:

```bash
brain/tools/capture-note.sh "User wants weekly summary every Friday" "user-pref,planning" "P1"
brain/tools/capture-note.sh "Check CUDA setup for faster QMD" "infra,qmd" "P2"
```

## Behavior

- Creates a timestamped file in `brain/40-inbox/entries/`
- Appends a pointer line to `brain/40-inbox/INBOX.md`
- Defaults:
  - tags = `quick-note`
  - priority = `P2`
