# ibex-csrs 盲预言机目录

## 元信息
- 树: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
- 扫描范围: hw/vendor/lowrisc_ibex/rtl（重点 ibex_cs_registers.sv, ibex_pmp.sv, ibex_csr.sv, ibex_pkg.sv）+ hw/top_earlgrey/ip_autogen/rv_core_ibex/data/*.hjson
- SEC_CM 声明数: 12 / SVA 数: 1 / testplan 条目数: 12

## 一、SEC_CM 声明 ↔ RTL 锚点

| # | SEC_CM 声明 (hjson:line) | RTL 锚点 (file:line) | 检验要点 |
|---|---|---|---|
| 1 | BUS.INTEGRITY (rv_core_ibex.hjson:584) | ibex_if_stage.sv:224, ibex_load_store_unit.sv:334 | 总线响应必须带 integrity metadata；ibex 本体不生成 SEC_CM 注释，由 top-level wrapper 加 |
| 2 | SCRAMBLE.KEY.SIDELOAD (rv_core_ibex.hjson:587) | 缺失! | 密钥从 OTP sideload，ibex RTL 内无显式锚点；检验 ibex_top.sv 中 scramble_key_i 端口到 icache 的连线 |
| 3 | CORE.DATA_REG_SW.SCA (rv_core_ibex.hjson:590) | ibex_cs_registers.sv:1629 // SEC_CM: CORE.DATA_REG_SW.SCA | DataIndTiming=1 时 cpuctrlsts_part_wdata.data_ind_timing 必须来自 wdata_raw 而非常数；DataIndTiming=0 时必须绑 1'b0 |
| 4 | PC.CTRL_FLOW.CONSISTENCY (rv_core_ibex.hjson:593) | ibex_if_stage.sv:537 // SEC_CM: PC.CTRL_FLOW.CONSISTENCY | PC 增量检查逻辑必须使 PC 跳变时触发 alert |
| 5 | CTRL_FLOW.UNPREDICTABLE (rv_core_ibex.hjson:596) | ibex_cs_registers.sv:1645 // SEC_CM: CTRL_FLOW.UNPREDICTABLE | DummyInstructions=1 时 cpuctrlsts_part_wdata.dummy_instr_en/mask 必须可写；=0 时必须绑常量零 |
| 6 | DATA_REG_SW.INTEGRITY (rv_core_ibex.hjson:599) | ibex_core.sv:896 // SEC_CM: DATA_REG_SW.INTEGRITY | 寄存器堆 ECC 生成/检查必须在 regfile 实例中生效 |
| 7 | DATA_REG_SW.GLITCH_DETECT (rv_core_ibex.hjson:606) | ibex_register_file_ff.sv:61 // SEC_CM: DATA_REG_SW.GLITCH_DETECT | we 信号 one-hot0 检测必须触发 alert |
| 8 | LOGIC.SHADOW (rv_core_ibex.hjson:613) | ibex_lockstep.sv:10 // SEC_CM: LOGIC.SHADOW | lockstep 比较器必须逐周期比对两核输出 |
| 9 | FETCH.CTRL.LC_GATED (rv_core_ibex.hjson:619) | ibex_core.sv:164 // SEC_CM: FETCH.CTRL.LC_GATED | fetch_enable_i 为 Off 时必须门控取指请求 |
| 10 | EXCEPTION.CTRL_FLOW.LOCAL_ESC (rv_core_ibex.hjson:622) | ibex_cs_registers.sv:802,803,828,829 // SEC_CM: EXCEPTION.CTRL_FLOW.LOCAL_ESC | 连续同步异常（sync_exc_seen 已置 1 时再发生同步异常）必须置 double_fault_seen_o=1 并停核 |
| 11 | EXCEPTION.CTRL_FLOW.GLOBAL_ESC (rv_core_ibex.hjson:628) | ibex_cs_registers.sv:802,803,828,829 // SEC_CM: EXCEPTION.CTRL_FLOW.GLOBAL_ESC | double_fault_seen_o=1 必须向上层 fatal alert 传播 |
| 12 | ICACHE.MEM.SCRAMBLE (rv_core_ibex.hjson:634) | ibex_top.sv:532 // SEC_CM: ICACHE.MEM.SCRAMBLE | icache 数据必须用 scramble key 加解密 |
| 13 | ICACHE.MEM.INTEGRITY (rv_core_ibex.hjson:637) | ibex_icache.sv:280,405 // SEC_CM: ICACHE.MEM.INTEGRITY | icache tag/data 必须带 ECC |

## 二、行为性描述句（hjson 原文 → 检验点）

| # | hjson 原文 (file:line) | 检验点 |
|---|---|---|
| 1 | "Data independent timing." (rv_core_ibex.hjson:591) | CORE.DATA_REG_SW.SCA：DataIndTiming=1 时 data_ind_timing_o 可被 SW 写 1 开启；=0 时该输出恒 0 (ibex_cs_registers.sv:1638) |
| 2 | "Randomized dummy instruction insertion." (rv_core_ibex.hjson:597) | CTRL_FLOW.UNPREDICTABLE：DummyInstructions=1 时 dummy_instr_en_o/mask_o 可写且 seed 可通过 CSR_SECURESEED 注入 (ibex_cs_registers.sv:1646-1651)；=0 时全部恒 0 (ibex_cs_registers.sv:1661-1664) |
| 3 | "Register file integrity checking." (rv_core_ibex.hjson:601) | DATA_REG_SW.INTEGRITY：regfile ECC 错误必须传播到 alert_major_internal_o |
| 4 | "A mechanism to detect and act on double faults. Local escalation shuts down the core when a double fault is seen." (rv_core_ibex.hjson:624) | 连续同步异常→double_fault_seen_o=1→local 停核 (ibex_cs_registers.sv:807-809) |
| 5 | "A mechanism to detect and act on double faults. Global escalation sends a fatal alert when a double fault is seen." (rv_core_ibex.hjson:630) | double_fault_seen_o=1→fatal_hw_err alert 上报 (ibex_core.sv:118-119) |
| 6 | "Fetch enable so core execution can be halted." (rv_core_ibex.hjson:620) | FETCH.CTRL.LC_GATED：fetch_enable_i=Off 时 instr_req_o 必须为 0 (ibex_core.sv:529) |
| 7 | "Shadow core run in lockstep to crosscheck CPU behaviour." (rv_core_ibex.hjson:614) | LOGIC.SHADOW：lockstep 比较器两路输出不一致→alert (ibex_lockstep.sv:10) |

## 三、SVA 清单（行为合同）

| # | 断言 (file:line) | 内容摘要 | 约束的预期行为 |
|---|---|---|---|
| 1 | PMPAddrRstLowBitsZero_A (ibex_cs_registers.sv:1262) | `ASSERT_INIT：PMPRstAddr[i] 的低位 [33-PMPAddrWidth:0] 必须全零 | PMP 地址复位值必须对齐到 granularity 边界；违反则 NAPOT 编码语义错 |
| 2 | IbexCsrOpEnRequiresAccess (ibex_cs_registers.sv:1728) | csr_op_en_i |-> csr_access_i | 操作使能隐含访问有效；若 csr_op_en_i=1 而 csr_access_i=0 则断言失败 |
| 3 | IbexCSREnValid (ibex_csr.sv:55) | `ASSERT_KNOWN：wr_en_i 不为 X/Z | CSR 写使能信号必须已知值，否则可能写入 X 态 |

## 四、关键 CSR 行为预言机（ibex_cs_registers.sv 特有）

| # | 行为 | 锚点 (file:line) | 检验要点 |
|---|---|---|---|
| 1 | **dcsr.ebreakm/ebreaku 输出直连** | ibex_cs_registers.sv:893-894 | debug_ebreakm_o = dcsr_q.ebreakm, debug_ebreaku_o = dcsr_q.ebreaku；任何修改 dcsr_d 的路径必须保留这两个字段的 SW 可写性（CSR_DCSR 写路径 685-710 不强制 ebreakm/ebreaku 为常数） |
| 2 | **dcsr.xdebugver 硬连线** | ibex_cs_registers.sv:687 | 写 DCSR 时 dcsr_d.xdebugver 强制 = XDEBUGVER_STD (4'd4)；读回必须返回 4'd4 |
| 3 | **dcsr.cause 只读** | ibex_cs_registers.sv:694 | 写 DCSR 时 dcsr_d.cause = dcsr_q.cause（忽略 wdata）；只有 debug_csr_save_i 路径可写 cause (ibex_cs_registers.sv:780) |
| 4 | **dcsr.stepie 硬连线零** | ibex_cs_registers.sv:697 | 单步模式中断始终禁用：dcsr_d.stepie = 1'b0 |
| 5 | **dcsr.nmip 硬连线零** | ibex_cs_registers.sv:700 | dcsr_d.nmip = 1'b0（NMI pending 位不可 SW 写） |
| 6 | **dcsr.mprven 硬连线零** | ibex_cs_registers.sv:701 | MPRV 使能在 debug 不支持：dcsr_d.mprven = 1'b0 |
| 7 | **dcsr.stopcount/stoptime 硬连线零** | ibex_cs_registers.sv:702-703 | debug 模式下计数器/计时器不停止 |
| 8 | **dcsr.prv 合法值钳位** | ibex_cs_registers.sv:689-691 | 写入非 M/U 的 prv 值→钳位为 PRIV_LVL_U |
| 9 | **mstatus.mpp 合法值钳位** | ibex_cs_registers.sv:663-665 | 写入非 M/U 的 mpp 值→钳位为 PRIV_LVL_U |
| 10 | **debug CSR 非调试模式访问违法** | ibex_cs_registers.sv:330 | dbg_csr=1 且 debug_mode_i=0 → debug_access_violation=1 → illegal_csr_insn_o=1 |
| 11 | **非 M 模式访问 M-only CSR 违法** | ibex_cs_registers.sv:331 | csr_addr[9:8] > priv_lvl_q → privilege_level_violation=1 |
| 12 | **csr_we_int 门控** | ibex_cs_registers.sv:880 | csr_we_int = csr_wr & csr_op_en_i & ~illegal_csr_insn_o；非法 CSR 写必须被此门控阻断 |
| 13 | **PMP CSR 无 PMPEnable 时非法** | ibex_cs_registers.sv:595-603 | PMPEnable=0 时 PMPCFG*/PMPADDR* 全部标记 illegal_csr=1 |
| 14 | **MSECCFG 无 PMPEnable 时非法** | ibex_cs_registers.sv:454,462 | PMPEnable=0 时 CSR_MSECCFG/MSECCFGH → illegal_csr=1 |
| 15 | **mseccfg.mml 粘性（不可清除）** | ibex_cs_registers.sv:1271 | pmp_mseccfg_d.mml = csr_wdata_int[CSR_MSECCFG_MML_BIT]：注意——当前实现是**直接赋值 wdata**而非 OR 累积，SW 写 0 可清 mml！对比 RISC-V Smepmp 规范要求 mml 一旦置 1 不可清 |
| 16 | **mseccfg.mmwp 粘性（不可清除）** | ibex_cs_registers.sv:1272 | pmp_mseccfg_d.mmwp = csr_wdata_int[CSR_MSECCFG_MMWP_BIT]：同上——直接赋值而非 OR 累积，SW 写 0 可清 mmwp！对比 Smepmp 规范要求不可清 |
| 17 | **mseccfg.rlb 在 any_pmp_entry_locked 时强制 0** | ibex_cs_registers.sv:1281 | any_pmp_entry_locked=1 → pmp_mseccfg_d.rlb=0；锁定 PMP 条目时 RLB 不可再置 1 |
| 18 | **pmp_cfg_locked 语义** | ibex_cs_registers.sv:1229 | pmp_cfg_locked[i] = pmp_cfg[i].lock & ~pmp_mseccfg_q.rlb；lock 位在 RLB=1 时被绕过 |
| 19 | **pmp_cfg_wr_suppress 语义** | ibex_cs_registers.sv:1233-1235 | MML=1 且 RLB=0 且 wdata 是 M-exec 配置→禁止该写入；防止 MML 下新增允许 M 模式执行的条目 |
| 20 | **pmp_cfg write 门控** | ibex_cs_registers.sv:1189-1192 | pmp_cfg_we[i] = csr_we_int & ~pmp_cfg_locked[i] & ~pmp_cfg_wr_suppress[i] & addr_match；三重条件必须同时满足 |
| 21 | **pmp_addr write 门控（含 TOR 锁定）** | ibex_cs_registers.sv:1241-1247 | 下一个区域 TOR 锁定时地址也不可写：~pmp_cfg_locked[i+1] | (pmp_cfg[i+1].mode != PMP_MODE_TOR) |
| 22 | **W=1,R=0 保留组合在 MML=0 时强制 W=0** | ibex_cs_registers.sv:1210-1211 | pmp_mseccfg_q.mml=0 时 write = &{wdata_write,wdata_read}（两位 AND），即 R=0 时 W 也被强为 0；MML=1 时 write = wdata_write（允许所有组合） |
| 23 | **mepc/depc 最低位清零** | ibex_cs_registers.sv:616,630 | mepc_d = {wdata[31:1], 1'b0}, depc_d = {wdata[31:1], 1'b0}；对齐到 2 字节边界 |
| 24 | **mtvec 模式强制_vectored** | ibex_cs_registers.sv:626-627 | mtvec_d 最低两位强制 2'b01（vectored 模式），BASE 高位强制 256 字节对齐（[7:0] 清零） |
| 25 | **priv_mode_lsu_o 受 MPRV 影响** | ibex_cs_registers.sv:864 | priv_mode_lsu_o = mstatus_q.mprv ? mstatus_q.mpp : priv_lvl_q；MPRV=1 时 LS 用 mpp 而非当前 priv |
| 26 | **MRET 恢复特权** | ibex_cs_registers.sv:820 | priv_lvl_d = mstatus_q.mpp；MRET 恢复到保存的 mpp 值 |
| 27 | **DRET 恢复特权** | ibex_cs_registers.sv:816 | priv_lvl_d = dcsr_q.prv；DRET 恢复到 dcsr 保存的 prv |
| 28 | **异常→强制 M 模式** | ibex_cs_registers.sv:774 | csr_save_cause_i 时 priv_lvl_d = PRIV_LVL_M |
| 29 | **异常不更新 CSR 在 debug 模式** | ibex_cs_registers.sv:784 | debug_mode_i=1 时非 debug_csr_save 路径跳过 mstatus/mepc/mcause 更新 |
| 30 | **ShadowCSR 错误聚合** | ibex_cs_registers.sv:1721-1722 | csr_shadow_err_o = mstatus_err | mtvec_err | pmp_csr_err | cpuctrlsts_part_err | cpuctrlsts_ic_scr_key_err；所有 shadow CSR 错误必须向上传播 |
| 31 | **trigger_match 只在非 debug 模式生效** | ibex_cs_registers.sv:1511-1516 | tmatch_control_we/value_we 限 debug_mode_i=1 时可写 |
| 32 | **DbgTriggerEn 未配置时 trigger CSR 非法** | ibex_cs_registers.sv:551-575 | DbgTriggerEn=0 时 TSELECT/TDATA1/2/3/MCONTEXT/SCONTEXT/MSCONTEXT → illegal_csr=1 |

## 五、树内参考

| # | 参考物 (绝对路径) | 类型 | 可对比什么 |
|---|---|---|---|
| 1 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_pmp.sv | 兄弟模块 | PMP 权限检查函数 mml_perm_check/orig_perm_check 与 ibex_cs_registers.sv 的 mseccfg/pmp_cfg 语义一致性；ibex_pmp.sv 使用 csr_pmp_mseccfg_i.rlb 但赋给 unused |
| 2 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_csr.sv | 参考实现 | ibex_csr 原语的 ShadowCopy 分支：shadow_q = ~ResetValue, rd_error = (rdata_q != ~shadow_q)；所有 CSR 实例的 ShadowCopy 参数和错误输出连线是否一致 |
| 3 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_pkg.sv | 规范注释 | pmp_mseccfg_t/priv_lvl_e/PMP_MODE_*/CSR_MSECCFG_* 的编码定义；RTL 行为必须匹配这些类型约束 |
| 4 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_controller.sv | 兄弟模块 | ebreak_into_debug 使用 debug_ebreakm_i/debug_ebreaku_i (ibex_controller.sv:397-398)，必须与 ibex_cs_registers.sv:893-894 的输出一致 |
| 5 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_core.sv | 兄弟模块 | SEC_CM EXCEPTION.CTRL_FLOW 锚点 (ibex_core.sv:118-119) 必须与 ibex_cs_registers.sv:802-803/828-829 对应；double_fault_seen_o 信号连线 |
| 6 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/rv_core_ibex/data/rv_core_ibex_sec_cm_testplan.hjson | testplan | 12 条 sec_cm 验证点与 RTL 锚点一一映射 |

## 六、特殊结构提示

- **mseccfg.mml/mmwp 粘性语义疑似缺失**：ibex_cs_registers.sv:1271-1272 直接赋值 wdata 而非 OR 累积（应为 `pmp_mseccfg_d.mml = pmp_mseccfg_q.mml | csr_wdata_int[CSR_MSECCFG_MML_BIT]`），SW 写 0 可清已置位——这是 sticky-bit-removal 漏洞模式的高概率候选（对照 OT-023 mseccfg GT）
- **ibex_pmp.sv:309 unused_csr_pmp_mseccfg_rlb**：RLB 位在 PMP 检查模块被赋给 unused，但实际影响 pmp_cfg_locked（通过 ibex_cs_registers.sv:1229），需确认信号传播链完整
- **pmp_addr_rdata 粒度分支**：ibex_cs_registers.sv:1144-1175 三分支（G=0, G=1, G≥2）各有不同掩码逻辑，任一分支的掩码/拼接错误即破坏 NAPOT 地址编码
- **privilege_level_violation 公式含冗余项**：ibex_cs_registers.sv:331 `(~dbg_csr | debug_mode_i)` 在 combined_access_check 中与其他项做 OR，但 illegal_csr_insn_o:340 又 `& ~privilege_level_violation`——此交互语义需逐路径验证
- **csr_we_int 与 illegal_csr_insn_o 的循环安全**：illegal_csr_insn_o 依赖 combined_access_check 包含 illegal_csr（read 逻辑设置），csr_we_int 又依赖 ~illegal_csr_insn_o——无组合环路但需验证 illegal_csr 在 read 逻辑中不依赖 csr_we_int
- **ibex_pmp.sv:285 pmp_req_err_o 赋值异常**：`pmp_req_err_o[c] = access_violation_detected & ~fault_analysis_result` 即 `(~debug_bypass & fault_analysis_result) & ~fault_analysis_result = 0` 恒零——对比原始 ibex_pmp 应为 `access_violation_detected`，此处可能为注入错误
