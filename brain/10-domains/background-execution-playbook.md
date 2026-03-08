# 后台执行任务操作笔记（WakeBridge 版）

> 用途：当你说“温习你后台执行的那个笔记”时，我必须按本文执行。
> 优先级：P0（硬约束）
> Last updated: 2026-03-08 UTC

## 核心原则（必须遵守）

1. **“后台执行”唯一合法方式**：`tools/runlong.sh`（WakeBridge）
   - 不是普通 `exec background:true`
2. 长任务必须有 **开始/结束/失败** 通知。
3. 任何时候都不能用前台长任务卡住对话。
4. 收到 `WB_START`/`WB_DONE`/`Exec completed` 等系统状态消息时：
   - 当作任务状态事件汇报；
   - **禁止**回复 `HEARTBEAT_OK`。

---

## 标准流程（每次都按这个）

### Step 0) 开跑前检查 TaskBoard

先确保 TaskBoard 在跑（默认端口 9876）：

```bash
python3 tools/taskboard.py serve --host 0.0.0.0 --port 9876
```

- 如果已在运行就保持不动
- 如果没运行，先启动再继续
- WakeBridge 现在已配置为：TaskBoard 不在线会 fail fast

### Step 1) 用 WakeBridge 启动长任务

```bash
tools/runlong.sh "<你的长命令>" "<label>"
```

示例：

```bash
tools/runlong.sh "sleep 30; echo alarm fired" "alarm-30s-test"
```

### Step 2) 同时设“检查闹钟”（可选但推荐）

目的：主动回看状态，避免漏跟进。

```bash
tools/runlong.sh "sleep 60; echo check long task" "alarm-check-60s"
```

### Step 3) 状态回报规范

- `WB_START`：回“任务已启动（label + 简要命令）”
- `WB_DONE SUCCESS`：回“任务完成（耗时 + 关键输出）”
- `WB_DONE FAILED`：回“任务失败（exit code + tail + 下一步建议）”

---

## 绝对禁止

- 禁止把“后台执行”替换为普通后台命令流程
- 禁止在普通聊天里对系统状态消息回复 `HEARTBEAT_OK`
- 禁止前台等待长任务导致对话阻塞

---

## 标签约定（Tags Convention）

TaskBoard 支持任务标签，用于分类过滤和互斥控制。

### 标签格式

- `vm:<name>` — 任务目标 VM（如 `vm:kimi-tpu-v5p64-auto-2048`）
- `op:<operation>` — 操作类型（如 `op:init`, `op:train`, `op:healthcheck`）
- 自由标签 — 任意字符串（如 `urgent`, `batch-3`）

### 使用方式

- **WakeBridge**：`--tags "vm:myvm,op:init"`
- **tpu_runlong.sh**：自动生成 `vm:<name>,op:init`
- **CLI 查询**：`python3 tools/taskboard.py list --tag vm:myvm`
- **API**：`/api/tasks?tag=vm:myvm`
- **UI**：下拉框按标签过滤

### 互斥规则

`tools/tpu_runlong.sh` 通过 `check-mutex` 实现 VM 级别互斥：

- 同一 VM 同时只允许一个 `op:init` 任务运行
- 不同 VM 可以并行（如 vm:A + vm:B 同时 init 没问题）
- 判定方式：检查是否有 running 任务同时持有所有指定标签

### 清理

```bash
# 标记所有超过 1 小时仍 running 的任务为 failed
python3 tools/taskboard.py cleanup --max-age 3600
```

---

## 自检清单（执行前/后）

执行前：
- [ ] 我是不是在用 `tools/runlong.sh`？
- [ ] TaskBoard 是否可用？
- [ ] 这个任务会不会阻塞当前对话？

执行后：
- [ ] 我是否正确解读了 `WB_START/WB_DONE`？
- [ ] 我是否给了用户清晰状态更新？
- [ ] 我有没有误回 `HEARTBEAT_OK`？

---

## 用户触发短语（记忆钩子）

当用户说：**“温习你后台执行的那个笔记”**

我必须立即：
1) 读取本文件；
2) 用 3 句话复述核心规则；
3) 后续任务严格按本笔记执行。
