# WakePing

把“长命令开始/结束通知”直接接到 OpenClaw 的最小工具。

- 不依赖 output pattern
- 开始时自动发一条
- 结束时自动发一条（带 exit code、耗时、尾部输出）

> 适合你刚刚说的最简需求：只要 start + end。

## 用法

```bash
python3 tools/wakeping.py \
  --cmd 'bash ./command.sh' \
  --channel telegram \
  --target @your_chat_or_id \
  --label 'command.sh'
```

可选参数：

- `--cwd <dir>`：命令执行目录
- `--tail-lines <n>`：结束消息附带的输出行数（默认 8）

## 说明

WakePing 内部通过：

```bash
openclaw message send --channel <channel> --target <target> --message <text>
```

来发送通知。

因此它适用于 OpenClaw 已支持的消息渠道（如 Telegram/Discord/Signal 等）。

## Webchat 限制

当前 webchat 会话通常没有可供 CLI 直接发送的 `channel+target` 路由标识，
所以这个桥接器主要用于“已接入并可定向发送”的外部渠道。
