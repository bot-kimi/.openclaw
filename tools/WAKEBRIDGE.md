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
| `--timeout-sec` | *(none)* | Kill process after N seconds, mark as timed-out (exit 124) |
| `--no-system-alarm` | off | Skip automatic system-alarm for long tasks |
| `--notify-channel` | *(none)* | Also send WB_START/WB_DONE/WB_ALARM as direct channel message |
| `--notify-target` | *(none)* | Direct message target, e.g. `telegram:8204583385` |

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

If you need guaranteed in-chat notifications for a specific thread/chat, pass channel+target:

```bash
tools/runlong.sh 'bash ./command.sh' 'command.sh' '' '' '120' 'telegram' 'telegram:8204583385'
```

## TaskBoard integration

WakeBridge automatically registers each run on the TaskBoard (`tools/taskboard.py`):

1. On start: adds a task with status `running`
2. On completion: updates to `completed` or `failed` with exit code, duration, and tail output

To disable: pass `--no-taskboard`.

View tasks: `python3 tools/taskboard.py list` or `python3 tools/taskboard.py serve`.

## Timeout

When `--timeout-sec N` is set, the process is killed after N seconds and marked as failed with a `TIMEOUT` status message. Exit code is set to 124.

## System-alarm (automatic)

When `--timeout-sec > 20` and the task is not itself an alarm (no `alarm` or `system-alarm` tag), WakeBridge automatically creates a paired alarm task:

- Tagged `system-alarm,parent:<task_id>`
- Fires `WB_ALARM` system event at timeout+10s if main task hasn't finished
- Auto-cancelled (status=`cancelled`) when main task finishes early

Disable with `--no-system-alarm`.

## Events emitted

- `WB_START`: label, timestamp, command (only with `--emit-start`)
- `WB_DONE`: label, status (SUCCESS/FAILED/TIMEOUT), exit code, duration, command, tail output
- `WB_ALARM`: parent task ID, label (only from system-alarm when task may be stuck)
