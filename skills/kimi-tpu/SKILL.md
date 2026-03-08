---
name: kimi-tpu
description: Manage HH group TPU VMs with kimi_tpu.sh only. Use when listing available TPU types, creating TPU VMs, listing active TPU VMs, SSHing into TPU VMs, deleting TPU VMs, or checking TPU process usage on a VM.
---

# kimi-tpu

Use this skill only for `kimi_tpu.sh` operations.

## Core commands

Check available TPU types:

```bash
./kimi_tpu.sh available
```

Create a TPU VM:

```bash
./kimi_tpu.sh create <vm-name> --zone=<zone> --accelerator-type=<type>
```

List active TPU VMs:

```bash
./kimi_tpu.sh list
```

SSH into a TPU VM:

```bash
./kimi_tpu.sh ssh <vm-name> --zone <zone>
```

Delete a TPU VM:

```bash
./kimi_tpu.sh delete <vm-name> --zone <zone>
```

## Troubleshooting (process occupancy)

Check python processes on a TPU VM:

```bash
./kimi_tpu.sh ssh <vm-name> --zone <zone> --command "ps -ef | grep python | grep -v grep"
```

## Scope boundary

- Keep this skill focused on `kimi_tpu.sh` command workflows only.
- Put compliance/cost/storage/experiment-tracking rules into separate skills or notebooks.
