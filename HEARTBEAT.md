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
6) 如果当前存在明确可执行的下一步（尤其是故障排查/重试链路），**禁止只汇报建议**；必须先启动下一步动作（优先后台 + WakeBridge），再同步状态。
7) 对“我停下来了/继续执行”类反馈：立即进入执行态，不要等待额外确认。
8) 任何说“继续盯/稍后检查/我再看一下”的表述，必须先创建后续 alarm（默认 120s）再回复；禁止只口头承诺不设 alarm。
9) 心跳检查后决策规则：若状态确认“稳定且无需下一步动作”，回复格式必须为“无需处理：<原因>”；仅当存在未闭环风险/待确认问题时，才设置下一次 alarm。

## WakeBridge 跨渠道路由规则（新增）

10) 若收到 WakeBridge/系统状态消息（WB_START/WB_DONE/WB_ALARM/Exec completed 等），先判断来源渠道：
   - 若来源是 **discord**：不要只在当前会话口头回复；必须额外调用 `tools/notify_telegram.sh` 向 Telegram 发送一条状态消息（默认目标 `telegram:8204583385`）。
   - 若来源不是 discord（如 telegram 主会话）：按正常主会话直接回复即可。

11) Discord→Telegram 转发消息格式：
   - `【WB转发】<label> | <status> | <简短结论>`
   - 失败时必须带一句错误关键词（如 `ssh 255` / `tpu init failed`）。

12) 若无法判断来源渠道，默认按“非 discord”处理，但在回复中加一句“来源渠道未识别”。
