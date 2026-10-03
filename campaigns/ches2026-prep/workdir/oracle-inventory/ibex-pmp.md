# ibex-pmp 盲预言机目录

## 元信息
- 树: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
- 扫描范围: hw/vendor/lowrisc_ibex/rtl（重点 ibex_pmp.sv）+ hw/top_earlgrey/ip_autogen/rv_core_ibex/data（hjson）+ hw/vendor/lowrisc_ibex/doc/03_reference/pmp.rst
- SEC_CM 声明数: 0（PMP 无独立 SEC_CM；rv_core_ibex.hjson countermeasures 列表无 PMP 专属条目） / SVA 数: 1（PMP 相关） / testplan 条目数: 13（无 PMP 专属；testplan 有 TODO 注释 PMP 缺验证条目）

## 一、SEC_CM 声明 ↔ RTL 锚点

| # | SEC_CM 声明 (hjson:line) | RTL 锚点 (file:line) | 检验要点 |
|---|---|---|---|
| 1 | RV_CORE_IBEX.CPU.EPMP (feature, 非 sec_cm) (rv_core_ibex.hjson:528) | ibex_pmp.sv:7 整模块 | hjson 声明 ePMP+Smepmp，RTL ibex_pmp.sv 必须实现全部 4 种 mode (OFF/NA4/NAPOT/TOR) + MML/MMWP/RLB 三位 mseccfg 语义；验证 region_match_all 四路分支与 mml_perm_check/orig_perm_check/perm_check_wrapper 三函数完整 |
| 2 | EXCEPTION.CTRL_FLOW.LOCAL_ESC (rv_core_ibex.hjson:622) | ibex_cs_registers.sv:802,828 | 非纯 PMP 但影响 PMP 上下文：double fault 时 core 停机，PMP 不再检查新请求；验证 sync_exc_seen→double_fault_seen 链 |
| 3 | EXCEPTION.CTRL_FLOW.GLOBAL_ESC (rv_core_ibex.hjson:628) | ibex_cs_registers.sv:803,829 | 同上，double fault 发 fatal alert；验证 alert_major_internal_o 触发路径 |

## 二、行为性描述句（hjson 原文 → 检验点）

| # | hjson/文档 原文 (file:line) | 检验点 |
|---|---|---|
| 1 | "implements the ePMP scheme specified in the RISC-V Privileged architecture specification, 16 regions are available for use" (rv_core_ibex.hjson:530) | ibex_pmp.sv PMPNumRegions 参数可达 16；ibex_pkg.sv:388 PMP_MAX_REGIONS=16；ibex_cs_registers.sv PMPNumRegions 参数默认 4 但可配置到 16 |
| 2 | "PMP+Smepmp" (rv_core_ibex.hjson:10) | ibex_pmp.sv mml_perm_check(:60) 实现 Smepmp MML 语义；perm_check_wrapper(:114) 按 csr_pmp_mseccfg_i.mml 选择 MML 或原始检查 |
| 3 | "A new CSR mseccfg providing functionality to allow locked regions to be modified and to implement default deny for M-mode accesses" (pmp.rst:44) | ibex_cs_registers.sv:1229 pmp_cfg_locked[i] = pmp_cfg[i].lock & ~pmp_mseccfg_q.rlb（RLB 绕过锁定位）；ibex_cs_registers.sv:1271 pmp_mseccfg_d.mml/mmwp 无 sticky 逻辑（原文说 once set cannot be unset，但 RTL 中 pmp_mseccfg_d.mml 直接赋 csr_wdata_int 无 OR 保持） |
| 4 | "When the granularity is greater than zero, NA4 mode is not available and will be treated as OFF mode" (pmp.rst:32) | ibex_cs_registers.sv:1201 PMPGranularity>0 时 pmp_cfg_wdata[i].mode 2'b10→PMP_MODE_OFF |
| 5 | "In debug mode, the PMP allows all accesses to addresses of the Debug Module" (pmp.rst:59) | ibex_pmp.sv:258 debug_address_range_match 计算；ibex_pmp.sv:259 debug_mode_allowed_access = debug_mode_i & debug_address_range_match |
| 6 | "When MSECCFG.MML is unset, W = 1, R = 0 is a reserved combination, so force W to 0 if R == 0" (ibex_cs_registers.sv:1209 注释) | ibex_cs_registers.sv:1210 pmp_cfg_wdata[i].write = pmp_mseccfg_q.mml ? csr_wdata_int[...] : &csr_wdata_int[...]（MML 未置时 W=R=0 才允许 W=0） |
| 7 | "When any PMP entry is locked, MSECCFG.RLB cannot be set again" (ibex_cs_registers.sv:1280 注释) | ibex_cs_registers.sv:1281 pmp_mseccfg_d.rlb = any_pmp_entry_locked ? 1'b0 : csr_wdata_int[CSR_MSECCFG_RLB_BIT] |
| 8 | "When MSECCFG.MML is set cannot add new regions allowing M mode execution unless MSECCFG.RLB is set" (ibex_cs_registers.sv:1232 注释) | ibex_cs_registers.sv:1233 pmp_cfg_wr_suppress[i] = pmp_mseccfg_q.mml & ~pmp_mseccfg.rlb & is_mml_m_exec_cfg(pmp_cfg_wdata[i]) |
| 9 | "PMP entries are statically prioritized, from 0 to N-1; The lowest-numbered PMP entry which matches an address determines accessibility" (ibex_pmp.sv:142-143) | ibex_pmp.sv access_fault_check(:129) for 循环 r=0→PMPNumRegions-1，!matched 时取第一个 match_all[r] 的结果 |

## 三、SVA 清单（行为合同）

| # | 断言 (file:line) | 内容摘要 | 约束的预期行为 |
|---|---|---|---|
| 1 | `ASSERT_INIT PMPAddrRstLowBitsZero_A (ibex_cs_registers.sv:1262) | PMPRstAddr[i][33-PMPAddrWidth:0] == '0 | PMP 地址重置值低位必须为零（字节对齐），参数约束 |
| 2 | `ASSERT IbexCsrOpEnRequiresAccess (ibex_cs_registers.sv:1728) | csr_op_en_i |-> csr_access_i | CSR 操作使能蕴含 CSR 访问信号（非 PMP 专属，但约束 PMP CSR 写路径） |

（注：ibex_pmp.sv 自身无任何 SVA 断言，仅有一个 `DV_FCOV_SIGNAL` 在 ibex_pmp.sv:297）

## 四、树内参考

| # | 参考物 (绝对路径) | 类型 | 可对比什么 |
|---|---|---|---|
| 1 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/doc/03_reference/pmp.rst | 规范注释（RISC-V Privileged Spec v1.12 + Smepmp v1.0） | pmp.rst 声明的行为与 RTL ibex_pmp.sv 的实现逐条对照：MML shared-region 表、MMWP default-deny、RLB lock bypass、debug window |
| 2 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/rv_core_ibex/data/rv_core_ibex.hjson | hjson 寄存器规格 | PMP 参数（PMPEnable/PMPGranularity/PMPNumRegions/PMPRstCfg/PMPRstAddr/PMPRstMsecCfg）与 RTL 默认值一致性；feature RV_CORE_IBEX.CPU.EPMP 声明 |
| 3 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/rv_core_ibex/data/rv_core_ibex_sec_cm_testplan.hjson | sec_cm 验证计划 | 13 条 sec_cm 无 PMP 专属条目——PMP 对策验证覆盖缺口 |
| 4 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv | 兄弟模块（CSR 端） | PMP cfg/addr 写使能逻辑（pmp_cfg_we/pmp_addr_we）与 ibex_pmp.sv 的读端语义一致性；mseccfg sticky 语义；lock+RLB 交互；addr 字节形掩码 |

## 五、特殊结构提示

### 5.1 pmp_req_err_o 语义异常（高优先级候选）

ibex_pmp.sv:285 `assign pmp_req_err_o[c] = access_violation_detected & ~fault_analysis_result;`

而 ibex_pmp.sv:282 `access_violation_detected = ~debug_bypass_active & fault_analysis_result;`

代入：`pmp_req_err_o = (~debug_bypass_active & fault_analysis_result) & ~fault_analysis_result = 0`（恒零）

**预言机依据**：pmp.rst:59 "In debug mode, the PMP allows all accesses to the Debug Module" + RISC-V Privileged Spec——PMP 在非 debug 访问时必须能产生 access fault。当前 RTL pmp_req_err_o 恒为 0，PMP 永不报错。

**期望正确表达式**：`pmp_req_err_o[c] = access_violation_detected`（即 `~debug_bypass_active & fault_analysis_result`）或等价地 `pmp_req_err_o[c] = ~debug_mode_allowed_access[c] & fault_analysis_result`。

### 5.2 mseccfg.MML/MMWP 缺失 sticky 语义（高优先级候选）

ibex_cs_registers.sv:1271-1272：
```
assign pmp_mseccfg_d.mml  = csr_wdata_int[CSR_MSECCFG_MML_BIT];
assign pmp_mseccfg_d.mmwp = csr_wdata_int[CSR_MSECCFG_MMWP_BIT];
```

pmp.rst:44 + Smepmp v1.0 spec：MML 和 MMWP 一旦置 1 不可清零（sticky-one）。

当前 RTL 直接用 csr_wdata_int 赋值，无 `pmp_mseccfg_q.mml |` 保持逻辑，SW 可写 0 清除 MML/MMWP。

**预言机依据**：pmp.rst:44 "allow locked regions to be modified and to implement default deny" + Smepmp spec Table 1 sticky 语义。

**期望正确表达式**：
```
assign pmp_mseccfg_d.mml  = pmp_mseccfg_q.mml | csr_wdata_int[CSR_MSECCFG_MML_BIT];
assign pmp_mseccfg_d.mmwp = pmp_mseccfg_q.mmwp | csr_wdata_int[CSR_MSECCFG_MMWP_BIT];
```

### 5.3 RLB 在 ibex_pmp.sv 被吸到 unused（信息性）

ibex_pmp.sv:304 `unused_config_fields[0] = csr_pmp_mseccfg_i.rlb;`

RLB 在 ibex_pmp.sv 中不参与权限检查，仅在 ibex_cs_registers.sv:1229 中用于 `pmp_cfg_locked[i] = pmp_cfg[i].lock & ~pmp_mseccfg_q.rlb`。这是正确分工（写端在 CSR 模块，检查端在 PMP 模块用 pmp_cfg_locked 输入），但需确认 ibex_pmp.sv 收到的 csr_pmp_cfg_i[i].lock 已是 RLB 处理后的值——实际上 ibex_pmp.sv 收到的是原始 pmp_cfg[i].lock，RLB 逻辑在 ibex_cs_registers.sv 的写使能端而非读出端。

### 5.4 pmp_cfg_locked 与 ibex_pmp.sv 的 lock 语义分歧

ibex_cs_registers.sv:1229 `pmp_cfg_locked[i] = pmp_cfg[i].lock & ~pmp_mseccfg_q.rlb` 仅用于写使能门控。

ibex_pmp.sv:94 在 orig_perm_check 中直接用 `region_csr_pmp_cfg.lock`（即 pmp_cfg[i].lock 原始值）做权限判定。

若 RLB=1 且 L=1：ibex_cs_registers.sv 允许写（pmp_cfg_locked=0），但 ibex_pmp.sv 的 orig_perm_check 仍按 L=1 判 M-mode allow-all。这是 Smepmp spec 正确语义——RLB 只影响写使能，不影响运行时权限检查。

### 5.5 PMP 地址字节形掩码（ibex_cs_registers.sv:1144-1175）

PMPGranularity>0 时 pmp_addr_rdata 的低位掩码逻辑分三段（g_pmp_g0/g_pmp_g1/g_pmp_g2），
g_pmp_g1（line 1148-1160）和 g_pmp_g2（line 1162-1175）的实现与上游 Ibex 参考不同：
- g_pmp_g1：用 always_comb + mask_bits 但 `mask_bits & '0` 恒零，实际效果是清低粒度位
- g_pmp_g2：用 `{pmp_addr[i], napot_mask}` 拼接，位宽可能不匹配（PMPAddrWidth vs 32）

**预言机依据**：ibex_pkg.sv:686 PmpAddrRst 全零 + RISC-V spec pmpaddr 字节形约束。

### 5.6 testplan 缺 PMP 验证条目

rv_core_ibex_testplan.hjson:344 注释 `// TODO: Need to add testplan entries for PMP and nested trap tests`

PMP 功能无对应验证点——hjson feature 声明 ePMP 但 sec_cm_testplan 无 PMP 条目，testplan 也有 TODO。
