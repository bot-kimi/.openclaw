# TPU Onboarding Notebook (Living Doc)

> Purpose: 作为组内 TPU/GCP 基础设施的“活文档”。
> 维护原则：删重复、补新增、保持可检索。
> Last updated: 2026-03-07 UTC

## 0) One-screen checklist（上机前 60 秒）

1. 确认 VM 区域（region/zone）
2. 只使用同 region 的 bucket / 大数据盘
3. 检查身份：`gcloud auth list` + `echo $GOOGLE_APPLICATION_CREDENTIALS`
4. 长任务进 `tmux`/`screen`
5. spot 任务准备好被抢占（可恢复）

---

## 1) 资源与开发模式

- 组内研发栈：**TPU + JAX**
- `on-demand`：持久，适合开发/调试
- `spot`：可被 GCP 随时回收，适合训练
- 新人建议：优先拿 `v4-8` 作为 dev VM

### TPU 管理命令（via `kimi_tpu.sh`）

- 查看可申请规格：`./kimi_tpu.sh available`
- 申请：`./kimi_tpu.sh create <name> --zone=<zone> --accelerator-type=<type>`
- 列表：`./kimi_tpu.sh list`
- SSH：`./kimi_tpu.sh ssh <vm-name> --zone <zone>`
- 删除：`./kimi_tpu.sh delete <vm-name> --zone <zone>`

---

## 2) 成本与合规红线（最重要）

- TPU 资源可近似视为免费，但**存储不免费且昂贵**
- **严禁跨 region 读写**（bucket / filestore 都一样）
- 跨区可能导致高额账单（文档中有历史事故）

### 硬约束

- VM 在哪个 region，就只访问同 region 的 bucket（尤其 checkpoint）
- 训练前必查：
  - `gcloud auth list`
  - `echo $GOOGLE_APPLICATION_CREDENTIALS`
- 禁止：
  - 用个人账号（如 @gmail/@mit）跑训练
  - 用跨区 service account 访问 bucket
  - 在脚本里硬编码凭证

### 监控机制

- Compliance Bot 定期巡检（README: 每 5 分钟）
- 身份不合规会直接删 TPU 实例

---

## 3) Storage 策略

### GS Bucket

- checkpoint 优先放 bucket（比 SSD 便宜）
- 但**跨 region 读写 bucket 代价非常大**
- 每个 region 对应自己的 bucket + service account

### Filestore / NFS

- 类似本地盘，但价格高
- 跨区读取大数据又贵又慢
- `/kmh-nfs-ssd-us-mount` 在 us-central2 侧，适合同区场景（如 v4）

---

## 4) 开发环境与任务习惯

- conda/miniforge 已有共享安装
- 不要改 `base`，需要时建自己的 env
- 长任务用 `tmux`/`screen`
- spot VM 的包/环境可丢失，预期内

---

## 5) 常见问题

### TPU backend 初始化失败（可能 TPU 被占用）

- 先查是否有人在跑：
  - `./kimi_tpu.sh ssh <vm> --zone <zone> --command "ps -ef | grep python | grep -v grep"`
- 若无人占用但状态异常，可清理临时 TPU 痕迹（按 README 操作）

### 磁盘满（No space left）

- 查占用：`ncdu /`
- 查已删未释放：`lsof +L1`
- 必要时重启日志相关服务释放句柄

---

## 6) 代码与仓库习惯（本地补充）

- 组内私有仓库默认用 **SSH clone**：`git@github.com:owner/repo.git`
- 不默认使用 HTTPS（避免凭证交互问题）

---

## 7) 待补充（随着 onboarding 更新）

- [ ] 各 region 常用 VM 命名规范
- [ ] 各 region SA key 获取与安全保管流程
- [ ] 组内常用训练脚本模板（JAX）
- [ ] spot 中断恢复 best practices
- [ ] 故障升级路径（找谁 + 怎么报）
