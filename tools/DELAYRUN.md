# DelayRun

把“X 秒后执行某条命令”抽象成一个可复用工具。

## 创建一次性延时任务

```bash
tools/delayrun.sh --after 30s --cmd 'df -h' --label 'disk-check'
```

参数：
- `--after`：延时（例如 `30s` / `5m`）
- `--cmd`：到点要执行的命令
- `--label`：可选标签（默认 `delayrun`）

它会创建一次性 cron，触发时发系统事件：

```text
DELAYRUN label=<label> cmd64=<base64(command)>
```

## 触发后的处理约定

当收到 `DELAYRUN ...` 系统事件时：
1. 解码 `cmd64`
2. 执行命令
3. 回用户结果摘要（成功/失败 + 关键输出）

## 例子

- 30 秒后跑磁盘检查：
  `tools/delayrun.sh --after 30s --cmd 'df -h' --label 'disk-check'`
- 5 分钟后跑同步：
  `tools/delayrun.sh --after 5m --cmd 'bash ./sync.sh' --label 'sync'`
