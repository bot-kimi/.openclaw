---
id: mem-20260305-inbox
title: Inbox Capture
level: inbox
priority: P1
status: active
tags: [capture, inbox]
source: system
created_at: 2026-03-05T01:48:00Z
updated_at: 2026-03-05T01:48:00Z
related: []
---

# Inbox Capture

Append quick notes here or as separate timestamped files.

## Entries
- [2026-03-05T01:48:00Z] Initialized hierarchical memory skeleton.
- [2026-03-05T02:02:21Z] Implemented quick capture entrypoint for hierarchical memory. (P1) -> entries/2026-03-05-20260305T020221Z.md
- [2026-03-05T02:22:58Z] skill化完成，需要后续加cron (P1) -> entries/2026-03-05-20260305T022258Z.md
- [2026-03-05T03:01:42Z] User requested daily Notion report after consolidation and granted Kimi a free-form living notebook page in Jasmine's home. (P1) -> entries/2026-03-05-20260305T030142Z.md
- [2026-03-05T04:00:49Z] [2026-03-05] 用户确认：skill 已通过；需要记录本次学到的内容与经验。 (P1) -> entries/2026-03-05-20260305T040049Z.md
- [2026-03-05T04:06:22Z] 你记一下，之后每次git提交的时候都push，这样是好习惯 (P1) -> entries/2026-03-05-20260305T040622Z.md
- [2026-03-05T16:46:20Z] 你记住你之后daily report提交到notion上面的东西要用中文 (P1) -> entries/2026-03-05-20260305T164620Z.md
- [2026-03-07T22:22:11Z] 新增能力1：WakeBridge（tools/wakebridge.py + tools/runlong.sh）。用途：长命令开始/结束（含失败）自动唤醒并回报；场景：webchat 会话下的后台任务通知。约定：长时间命令优先走 runlong.sh。 (P1) -> entries/2026-03-07-20260307T222211Z.md
- [2026-03-07T22:22:16Z] 新增能力2：DelayRun（tools/delayrun.sh）。用途：把“X 秒/分钟后执行命令”抽象为一次性调度；机制：创建 one-shot cron，触发 DELAYRUN 事件后执行 cmd64 对应命令并回报结果。示例：30s 后执行 df -h。 (P1) -> entries/2026-03-07-20260307T222216Z.md
- [2026-03-07T22:54:03Z] 用户新偏好：使用 coding skill 写代码时，必须后台启动 coding agent，并通过完成事件唤醒主会话；避免前台阻塞导致聊天卡死。 (P0) -> entries/2026-03-07-20260307T225403Z.md
- [2026-03-07T23:10:21Z] HH老师要求记住：clone 组内/私有 GitHub 仓库时优先使用 SSH（git@github.com:...），不要默认 https。当前环境已有 SSH key。 (P1) -> entries/2026-03-07-20260307T231021Z.md
- [2026-03-07T23:12:59Z] TPU onboarding关键规则：1) 私有仓库用SSH clone；2) TPU+JAX开发，dev优先on-demand v4-8，训练多用spot；3) 严禁跨region读写（bucket/filestore必须同区）；4) 训练前检查gcloud auth与GOOGLE_APPLICATION_CREDENTIALS；5) 禁止个人账号训练/禁止跨区SA/禁止硬编码凭证；6) Compliance Bot每5分钟巡检，不合规会删TPU；7) checkpoint优先GS bucket，Filestore昂贵且跨区慢；8) dev VM不要重启；9) 长任务用tmux；10) spot被抢占后及时清理。 (P0) -> entries/2026-03-07-20260307T231259Z.md
- [2026-03-07T23:30:48Z] HH老师新规：后续记忆相关一律使用高级记忆系统（qmd-memory），不再使用 OpenClaw memory_search 作为主流程。用户说‘记住这个’时，统一走高级记忆 capture/recall。 (P1) -> entries/2026-03-07-20260307T233048Z.md
- [2026-03-07T23:32:39Z] TPU onboarding notebook 已建立：memory/tpu-onboarding-notebook.md。内容含上机前60秒checklist、跨region成本红线、SA合规检查、bucket/filestore同区原则、tmux与spot抢占策略。后续所有TPU基础设施更新先写入该notebook，再做去重精炼。 (P1) -> entries/2026-03-07-20260307T233239Z.md
- [2026-03-07T23:37:24Z] HH老师偏好更新：TPU知识笔记只维护一个版本，避免 memory/ 与 brain/ 双份同步；后续以高级记忆主路径为准，单一来源维护。 (P1) -> entries/2026-03-07-20260307T233724Z.md
- [2026-03-07T23:47:15Z] General practice细则（HH老师）：(1) one experiment, one code dir, one results dir。每次运行前先拷贝完整代码目录，在拷贝目录中启动实验；结果写入独立results/logs目录，确保可复现（随时可追溯到实际运行代码）。(2) 所有实验必须记录到spreadsheet，便于整洁管理、横向对比与回溯。 (P0) -> entries/2026-03-07-20260307T234716Z.md
- [2026-03-07T23:59:27Z] 实验记录主表已确定：Google Sheets 文件ID=1vsic-xRGf6uzWJ58SUGNEE116FnInfAiWKePLj0bA34，名称=general，链接=https://docs.google.com/spreadsheets/d/1vsic-xRGf6uzWJ58SUGNEE116FnInfAiWKePLj0bA34/edit。规则：后续所有实验记录默认同步到该主表；其他实验可创建子sheet/tab。服务账号：zhh-spreadsheet@he-vision-group.iam.gserviceaccount.com（gog可读写）。 (P0) -> entries/2026-03-07-20260307T235927Z.md
- [2026-03-08T00:01:29Z] Spreadsheet约定修正：文件名保持 kimi-worksheet，不改文件名；默认主tab命名为 general，其他实验使用新增tab。 (P1) -> entries/2026-03-08-20260308T000129Z.md
- [2026-03-08T00:04:45Z] Compute硬规则（HH老师）：我当前运行在 dev VM v4-8-1 的一个 tmux window。绝对禁止在该机器上执行重启（reboot）或清理 /tmp（任何形式），否则会导致当前会话/进程中断（我会‘死掉’）。 (P0) -> entries/2026-03-08-20260308T000445Z.md
- [2026-03-08T00:09:42Z] Compute换算基准（HH老师提供）：v4=275 TFLOPs/32GB，v5e=197 TFLOPs/16GB，v5p=459 TFLOPs/95GB，v6e=918 TFLOPs/32GB，A100=312 TFLOPs，H200=1979 TFLOPs。按TFLOPs粗略折算A100当量：v4≈0.88，v5e≈0.63，v5p≈1.47，v6e≈2.94（每单位TPU）。用于快速算力直觉，不作为严格benchmark结论。 (P1) -> entries/2026-03-08-20260308T000942Z.md
- [2026-03-08T00:17:30Z] Compute小知识已确认并记住：1) TPU机器是远程机器，本地操作不影响远程；通过kimi_tpu.sh create/ssh/delete等命令操控远程。2) v5p-64对应8个workers（worker 0..7可并行ssh）。3) 不同worker的root/local目录不共享（在worker0写入/tmp文件，worker1不可见）。4) 当前生存约束：我在dev VM v4-8-1的tmux中，禁止重启v4-8-1与清理/tmp。 (P0) -> entries/2026-03-08-20260308T001730Z.md
- [2026-03-08T00:35:59Z] Storage/Workflow纠正（HH老师）：staging 不是临时垃圾区；它是实验代码快照区。遵循 one experiment, one code directory：每次实验前拷贝完整代码目录到 staging 下新目录并从该目录运行。staging 里保留机器创建以来跑过的代码副本，用于可复现与追溯。 (P0) -> entries/2026-03-08-20260308T003559Z.md
- [2026-03-08T00:38:40Z] Storage/code实践规则（HH老师）：大部分代码应放在共享NFS的 code 目录下（长期保存、远程可访问）；workspace/home 只放临时调试脚本。 (P0) -> entries/2026-03-08-20260308T003840Z.md
- [2026-03-08T18:40:07Z] TPU/compute hard rule: local development default python must be /kmh-nfs-ssd-us-mount/code/hanhong/miniforge3/bin/python; do NOT install packages into this shared python environment casually (treat as protected/shared). (P0) -> entries/2026-03-08-20260308T184007Z.md
- [2026-03-08T19:49:18Z] Workflow correction: for long-running remote setup/tasks, always run in background (WakeBridge style), then check status via reminder/alarm instead of blocking foreground. User suggested pairing background run with a timer to proactively check completion. (P1) -> entries/2026-03-08-20260308T194918Z.md
- [2026-03-08T19:51:04Z] TPU hard rule: remote machines are multi-host; default must use --worker=all for TPU operations/init. Multi-worker TPU must initialize simultaneously across workers, otherwise JAX init may hang/fail. (P0) -> entries/2026-03-08-20260308T195104Z.md
- [2026-03-08T19:58:53Z] HARD RULE: '后台执行' means using WakeBridge script tools/runlong.sh (not plain exec background). For any long-running command, must use tools/runlong.sh to get start/end/failure notifications. (P0) -> entries/2026-03-08-20260308T195853Z.md
