---
id: domain-hh-onboarding-hierarchy
title: HH Onboarding Hierarchy
status: active
updated_at: 2026-03-08T00:45:00Z
tags: [onboarding, hierarchy, general-practice, compute, storage, other]
---

# HH Onboarding Hierarchy

## 1) General Practice

- One experiment, one code directory snapshot, one results/logs directory.
- Run experiments from copied snapshot directory (reproducibility).
- Record every experiment in spreadsheet:
  - file: `kimi-worksheet`
  - default tab: `general`
  - create extra tabs for specific tracks.

## 2) Compute (TPU)

- TPU infra is remote; local operations do not directly affect remote TPU VMs.
- Use `kimi_tpu.sh` for TPU lifecycle and remote execution.
- Known mapping: `v5p-64` has 8 workers.
- Worker-local root/tmp is not shared across workers.
- Hard constraint: current session lives on dev VM `v4-8-1` tmux; never reboot `v4-8-1`, never clear `/tmp` there.

## 3) Storage

- Primary experiment buckets: `us-central1`, `us-east5`, `asia-northeast1-b`.
- Keep compute region and storage region aligned (avoid cross-region transfer).
- Current shared filestore: `/kmh-nfs-ssd-us-mount`.
- `staging`: per-experiment code snapshot area (history of run code copies).
- `logs`: run log archive.
- Most code should live under `/kmh-nfs-ssd-us-mount/code/...`.
- Workspace/home for temporary debugging scripts only.
- My code home: `/kmh-nfs-ssd-us-mount/code/jasm`.

## 4) Other

### A. Safety / survival constraints
- Do not reboot dev VM `v4-8-1`.
- Do not clear `/tmp` on dev VM `v4-8-1`.

### B. Tooling / collaboration conventions
- `skills/kimi-tpu` is single-purpose for `kimi_tpu.sh` workflows.
- Keep TPU operation, storage policy, and experiment policy as separate modules/notes.
