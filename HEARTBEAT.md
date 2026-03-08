# HEARTBEAT.md

## Heartbeat Guardrails (must follow)

1) 只有在**真实 heartbeat poll**时才回复 `HEARTBEAT_OK`。
2) 若消息是工具状态/系统日志（例如 `WB_START` / `WB_DONE` / `Exec completed` / runlong 通知），**禁止**回复 `HEARTBEAT_OK`。
3) 对于 runlong/WakeBridge 通知：
   - 把它当作任务状态事件；
   - 正常向用户汇报“已开始/已完成/失败”；
   - 不触发 heartbeat 流程。
4) 判断优先级：
   - 先判断是否为 runlong/系统状态消息；若是，按第3条处理；
   - 只有明确是 heartbeat poll，才走 heartbeat 逻辑。
5) 若无法确定是否 heartbeat poll：默认**不**回复 `HEARTBEAT_OK`，改为简短状态说明并等待用户确认。
