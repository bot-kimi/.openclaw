# WakeWatch (MVP+)

一个最小可用的“事件驱动唤醒”工具原型：

- 执行长命令
- 实时读取 stdout/stderr
- 命中正则规则时写入事件（JSONL）
- 写入 start/exit 事件
- 可选执行 hook 命令（on-start / on-match / on-exit）

> 依赖：Python 3 标准库，无第三方包。

## 基础用法

```bash
python3 tools/wakewatch.py \
  --cmd 'bash ./command.sh' \
  --rule 'part1::密码的第一部分是(.+)' \
  --rule 'part2::密码的第二部分是(.+)' \
  --events /tmp/wakewatch-events.jsonl
```

可选参数：

- `--cwd <dir>`：命令执行目录

## Hook 用法（关键）

可以在事件触发时执行 shell 命令：

```bash
python3 tools/wakewatch.py \
  --cmd 'bash ./command.sh' \
  --rule 'part1::密码的第一部分是(.+)' \
  --rule 'part2::密码的第二部分是(.+)' \
  --events /tmp/wakewatch-events.jsonl \
  --on-start-cmd "echo START >> /tmp/wakewatch-notify.log" \
  --on-match-cmd "echo MATCH:$rule:$group1 >> /tmp/wakewatch-notify.log" \
  --on-exit-cmd "echo EXIT:$exitCode >> /tmp/wakewatch-notify.log"
```

### 模板变量

- 通用：`$type` `$ts`
- match：`$rule` `$source` `$line` `$group1 ... $group5`
- exit：`$exitCode`

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

## 下一步（接 OpenClaw 唤醒）

当前 hook 已经能接“桥接命令”。接下来可以把 `--on-match-cmd` 指向一个 OpenClaw 消息发送器（或 session 通知器），实现：

1. 第一段输出命中就立即推送
2. 第二段输出命中再推送
3. exit 再推送状态

这就是你要的“沉睡中被事件唤醒”。
