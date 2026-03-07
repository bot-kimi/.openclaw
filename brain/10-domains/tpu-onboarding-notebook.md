# TPU Onboarding Notebook (Living Doc)

> Purpose: 作为组内 TPU/GCP 基础设施的“活文档”。
> 维护原则：删重复、补新增、保持可检索。
> Last updated: 2026-03-07 UTC

## One-screen checklist（上机前 60 秒）

1. 确认 VM 区域（region/zone）
2. 只使用同 region 的 bucket / 大数据盘
3. 检查身份：`gcloud auth list` + `echo $GOOGLE_APPLICATION_CREDENTIALS`
4. 长任务进 `tmux`/`screen`
5. spot 任务准备好被抢占（可恢复）

---

## 1) General Practice

### 团队默认开发范式

- 研发栈：**TPU + JAX**
- 新人建议：优先拿 `on-demand v4-8` 作为 dev VM
- 训练任务常用 `spot`（必须接受可被回收）

### 合规与安全习惯

- 训练前必查：
  - `gcloud auth list`
  - `echo $GOOGLE_APPLICATION_CREDENTIALS`
- 禁止：
  - 用个人账号（@gmail/@mit）跑训练
  - 用跨区 service account 访问 bucket
  - 在脚本中硬编码凭证
- Compliance Bot 会巡检，不合规可能直接删 TPU

### 工程习惯

- 长任务统一进 `tmux`/`screen`
- 环境建议：conda/miniforge，自建 env，不改 `base`
- 组内私有仓库默认 **SSH clone**：`git@github.com:owner/repo.git`

---

## 2) Compute (TPUs)

### 资源形态

- `on-demand`：持久，适合开发/调试
- `spot`：可被 GCP 随时回收，适合训练

### TPU VM 管理（`kimi_tpu.sh`）

- 查看可申请规格：`./kimi_tpu.sh available`
- 申请：`./kimi_tpu.sh create <name> --zone=<zone> --accelerator-type=<type>`
- 列表：`./kimi_tpu.sh list`
- 连接：`./kimi_tpu.sh ssh <vm-name> --zone <zone>`
- 删除：`./kimi_tpu.sh delete <vm-name> --zone <zone>`

### 常见 TPU 故障

- `Unable to initialize backend 'tpu'` 等：
  1) 先查是否有人在跑：
     - `./kimi_tpu.sh ssh <vm> --zone <zone> --command "ps -ef | grep python | grep -v grep"`
  2) 若无人占用但异常：按 README 清理 `/tmp/*tpu*`

---

## 3) Storage

### 成本红线

- TPU 可近似视为免费，但**存储昂贵**
- **严禁跨 region 读写**（bucket / filestore 都一样）

### GS Bucket

- checkpoint 优先放 bucket（通常比 SSD 便宜）
- 但跨区 bucket I/O 代价高
- 原则：VM 在哪个 region，就访问同 region bucket

### Filestore / NFS

- 类似本地盘，但费用高
- 跨区读大数据又贵又慢
- `/kmh-nfs-ssd-us-mount` 在 us-central2，适合同区场景（如 v4）

### 磁盘空间问题

- `No space left` 排查：
  - `ncdu /`
  - `lsof +L1`
- 必要时重启日志相关服务释放句柄

---

## 4) Other

### 已知高优先规则（来自 onboarding）

- 私有/组内 GitHub repo 优先 SSH clone，不默认 HTTPS
- spot 被回收后要及时清理无效 VM 记录
- dev VM 避免重启（共享环境，可能影响他人任务）

### 待补充

- [ ] 各 region VM 命名规范
- [ ] 各 region SA key 申请与保管流程
- [ ] 组内常用 JAX 训练模板
- [ ] spot 中断恢复 SOP
- [ ] 故障升级路径（找谁 + 怎么报）
