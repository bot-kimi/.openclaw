# WakeWatch (MVP)

一个最小可用的“事件驱动唤醒”工具原型：

- 执行长命令
- 实时读取 stdout/stderr
- 命中正则规则时写入事件（JSONL）
- 同时写入 start/exit 事件

> 依赖：Python 3 标准库，无第三方包。

## 用法

```bash
python3 tools/wakewatch.py \
  --cmd 'bash ./command.sh' \
  --rule 'part1::密码的第一部分是(.+)' \
  --rule 'part2::密码的第二部分是(.+)' \
  --events /tmp/wakewatch-events.jsonl
```

可选参数：

- `--cwd <dir>`：命令执行目录

## 事件格式

每行一个 JSON：

- `start`
- `match`（包含 `rule`、`line`、`groups`）
- `exit`

示例：

```json
{"ts":"2026-03-07T20:00:00+00:00","type":"start","cmd":"bash ./command.sh"}
{"ts":"2026-03-07T20:00:01+00:00","type":"match","rule":"part1","line":"密码的第一部分是23chn4","groups":["23chn4"]}
{"ts":"2026-03-07T20:00:31+00:00","type":"match","rule":"part2","line":"密码的第二部分是hic0307","groups":["hic0307"]}
{"ts":"2026-03-07T20:00:31+00:00","type":"exit","exitCode":0}
```

## 下一步（可选）

如果要直接“唤醒主会话”，可以再加一个小桥接器：

- tail `events.jsonl`
- 读到 `match` 就调用 `sessions_send`
- 从而在任务中途主动发消息（而不是等命令全部结束）
