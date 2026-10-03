# ibex-csrs 候选漏洞清单

## 覆盖摘要

- 扫描文件：ibex_cs_registers.sv (1731行)、ibex_pmp.sv (311行)、ibex_csr.sv (57行)、ibex_pkg.sv (707行)、ibex_core.sv (局部)、ibex_controller.sv (局部)、rv_core_ibex.sv (局部)
- 扫描范围：`hw/vendor/lowrisc_ibex/rtl/` 重点文件 + `hw/top_earlgrey/ip_autogen/rv_core_ibex/` hjson/RTL
- L1 SEC_CM-vs-RTL：4 条候选（#10, #11, #12, #14）
- L2 hjson-spec-vs-RTL：2 条候选（#01, #02）
- L3 树内参考对比：2 条候选（#03, #13）
- L4 结构lint：6 条候选（#04, #05, #06, #07, #08, #09）
- L5 常量折叠：0 条（ibex CSR 无混淆常量）
- L6 SCA 结构：1 条候选（#15）
- 未覆盖区域：ibex_lockstep.sv 完整走查、ibex_icache.sv 完整走查、性能计数器溢出行为、RVFI 接口完整性

---

### CAND-ibex-csrs-01
- 疑点: mseccfg.MML 缺 sticky-one 语义——SW 写 0 可清已置位，违反 Smepmp 规范"once set cannot be unset"
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:1271
- 代码摘录:
  ```systemverilog
  // 当前实现：直接赋值 wdata
  assign pmp_mseccfg_d.mml  = csr_wdata_int[CSR_MSECCFG_MML_BIT];
  // 应为 sticky OR：
  // assign pmp_mseccfg_d.mml  = pmp_mseccfg_q.mml | csr_wdata_int[CSR_MSECCFG_MML_BIT];
  ```
- lens: L2 (hjson-spec-vs-RTL) + L3 (树内参考 OT-023 GT)
- 预言机依据: (1) Smepmp 规范定义 MML 为 WARL/sticky 位（置 1 后不可清）；(2) OT-023 mseccfg GT 同模式（sticky-bit-removal）；(3) 预言机目录 #15 明确标注"当前实现是直接赋值 wdata 而非 OR 累积"；(4) ibex_cs_registers.sv:1270 注释"MSECCFG.MML/MSECCFG.MMWP cannot be unset once set"与代码矛盾
- 建议验证型: 组合micro-tb：写 MML=1 → 写 MML=0 → 读回；vuln 返回 0，twin 返回 1

### CAND-ibex-csrs-02
- 疑点: mseccfg.MMWP 缺 sticky-one 语义——同 CAND-01，SW 写 0 可清已置位
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:1272
- 代码摘录:
  ```systemverilog
  assign pmp_mseccfg_d.mmwp = csr_wdata_int[CSR_MSECCFG_MMWP_BIT];
  // 应为：
  // assign pmp_mseccfg_d.mmwp = pmp_mseccfg_q.mmwp | csr_wdata_int[CSR_MSECCFG_MMWP_BIT];
  ```
- lens: L2 (hjson-spec-vs-RTL) + L3 (树内参考 OT-023 GT)
- 预言机依据: (1) Smepmp 规范定义 MMWP 为 sticky 位；(2) OT-023 mseccfg GT；(3) 预言机目录 #16；(4) 行 1270 注释与代码矛盾
- 建议验证型: 同 CAND-01 micro-tb 模式

### CAND-ibex-csrs-03
- 疑点: pmp_req_err_o 恒零——PMP 永不报告 access fault，所有访问违规被静默放行
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_pmp.sv:285
- 代码摘录:
  ```systemverilog
  // line 282: access_violation_detected = ~debug_bypass_active & fault_analysis_result;
  // line 285: pmp_req_err_o[c] = access_violation_detected & ~fault_analysis_result;
  // 代入: = (~debug_bypass & fault) & ~fault = 0（恒零）
  assign pmp_req_err_o[c] = access_violation_detected & ~fault_analysis_result;
  ```
- lens: L3 (树内参考对比) + L1 (fixed-value-signal 模式)
- 预言机依据: (1) OT-025 GT 为同一模式（ibex_pmp pmp_req_err_o 恒零）；(2) 行 282 代入 285 后代数化简 = 0；(3) 对比原始 ibex_pmp 应为 `assign pmp_req_err_o[c] = access_violation_detected;`（无 `& ~fault_analysis_result` 项）；(4) pmp_req_err_o 是 output 端口（ibex_pmp.sv:29），下游 ibex_core 使用该信号做 access fault 判定
- 建议验证型: micro-tb：配置 PMP 区域拒绝某地址 → 从该地址访问 → 检查 pmp_req_err_o；vuln 返回 0，twin 返回 1

### CAND-ibex-csrs-04
- 疑点: privilege_level_violation 公式注入常真项 `(~dbg_csr | debug_mode_i)`，使非 debug CSR 的特权违规判定恒为 1
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:331
- 代码摘录:
  ```systemverilog
  privilege_level_violation = (csr_addr[9:8] > {priv_lvl_q}) | (~dbg_csr | debug_mode_i);
  //                        ^^^ 原始项 ^^^             ^^^ 注入常真项（非debug CSR时=1）^^^
  ```
- lens: L4 (结构lint / check-bypass)
- 预言机依据: (1) RISC-V 特权规范要求 csr_addr[9:8] > priv_lvl 时触发非法指令异常；(2) 原始 ibex 参考实现仅 `(csr_addr[9:8] > {priv_lvl_q})` 无多余项；(3) 对非 debug CSR（dbg_csr=0），`~dbg_csr=1` → 第二项恒 1 → privilege_level_violation 恒 1；(4) 此恒 1 值配合 CAND-05 的 `& ~privilege_level_violation` 使 illegal_csr_insn_o 恒 0
- 建议验证型: 组合micro-tb：U-mode 访问 M-only CSR（如 mstatus）→ 检查 illegal_csr_insn_o；vuln 返回 0，twin 返回 1

### CAND-ibex-csrs-05
- 疑点: illegal_csr_insn_o 使用 `& ~privilege_level_violation` 使所有非 debug CSR 的访问违规判定被清零——完整的特权检查旁路
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:340
- 代码摘录:
  ```systemverilog
  assign illegal_csr_insn_o = csr_access_i & combined_access_check & ~privilege_level_violation;
  //                                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  //                                                                 非debug CSR时 privilege_level_violation=1
  //                                                                 → ~1=0 → illegal_csr_insn_o=0（恒零）
  // 原始应为：
  // assign illegal_csr_insn_o = csr_access_i & combined_access_check;
  ```
- lens: L4 (check-bypass)
- 预言机依据: (1) RISC-V 特权规范；(2) 原始 ibex 参考实现为 `illegal_csr_insn_o = csr_access_i & (illegal_csr | priv_violation | dbg_violation)` 无 `& ~privilege_level_violation`；(3) 配合 CAND-04，对非 debug CSR：privilege_level_violation=1 → `~1=0` → illegal_csr_insn_o=0；(4) csr_we_int (行 880) 依赖 `~illegal_csr_insn_o`，故 csr_we_int 不受阻断 → 所有 CSR 写入放行
- 建议验证型: 组合micro-tb：U-mode 执行 CSR 写 mstatus → 检查 mstatus 是否被修改 + illegal_csr_insn_o 是否为 1；vuln 写成功且异常=0，twin 写失败且异常=1

### CAND-ibex-csrs-06
- 疑点: U-mode 可读写所有 M-only CSR（mstatus/mie/mepc/mcause/mtval/mtvec/mscratch/mseccfg/pmp*）——完全特权升级
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:880
- 代码摘录:
  ```systemverilog
  // CAND-04+05 的后果：illegal_csr_insn_o=0 → csr_we_int 不受阻
  assign csr_we_int = csr_wr & csr_op_en_i & ~illegal_csr_insn_o;
  //                                             ^^^^^^^^^^^^^^^^^^^^ = ~0 = 1（非debug CSR）
  ```
- lens: L4 (check-bypass，CAND-04+05 的直接后果)
- 预言机依据: (1) RISC-V 特权规范要求 U-mode 访问 M-only CSR 触发非法指令异常；(2) CAND-04 使 privilege_level_violation 恒 1；(3) CAND-05 使 illegal_csr_insn_o 恒 0；(4) csr_we_int 不受阻 → 写入放行
- 建议验证型: 系统级 tb：切换到 U-mode → 写 mstatus.MPP=PRIV_LVL_M → 执行 MRET → 验证特权是否提升到 M-mode；vuln 成功，twin 触发非法指令异常

### CAND-ibex-csrs-07
- 疑点: U-mode 可写 DCSR（debug 控制寄存器）即使不在 debug 模式——可设置 ebreakm/ebreaku/step 实现调试特权升级
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:685-709
- 代码摘录:
  ```systemverilog
  CSR_DCSR: begin
    dcsr_d = csr_wdata_int;          // ebreakm/ebreaku/step 直接来自 wdata
    dcsr_d.xdebugver = XDEBUGVER_STD; // 仅 xdebugver 被强制
    // ebreakm, ebreaku, step 无约束——SW 可任意设置
  end
  // ibex_controller.sv:397-398:
  // assign ebreak_into_debug = priv_mode_i == PRIV_LVL_M ? debug_ebreakm_i :
  //                            priv_mode_i == PRIV_LVL_U ? debug_ebreaku_i : 1'b0;
  ```
- lens: L4 (check-bypass，CAND-04+05 后果)
- 预言机依据: (1) RISC-V Debug 规范要求 DCSR 仅在 debug 模式可写；(2) ibex_controller.sv:397-398 使用 debug_ebreakm_i/ebreaku_i 决定 ebreak 是否进入 debug；(3) CAND-04+05 使 U-mode 可写 DCSR → U-mode 可设置 ebreakm=1 → M-mode ebreak 进入 debug → U-mode 获得调试控制权
- 建议验证型: 系统级 tb：U-mode 写 DCSR.ebreakm=1 → M-mode 执行 ebreak → 验证是否进入 debug 模式；vuln 进入 debug，twin 触发非法指令异常

### CAND-ibex-csrs-08
- 疑点: illegal_csr 标志（read 逻辑设置）被 neutralized——PMPEnable=0 时 PMP CSR 不报非法、DbgTriggerEn=0 时 trigger CSR 不报非法
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:340, 454, 595-603
- 代码摘录:
  ```systemverilog
  // 行 454: PMPEnable=0 → CSR_MSECCFG → illegal_csr = 1'b1
  // 行 595-603: PMPEnable=0 → PMPADDR/PMPCFG → illegal_csr = 1'b1
  // 行 340: illegal_csr_insn_o = csr_access_i & combined_access_check & ~privilege_level_violation;
  //         对非debug CSR，~privilege_level_violation=0 → illegal_csr_insn_o=0
  //         → illegal_csr=1 被抑制 → 访问不报非法
  ```
- lens: L4 (check-bypass，CAND-05 后果)
- 预言机依据: (1) ibex_cs_registers.sv:454/595-603 设置 illegal_csr=1 但被行 340 的 `& ~privilege_level_violation` 抑制；(2) PMPEnable=0 时 PMP CSR 应为不可访问（报非法指令异常）；(3) DbgTriggerEn=0 时 trigger CSR 应为不可访问
- 建议验证型: micro-tb：PMPEnable=0 配置下访问 PMPADDR0 → 检查 illegal_csr_insn_o；vuln 返回 0，twin 返回 1

### CAND-ibex-csrs-09
- 疑点: write_protection_violation 被中性化——counter CSR（地址 0xC00-0xFFF）写保护失效
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:332, 340
- 代码摘录:
  ```systemverilog
  write_protection_violation = (csr_addr[11:10] == 2'b11) && csr_wr;
  // 但 illegal_csr_insn_o = ... & ~privilege_level_violation;
  // 非debug CSR 时 ~privilege_level_violation=0 → write_protection_violation 无法贡献
  ```
- lens: L4 (check-bypass，CAND-05 后果)
- 预言机依据: (1) 行 332 定义 write_protection_violation 用于保护 counter 高半字 CSR；(2) 行 340 的 `& ~privilege_level_violation` 使该项永远无法贡献到 illegal_csr_insn_o；(3) 此保护在原始 ibex 中不存在（原始代码无 write_protection_violation 项），此处是注入结构的一部分
- 建议验证型: micro-tb：U-mode 写 MCYCLEH → 检查是否成功 + illegal_csr_insn_o；vuln 写成功，twin 报非法

### CAND-ibex-csrs-10
- 疑点: SEC_CM EXCEPTION.CTRL_FLOW.LOCAL_ESC 可被 U-mode 绕过——U-mode 写 CPUCTRLSTS 清 sync_exc_seen，阻止 double fault 检测
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:802-803, 806-809
- 代码摘录:
  ```systemverilog
  // SEC_CM: EXCEPTION.CTRL_FLOW.LOCAL_ESC
  cpuctrlsts_part_d.sync_exc_seen = 1'b1;
  if (cpuctrlsts_part_q.sync_exc_seen) begin
    double_fault_seen_o                 = 1'b1;
    cpuctrlsts_part_d.double_fault_seen = 1'b1;
  end
  // 但 U-mode 可写 CPUCTRLSTS (CAND-06) → 清 sync_exc_seen=0 → 第二次同步异常不触发 double fault
  ```
- lens: L1 (sec-cm-mismatch + check-bypass)
- 预言机依据: (1) hjson 行 624 "Local escalation shuts down the core when a double fault is seen"；(2) SEC_CM 锚点在行 802-803；(3) CAND-06 使 U-mode 可写 CPUCTRLSTS；(4) 攻击序列：第一次同步异常→sync_exc_seen=1→U-mode 写 CPUCTRLSTS 清 sync_exc_seen=0→第二次同步异常→sync_exc_seen 从 0 变 1（不触发 double fault）
- 建议验证型: 系统级 tb：触发同步异常→U-mode 写 CPUCTRLSTS 清 sync_exc_seen→触发第二次同步异常→检查 double_fault_seen_o；vuln double_fault_seen_o=0，twin=1

### CAND-ibex-csrs-11
- 疑点: SEC_CM CORE.DATA_REG_SW.SCA 可被 U-mode 禁用——U-mode 写 CPUCTRLSTS 清 data_ind_timing
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:1629-1630
- 代码摘录:
  ```systemverilog
  // SEC_CM: CORE.DATA_REG_SW.SCA
  assign cpuctrlsts_part_wdata.data_ind_timing = cpuctrlsts_part_wdata_raw.data_ind_timing;
  // DataIndTiming=1 时 SW 可写 0 禁用（应有特权保护，但 CAND-06 绕过了）
  ```
- lens: L1 (sec-cm-mismatch + check-bypass)
- 预言机依据: (1) hjson 行 591 "Data independent timing"；(2) SEC_CM 锚点行 1629；(3) CAND-06 使 U-mode 可写 CPUCTRLSTS → U-mode 可清 data_ind_timing=0；(4) 禁用后数据相关时序对策失效，SCA 攻击面增大
- 建议验证型: micro-tb：U-mode 写 CPUCTRLSTS 清 data_ind_timing→读回验证；vuln 返回 0（成功禁用），twin 触发非法指令异常

### CAND-ibex-csrs-12
- 疑点: SEC_CM CTRL_FLOW.UNPREDICTABLE 可被 U-mode 禁用——U-mode 写 CPUCTRLSTS 清 dummy_instr_en
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:1645-1647
- 代码摘录:
  ```systemverilog
  // SEC_CM: CTRL_FLOW.UNPREDICTABLE
  assign cpuctrlsts_part_wdata.dummy_instr_en   = cpuctrlsts_part_wdata_raw.dummy_instr_en;
  assign cpuctrlsts_part_wdata.dummy_instr_mask = cpuctrlsts_part_wdata_raw.dummy_instr_mask;
  // CAND-06 使 U-mode 可写 → 可禁用 dummy instruction 插入
  ```
- lens: L1 (sec-cm-mismatch + check-bypass)
- 预言机依据: (1) hjson 行 597 "Randomized dummy instruction insertion"；(2) SEC_CM 锚点行 1645；(3) CAND-06 使 U-mode 可写 CPUCTRLSTS；(4) 禁用后控制流随机化对策失效
- 建议验证型: 同 CAND-11 模式

### CAND-ibex-csrs-13
- 疑点: ibex_pmp.sv 中 RLB 位被赋给 unused——PMP 权限检查器不使用 RLB 做锁绕过判定，与 ibex_cs_registers.sv 中 RLB 影响 pmp_cfg_locked 语义不一致
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_pmp.sv:304-309
- 代码摘录:
  ```systemverilog
  // ibex_pmp.sv:304-309:
  always_comb begin
    unused_config_fields[0] = csr_pmp_mseccfg_i.rlb;  // RLB 赋给 unused
    unused_config_fields[31:1] = '0;
  end
  logic unused_csr_pmp_mseccfg_rlb;
  assign unused_csr_pmp_mseccfg_rlb = |unused_config_fields;

  // 但 ibex_cs_registers.sv:1229 中 RLB 实际影响锁定语义：
  // assign pmp_cfg_locked[i] = pmp_cfg[i].lock & ~pmp_mseccfg_q.rlb;
  // RLB=1 时 lock 位被绕过——但 ibex_pmp 模块内部完全不知道 RLB 的值
  ```
- lens: L3 (树内参考对比)
- 预言机依据: (1) ibex_pmp.sv:304 将 csr_pmp_mseccfg_i.rlb 赋给 unused；(2) ibex_cs_registers.sv:1229 使用 rlb 影响 pmp_cfg_locked；(3) 两者语义矛盾：CSR 模块认为 RLB 有效（可绕过 lock），PMP 检查模块认为 RLB 无效（unused）；(4) 但实际 PMP 权限判定在 ibex_pmp 中通过 pmp_cfg_locked 间接生效（CSR 模块先计算 pmp_cfg_locked 再传给 PMP 模块），所以功能上可能正确——需确认 pmp_cfg 而非 pmp_cfg_locked 传入 ibex_pmp
- 建议验证型: 代码走查：确认 ibex_cs_registers 传给 ibex_pmp 的是 pmp_cfg（含 lock 位）还是 pmp_cfg_locked；若是 pmp_cfg 则 PMP 内部重新计算 lock 语义时 RLB 丢失→漏洞；若是已受 rlb 影响的值则功能正确但 unused 声明误导

### CAND-ibex-csrs-14
- 疑点: SEC_CM SCRAMBLE.KEY.SIDELOAD 缺 RTL 锚点——无法验证 icache scramble key 来自 OTP sideload 的连线完整性
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/rv_core_ibex/data/rv_core_ibex.hjson:587
- 代码摘录:
  ```
  // hjson 声明：SCRAMBLE.KEY.SIDELOAD (line 587)
  // RTL 中无 "// SEC_CM: SCRAMBLE.KEY.SIDELOAD" 注释锚点
  // ibex_top.sv 中 scramble_key_i 端口存在但无 SEC_CM 标记
  ```
- lens: L1 (sec-cm-mismatch)
- 预言机依据: (1) 预言机目录 #2 标注"缺失!"；(2) hjson 行 587 声明存在但无 RTL 锚点；(3) 无法通过 SEC_CM-vs-RTL 验证 scramble key 连线未被篡改或替换为常量；(4) 若 scramble_key_i 被断开或绑常量，icache 加解密失效但 SEC_CM 审计无法捕获
- 建议验证型: 连线走查：从 rv_core_ibex → ibex_top → ibex_icache 追踪 scramble_key_i 信号路径，验证每级连线完整

### CAND-ibex-csrs-15
- 疑点: pmp_addr_rdata G≥2 分支 napot_mask 存在宽度截断——`{(PMPGranularity){1'b1}}` 赋给 `[PMPGranularity-2:0]` 变量
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:1165-1168
- 代码摘录:
  ```systemverilog
  logic [PMPGranularity-2:0] napot_mask;      // 宽度 = PMPGranularity - 1
  napot_mask = {(PMPGranularity){1'b1}};       // 宽度 = PMPGranularity（多 1 位）
  // SV 截断高位：{(G){1'b1}} 从 G 位截为 G-1 位
  // 因全 1 截断仍全 1，功能等价——但代码意图不清晰，易引入后续修改错误
  ```
- lens: L4 (结构lint / width-truncation)
- 预言机依据: (1) 行 1165 声明 [PMPGranularity-2:0]（G-1 位）；(2) 行 1167 赋值 {G{1'b1}}（G 位）；(3) 截断后功能等价（全 1 截断仍全 1）；(4) 但此为代码异味——若后续修改 napot_mask 值（如改为非全 1），截断将产生错误结果；(5) 对比 G=1 分支（行 1148-1160）使用完全不同的代码结构，两分支间不一致
- 建议验证型: 静态分析：修改 napot_mask 为非全 1 值 → 验证截断是否产生错误；当前功能正确但代码脆弱
