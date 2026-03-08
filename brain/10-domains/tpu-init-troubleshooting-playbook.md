# TPU Initialization 排障流程（实战版）

Last updated: 2026-03-08 UTC

## 目标
把 `jax.devices()` 从失败推进到成功，且过程可复用。

## 硬规则
1. 长任务必须走 `tools/runlong.sh`（WakeBridge），不能前台卡住。
2. 远程 TPU 默认按 **multi-host** 处理，命令必须带 `--worker=all`。
3. 同一张卡同一时刻只允许一个 `jax.devices()` 初始化进程（避免互斥冲突）。
4. TPU 长任务统一走 `tools/tpu_runlong.sh`（自带“已有 TPU 运行任务则阻塞”保护）。
5. 每轮结束后检查并清理 TaskBoard 的 stale running 条目，保持面板与真实进程一致。
4. 发现卡被 preempted/连接层异常时，优先 `delete + reapply`，不要死磕旧卡。

## 常见错误信号与含义

### A) `TPU backend initialization is taking more than 60.0 seconds`
- 含义：异常信号，不是根因。
- 动作：立刻继续查真实错误（不能停在这句）。

### B) `Unable to initialize backend 'tpu': ... Device or resource busy`
- 含义：设备被占用（可能是别人的，也可能是自己并发残留）。
- 动作：
  - `sudo lsof /dev/accel*` 或 `sudo lsof /dev/vfio/*` 查占用
  - 别人占用：按流程 ignore/delete mapping，不要随便 kill
  - 自己残留：清理自身残留进程，再重试

### C) `FAILED_PRECONDITION ... worker has joined the slice`
- 含义：all-worker 里有 worker 没 join 成功（同步/连接层问题）。
- 动作：
  - 先跑 `--worker=all` 的 health check（hostname/whoami/python）
  - 再做 all-worker init
  - 若仍失败，通常换卡更快（delete + reapply）

### D) `ssh return code [255]`
- 含义：连接层问题（worker 不可达、链路中断、节点异常）
- 动作：
  - 先 all-worker 健康检查
  - 必要时直接 delete + reapply

### E) `ModuleNotFoundError: No module named 'jax'`
- 含义：远端该环境未装 jax
- 动作：
  - `python3 -m pip install --user "jax[tpu]==0.4.37" jaxlib -f https://storage.googleapis.com/jax-releases/libtpu_releases.html`

### F) `/tmp` 相关噪音/问题（如 tpu_logs 权限或空间）
- 动作：
  - `sudo rm -rf /tmp/*tpu* /tmp/tpu_logs/*`
  - 必要时先看 `df -h /tmp`

## 推荐执行模板（后台）

```bash
tools/runlong.sh "./wiki_tpu/kimi_tpu.sh ssh <vm-name> --worker=all --command 'python3 -m pip install --user \"jax[tpu]==0.4.37\" jaxlib -f https://storage.googleapis.com/jax-releases/libtpu_releases.html && sudo rm -rf /tmp/*tpu* /tmp/tpu_logs/* 2>/dev/null || true && timeout 240s python3 -c \"import jax; print(jax.__version__); print(jax.devices())\"'" "tpu-<type>-init"
```

## 本次实战结论（2026-03-08）
- 旧卡多次出现 worker join / ssh 255 等连接层问题，继续重试收益低。
- 采用 delete + reapply 后，在新卡 `kimi-tpu-v5p64-auto-2048` 上成功跑通。
- 成功标志：`WB_DONE ... status=SUCCESS exit=0` 且 `jax.devices()` 输出完整 TPU device 列表。
