# Vuln-vs-Twin 动态验证方法论

## 核心思想

复制被测模块为 `*_twin.sv`，**只修复漏洞行**（修复依据=树内预言机：文件自身
注释/SVA、hjson 文档、兄弟模块模式、RISC-V 规范），同一 tb 同时实例化
vuln 和 twin，同一激励差分比对。

**不依赖上游 diff，Rule 3 合规。**

## 保真度分级（证据等级，动态压静态，置信度只降不升）

| 级别 | 手段 | 适用 |
|---|---|---|
| L1 执行级实证 | Verilator 全模块 vuln-vs-twin 仿真 | FSM/数据通路洞 |
| L2 数据流实证 | 组合逻辑 micro-tb（表达式级） | 门控极性/截断类 |
| L3 脚本级实证 | Python 常量折叠/概率脚本 | 混淆常量、ECC 概率 |
| L4 静态结论 | 纯预言机对照，未动态验证 | 兜底，报告必须标注 |

## tb 三型

1. **组合 micro-tb**（hmac_wipe_gate 模式）：把疑点表达式抄进 tb 直接算，
   vuln/twin 各一个 assign。10 分钟建好，适合 L2。
2. **negedge-FSM 时序 tb**（entropy_markov/aes_core 模式）：tb 内 FSM 驱激励
   （Verilator 4.210 每个 initial 只允许一个时序控制），XMR 探内部信号，
   输出 verdict 信号。适合 L1。
3. **DPI 差分 tb**（ascon 模式）：DPI-C 调树内 vendored C 参考，
   多配置矩阵（算法变体 × ENC/DEC × 边界长度）。适合密码功能洞。

## 10 个已验证案例索引（模式→案例）

| 案例目录 | 型 | 验证内容 |
|---|---|---|
| dyn_verify/hmac_wipe_gate | 组合 | OT-008 wipe gate 极性 |
| dyn_verify/entropy_markov | 时序 | markov HT fail-dead（negedge 采样） |
| dyn_verify/aes_core | 时序 | SEC_WIPE F1/F2（PRD vs 0/明文） |
| dyn_verify/aes_data_out_reset | 组合 | F3 复位门控（FI 场景） |
| dyn_verify/aes_ctr | 时序 | 错误告警 100 拍延迟 + SVA 违规计数 |
| dyn_verify/aes_force_masks | 时序 | FORCE_MASKS 机制再定性 |
| dyn_verify/ascon | DPI | 128a 双分支吸收洞，6 配置矩阵 |
| dyn_verify/ascon_core | 时序 | escalate-ignored + WIPE-noop |
| dyn_verify/ibex_pmp | 时序+随机 | 判定矩阵 8 项 + 3000 随机 + XMR 窗口探针 |
| rom_ctrl ECC (Python) | 脚本 | chk_bits=0 概率 1/128（10000 试验 78 命中） |

## 工单要素（verify-planner 填）

- tb 类型（三选一）+ 保真度目标级别
- 依赖文件清单（DUT 叶子 + prim 链 + stub 列表）
- 激励序列（FSM 状态列表或矩阵枚举）
- 成功判据（机器可查：exit code / verdict 信号 / 差分输出）
- 失败判据与排查（编译失败→检查文件顺序/VERILATOR_ROOT；
  结果不反→检查激励是否真踩中路径）

## 产出规范

每个 PoC 目录自包含：`tb_*.sv` + `{module}_twin.sv` + `*_stub.sv` +
`build_*.sh` + `exploit.py`（redbud 模式：find_verilator()/tempdir/--repo，
评委 VM 可直接跑）。**exit 1 = finding confirmed**。
