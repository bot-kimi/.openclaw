# USER.md - About Your Human

_Learn about the person you're helping. Update this as you go._

- **Name:**
- **What to call them:**
- **Pronouns:** _(optional)_
- **Timezone:** UTC-5 (provisional; inferred 2026-03-05)
- **Notes:**
  - Assigned assistant name: Kimi (2026-03-05 UTC)
  - Git workflow preference: commits do not require prior confirmation (2026-03-05 UTC)
  - Memory hook preference: when user says "记住这个", auto-capture a quick note via advanced qmd-memory workflow (2026-03-05 UTC; reinforced 2026-03-07 UTC)
  - Memory workflow preference: use advanced memory system (qmd-memory) as the default/primary recall path; do not rely on OpenClaw memory_search for normal recall (2026-03-07 UTC)
  - Consolidation schedule preference: run daily at 03:00 in user's local timezone (2026-03-05 UTC)
  - Notion integration preference: after each consolidation, create a daily report page in Notion database `31a84f61933e80358481f064fe64b58c` with 3 sections (done well/improve), and treat `Jasmine's home` page as Kimi's living notebook (2026-03-05 UTC)
  - Daily report language preference: content posted to Notion should be in Chinese (2026-03-05 UTC)
  - Coding workflow preference: for non-trivial coding tasks, always use the `coding-session-router` skill (cursor-agent for quick tasks, opencode for long-lived resumable sessions) (2026-03-05 UTC)
  - Git workflow preference: after every git commit, always push (2026-03-05 UTC)
  - Long-running command workflow HARD rule: “后台执行” means using WakeBridge/`tools/runlong.sh` (not plain background exec), to ensure start/end/failure notifications in-session (2026-03-07 UTC; reinforced 2026-03-08 UTC)
  - Coding workflow stability preference: when using coding skills/agents, always run agent in background and rely on completion wake-up; never block the main chat turn with foreground coding runs (2026-03-07 UTC)
  - Infra workflow reminder: for private/org GitHub repos, clone via SSH (`git@github.com:owner/repo.git`) using existing SSH key; do not default to HTTPS (2026-03-07 UTC)
  - Experiment tracking preference: sync all experiment records to Google Sheets master file `general` (ID: `1vsic-xRGf6uzWJ58SUGNEE116FnInfAiWKePLj0bA34`); use sub-sheets/tabs for specific experiment tracks (2026-03-07 UTC)
  - TPU local-dev default python rule: use `/kmh-nfs-ssd-us-mount/code/hanhong/miniforge3/bin/python` by default; do not casually install packages into this shared environment (2026-03-08 UTC)
  - Background execution HARD rule: “后台执行” strictly means WakeBridge (`tools/runlong.sh`), not plain background exec; require start/end/failure notifications (reinforced 2026-03-08 UTC)
  - Task monitoring reliability rule: if TaskBoard UI (`tools/taskboard.py` on :9876) is down, WakeBridge should fail fast and force recovery before long tasks (2026-03-08 UTC)
  - Heartbeat discrimination rule: never reply `HEARTBEAT_OK` to WakeBridge/system status messages (`WB_START`/`WB_DONE`/`Exec completed`); treat them as task status events (2026-03-08 UTC)
  - TPU multi-host init rule: remote TPU ops/init must default to `--worker=all`; multi-worker TPU must initialize simultaneously (2026-03-08 UTC)
  - TPU contention handling rule: if others occupy TPU, delete mapping/ignore card first (do not kill others without explicit authorization); when no occupancy, clear `/tmp/*tpu*` then retry init (2026-03-08 UTC)

## Context

_(What do they care about? What projects are they working on? What annoys them? What makes them laugh? Build this over time.)_

---

The more you know, the better you can help. But remember — you're learning about a person, not building a dossier. Respect the difference.
