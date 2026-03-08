---
name: kimi-tpu
description: Operate the HH group TPU infrastructure on GCP using kimi_tpu.sh and strict region/compliance rules. Use when requesting or managing TPU VMs, checking TPU availability, SSHing into TPU VMs, handling TPU contention/preemption, or preparing safe TPU experiment runs under group policy.
---

# kimi-tpu

Use this skill as the default workflow for TPU operations in HH group infra.

## Hard constraints

- Never reboot dev VM `v4-8-1`.
- Never clear `/tmp` on dev VM `v4-8-1`.
- Never perform cross-region data transfers for large data/checkpoints.
- Never use personal accounts for training jobs.

## Pre-run compliance check (always)

Run before long jobs:

```bash
gcloud auth list
echo $GOOGLE_APPLICATION_CREDENTIALS
```

Ensure account + service account match VM region.

## TPU VM lifecycle (kimi_tpu.sh)

Check available quotas/types:

```bash
./kimi_tpu.sh available
```

Create VM (spot default):

```bash
./kimi_tpu.sh create <vm-name> --zone=<zone> --accelerator-type=<type>
```

List VMs:

```bash
./kimi_tpu.sh list
```

SSH into VM:

```bash
./kimi_tpu.sh ssh <vm-name> --zone <zone>
```

Delete VM:

```bash
./kimi_tpu.sh delete <vm-name> --zone <zone>
```

## TPU contention debug

If TPU backend init fails, check whether someone else is using TPU:

```bash
./kimi_tpu.sh ssh <vm-name> --zone <zone> --command "ps -ef | grep python | grep -v grep"
```

Only apply cleanup actions if TPU is truly idle and policy allows.

## Storage rules (critical)

- Prefer same-region bucket for checkpoints.
- Keep compute region and storage region aligned.
- Avoid large reads from `/kmh-nfs-ssd-us-mount` unless region-appropriate.

## Experiment hygiene

- One experiment = one code directory copy + one results/logs directory.
- Record experiments in spreadsheet `kimi-worksheet`, tab `general` (or dedicated tabs).
