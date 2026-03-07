# WakeBridge

用于 webchat 场景的“后台命令完成即唤醒”桥接器。

思路：
- 后台运行命令
- 通过 `openclaw system event --mode now` 发送系统事件
- 让主会话在命令结束时被立即唤醒并回消息

## 用法

```bash
python3 tools/wakebridge.py \
  --cmd 'bash ./command.sh' \
  --label 'command.sh' \
  --cwd /home/jasm/.openclaw/workspace
```

可选：
- `--emit-start`：开始时也触发一次唤醒事件
- `--tail-lines 12`：结束事件里附带的输出尾行数

## 推荐执行方式（后台）

```bash
python3 tools/wakebridge.py --cmd 'bash ./command.sh' --label 'command.sh' --cwd /home/jasm/.openclaw/workspace &
```

然后当前会话先回复“已开始执行”；
命令结束时，WakeBridge 会触发系统事件，主会话应可立即发出“已结束”消息。
