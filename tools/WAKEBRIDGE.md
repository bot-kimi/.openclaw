# WakeBridge

Run a command in the background and trigger OpenClaw system events on start/exit.

## Usage

```bash
python3 tools/wakebridge.py \
  --cmd 'bash ./command.sh' \
  --label 'command.sh' \
  --cwd /home/jasm/.openclaw/workspace
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--cmd` | *(required)* | Shell command to run |
| `--label` | `任务` | Display label for events and taskboard |
| `--cwd` | current dir | Working directory |
| `--emit-start` | off | Also emit a `WB_START` system event |
| `--tail-lines` | 12 | Number of tail lines included in exit event |
| `--no-taskboard` | off | Skip TaskBoard registration |

## Background execution

```bash
python3 tools/wakebridge.py \
  --cmd 'bash ./command.sh' \
  --label 'command.sh' \
  --cwd /home/jasm/.openclaw/workspace \
  --emit-start &
```

## One-liner (recommended)

```bash
tools/runlong.sh 'bash ./command.sh' 'command.sh'
```

Automatically sets `--cwd` to current directory and enables `--emit-start`.

## TaskBoard integration

WakeBridge automatically registers each run on the TaskBoard (`tools/taskboard.py`):

1. On start: adds a task with status `running`
2. On completion: updates to `completed` or `failed` with exit code, duration, and tail output

To disable: pass `--no-taskboard`.

View tasks: `python3 tools/taskboard.py list` or `python3 tools/taskboard.py serve`.

## Events emitted

- `WB_START`: label, timestamp, command (only with `--emit-start`)
- `WB_DONE`: label, status (SUCCESS/FAILED), exit code, duration, command, tail output
