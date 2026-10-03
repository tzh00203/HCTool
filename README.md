# logos-lite

Hack@CHES 2026 决赛备战 harness。确定性调度内核 + 对话式 agent 外壳，
内嵌 RTL 猎洞知识库与 blind-scan 实战验证过的 6-lens 盲猎 + vuln-vs-twin 动态验证方法。

## 安装

```bash
cd logos-lite
pip install -e .          # 得到 lt 命令
pytest tests/             # 20+ 用例全绿
```

网关：沿用现有 BigModel 网关，`lt run` 会自动转发
`ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN / ANTHROPIC_MODEL` 等环境变量给每个节点。

## 快速上手

```bash
cd campaigns/ches2026-prep

lt validate                  # 校验 pipeline.yaml DAG
lt validate -f pipeline-mini.yaml
lt run                       # 跑完整 DAG（tmux 会话 lt-<run_id>）
lt run -f pipeline-mini.yaml # 冒烟：lc_ctrl scout→hunter 两节点
lt status                    # 状态总览
lt attach <node>             # 进入某节点窗口观察（fcntl 锁防抢键）
lt log <node>                # 看节点终端日志
lt accept correlator         # checkpoint 节点人工放行
lt seed <node> "补充信息"    # 运行中向节点投递消息（持久队列）
lt retry <node> / lt dismiss <node>
lt resume                    # 中断后续跑（workdir 持久，run 状态可恢复）
lt stop                      # 停止（幂等）
```

## 目录

```
logos-lite/         引擎：2s 轮询状态机、tmux 会话管理、complete.marker 两段式完成、
                checkpoint/seed/retry、claude-only 后端（Stop hook + offline 机器强制）
agents/         8 角色合同（中文四段式 + sidecar：lenses/FORMAT/WORKORDER/EVIDENCE/FIELDS）
knowledge/      12 个 RTL 漏洞模式（含 GT 实例与盲检方法）+ OT 安全笔记 + 规则/方法论
templates/      dyn-verify 模板（tb 组合/时序/DPI + build.sh + exploit.py + stub 库 + 活样板）
campaigns/      ches2026-prep：28 节点完整 DAG + mini 冒烟 + 持久 workdir
```

## ches2026-prep 流水线

```
oracle-scout-<ip> ×12 (offline, 并行)     ← 盘点树内预言机
      ↓
hunter-<ip> ×12 (offline)                 ← 6-lens 盲猎，report-everything
      ↓
correlator  [checkpoint: 人工审 vulns.md]  ← 去重、VULN-ID、预估分排序
      ↓
verify-planner                            ← 写验证工单 + 同步执行子流水线
      └─ (子流水线) dyn-verifier ×N ≤4/批 ← twin+tb+Verilator，exit 1 = confirmed
      ↓
reviewer    [checkpoint: 人工审 review.md] ← Rule 3 / PoC 复跑 / CVSS 校准
      ↓
reporter                                  ← CHES 19 字段提交包 → workdir/submissions/
```

顶层 env：`OT_TREE`（盲扫目标树）、`VERILATOR`（4.210）、`HARNESS`（本目录）。
12 IP：aes, hmac, ascon, entropy_src, keymgr, lc_ctrl, otp_ctrl, rom_ctrl,
uart, ibex-pmp, ibex-csrs, kmac。改 IP 清单编辑 `scripts/gen_nodes.py` 再生成。

## 关键设计

- **Rule 3 机器强制**：hunter/oracle-scout 节点 `offline: true`，
  claude settings 直接 deny WebSearch/WebFetch
- **证据分级**（agents/dyn-verifier/EVIDENCE.md）：L1 执行级仿真 > L2 组合 micro-tb
  > L3 脚本级 > L4 静态；动态证据压静态结论，置信度只降不升
- **falsification 值钱**：`[poc-fail]`（vuln 与 twin 行为一致）如实记录，
  防误报进提交流
- **report-everything**：候选不设严重度门槛（Phase 1 实测 found 67% 只交了 48%）
- **workdir 跨 run 持久**：oracle-inventory/ findings/ artifacts/ poc/ submissions/
  沉淀资产；runs/<run_id>/ 只是单次执行现场
