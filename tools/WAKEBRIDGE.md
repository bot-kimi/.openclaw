# WakeBridge

用于 webchat 场景的“后台命令完成即唤醒”桥接器。

思路：
- 后台运行命令
- 通过 `openclaw system event --mode now` 发送**结构化短事件**（`WB_START`/`WB_DONE`）
- 让主会话在命令结束时被立即唤醒并回消息，同时尽量降低系统提示噪音

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
python3 tools/wakebridge.py --cmd 'bash ./command.sh' --label 'command.sh' --cwd /home/jasm/.openclaw/workspace --emit-start &
```

然后当前会话会先收到“已开始”；
命令结束时，WakeBridge 会触发系统事件，主会话会再发“已结束”。

## 一键方式（推荐）

新增了包装脚本：

```bash
tools/runlong.sh 'bash ./command.sh' 'command.sh'
```

它会自动：
- 使用当前目录作为 `--cwd`
- 打开 `--emit-start`
- 保留结束事件推送
