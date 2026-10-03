# ibex-pmp 候选清单

## 覆盖摘要

- 扫描文件：
  - `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_pmp.sv`（全文件 310 行）
  - `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv`（line 1140-1320，PMP CSR 区域）
  - `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_core.sv`（line 1185-1222，PMP 实例化与接线）
  - `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_pkg.sv`（line 380-460，PMP 类型定义）
  - `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/doc/03_reference/pmp.rst`（规范文档）
  - `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/rv_core_ibex/data/rv_core_ibex.hjson`（feature + countermeasures 声明）
- 每个 lens 产出：L1=1, L2=3, L3=2, L4=2, L5=0, L6=0 → 合计 8 候选
- 未覆盖区域：ibex_cs_registers.sv 非 PMP 区域（dcsr/ebreak 等）；ibex_id_box/ex 的 PMP 错误消费路径时序；PMPGranularity>2 的地址掩码扩展验证

---

### CAND-ibex-pmp-01

- 疑点: `pmp_req_err_o` 恒为零——PMP 永不报错，所有内存访问均被允许
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_pmp.sv:285`
- 代码摘录:
  ```systemverilog
  // line 282
  access_violation_detected = ~debug_bypass_active & fault_analysis_result;
  // line 285
  assign pmp_req_err_o[c] = access_violation_detected & ~fault_analysis_result;
  ```
  代入 line 282：`pmp_req_err_o = (~debug_bypass_active & fault_analysis_result) & ~fault_analysis_result = 0`
- lens: L1 SEC_CM-vs-RTL（fixed-value-signal 模式）+ L2 hjson-spec-vs-RTL
- 预言机依据:
  1. pmp.rst:59 "In debug mode, the PMP allows all accesses to the Debug Module"——隐含语义：非 debug 模式下 PMP 必须能拒绝违规访问
  2. RISC-V Privileged Spec v1.12 §3.7：PMP 必须能产生 access fault
  3. ibex_core.sv:761 `data_req_o = data_req_out & ~pmp_req_err[PMP_D]`——pmp_req_err=0 意味着 data_req 永不被门控
  4. ibex_core.sv:480 `pmp_err_if_i = pmp_req_err[PMP_I]`——取指错误永不为 1
  5. oracle-inventory §5.1 同一分析（预言机交叉确认）
- 建议验证型: 组合 micro-tb（给定 PMP region 配置 + 违规地址，断言 pmp_req_err_o=1；vuln 版全 0，twin 版正确报错）

---

### CAND-ibex-pmp-02

- 疑点: `mseccfg.MML` 和 `mseccfg.MMWP` 缺 sticky-one 语义——SW 可写 0 清除，违反 Smepmp v1.0 spec
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:1271-1272`
- 代码摘录:
  ```systemverilog
  // line 1270 注释："MSECCFG.MML/MSECCFG.MMWP cannot be unset once set"
  // line 1271
  assign pmp_mseccfg_d.mml  = csr_wdata_int[CSR_MSECCFG_MML_BIT];
  // line 1272
  assign pmp_mseccfg_d.mmwp = csr_wdata_int[CSR_MSECCFG_MMWP_BIT];
  ```
  缺少 `pmp_mseccfg_q.mml |` / `pmp_mseccfg_q.mmwp |` 保持逻辑。
- lens: L2 hjson-spec-vs-RTL（sticky-bit-removal 模式）
- 预言机依据:
  1. ibex_cs_registers.sv:1270 同文件注释："MSECCFG.MML/MSECCFG.MMWP cannot be unset once set"——注释直接声称 sticky 语义
  2. pmp.rst:44 "A new CSR mseccfg providing functionality to allow locked regions to be modified and to implement default deny for M-mode accesses"——Smepmp 功能不可撤销
  3. Smepmp v1.0 spec Table 1：MML 和 MMWP 为 sticky-one 位
  4. oracle-inventory §5.2 同一分析
- 建议验证型: 组合 micro-tb（写 MML=1 → 读 MML=1 → 写 MML=0 → 读 MML：vuln 返回 0，twin 返回 1）

---

### CAND-ibex-pmp-03

- 疑点: `access_fault_check` 函数接收 `csr_pmp_mseccfg_mmwp` 和 `csr_pmp_mseccfg_mml` 参数但未使用——MMWP 默认拒绝和 MML 未匹配 EXEC 拒绝语义未实现
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_pmp.sv:129-151`
- 代码摘录:
  ```systemverilog
  function automatic logic access_fault_check (logic csr_pmp_mseccfg_mmwp,
                                               logic csr_pmp_mseccfg_mml,
                                               ...);
    // line 137-138 注释：
    // "When MSECCFG.MMWP is set default deny always, otherwise allow for M-mode, deny for other modes."
    // "Also deny unmatched for M-mode when MSECCFG.MML is set and request type is EXEC."
    logic access_fail = 1'b0;   // 无条件初始化为 0
    logic matched = 1'b0;
    for (int r = 0; r < PMPNumRegions; r++) begin
      if (!matched && match_all[r]) begin
        access_fail = ~final_perm_check[r];
        matched = 1'b1;
      end
    end
    return access_fail;  // 无 region 匹配时永远返回 0（允许）
  endfunction
  ```
  Bugs:
  1. MMWP=1 且无 region 匹配时，`access_fail` 应=1（default-deny），实际=0（allow）
  2. MML=1 且 pmp_req_type=EXEC 且无 region 匹配时，M-mode 应被拒绝，实际=0（allow）
- lens: L2 hjson-spec-vs-RTL + L3 树内参考对比
- 预言机依据:
  1. ibex_pmp.sv:137-138 同文件注释明确声称两种行为："default deny always" 和 "deny unmatched for M-mode"
  2. pmp.rst:44 "implement default deny for M-mode accesses"——MMWP 语义
  3. Smepmp v1.0 spec §2.4：MMWP=1 时 M-mode 无匹配 region 的访问默认拒绝
  4. Smepmp v1.0 spec §2.5：MML=1 时 M-mode EXEC 无匹配默认拒绝
  5. 注释声称但代码未做——典型的 check-bypass / hjson-spec-vs-RTL 矛盾
- 建议验证型: 组合 micro-tb（配置 MMWP=1，无 region 匹配，M-mode READ：vuln 返回 allow，twin 返回 fault）

---

### CAND-ibex-pmp-04

- 疑点: debug 地址窗口 `| ~DmAddrMask` 逻辑错误——debug 窗口永不匹配，debug 模式下 PMP 仍拒绝 Debug Module 地址访问
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_pmp.sv:258`
- 代码摘录:
  ```systemverilog
  debug_address_range_match = ((pmp_req_addr_i[c][31:0] | ~DmAddrMask) == DmBaseAddr);
  ```
  代入 DmAddrMask=32'h00000FFF：`~DmAddrMask=32'hFFFFF000`
  → `(addr | 32'hFFFFF000)` 高 20 位恒为 1 → 结果为 `32'hFFFFF???`
  → 永不等于 `DmBaseAddr=32'h1A110000`
  → `debug_address_range_match` 恒为 0
  → `debug_mode_allowed_access` 恒为 0
  期望正确表达式：`((pmp_req_addr_i[c][31:0] & DmAddrMask) == (DmBaseAddr & DmAddrMask))`
  或等价地使用 `&` 而非 `|`：`((addr & ~DmAddrMask) == (DmBaseAddr & ~DmAddrMask))`
- lens: L4 结构 lint（structural-anomaly 模式）
- 预言机依据:
  1. pmp.rst:59 "In debug mode, the PMP allows all accesses to the Debug Module"——当前实现 debug 模式下 PMP 对 DM 地址仍拒绝
  2. RISC-V Debug Spec v1.0.0 §A.2：debug 模式下 DM 地址访问必须被允许
  3. OT-027 GT 实例：同一注入模式（`|` 替换 `&`），已被 verilator twin 方法验证
  4. ibex_core.sv:1189-1206 实例化传入 DmBaseAddr=32'h1A110000, DmAddrMask=32'h00000FFF——参数确认窗口不可匹配
- 建议验证型: 组合 micro-tb + XMR probe（驱动 debug_mode=1 + DM 地址，probe debug_address_range_match：vuln=0，twin=1）

---

### CAND-ibex-pmp-05

- 疑点: `pmp_mseccfg_d.rlb` 赋值依赖 `pmp_mseccfg.rlb`（注意：非 `pmp_mseccfg_q.rlb`）——读出值 vs 写入值混用
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:1234`
- 代码摘录:
  ```systemverilog
  // line 1233
  assign pmp_cfg_wr_suppress[i] = pmp_mseccfg_q.mml  &
                                  ~pmp_mseccfg.rlb    &   // ← pmp_mseccfg, not pmp_mseccfg_q
                                  is_mml_m_exec_cfg(pmp_cfg_wdata[i]);
  // line 1297
  assign pmp_mseccfg = pmp_mseccfg_q;  // pmp_mseccfg 是 pmp_mseccfg_q 的别名
  ```
  在 line 1297 `pmp_mseccfg = pmp_mseccfg_q`，所以当前两者等价。但这是非典型用法——同一文件中 line 1229 用 `pmp_mseccfg_q.rlb`，line 1234 用 `pmp_mseccfg.rlb`。若未来 `pmp_mseccfg` 赋值逻辑改变（如改为组合计算值），此行将静默出错。
- lens: L4 结构 lint（命名一致性）
- 预言机依据:
  1. 同文件 line 1229 使用 `pmp_mseccfg_q.rlb`（一致用法）
  2. 同文件 line 1297 `pmp_mseccfg = pmp_mseccfg_q`——当前等价，但设计意图不明确
  3. 单一依据，存疑
- 建议验证型: 代码审计确认意图即可（无动态验证需求）

---

### CAND-ibex-pmp-06

- 疑点: PMP 地址粒度 g_pmp_g1 (Granularity==1) 掩码实现——`mask_bits & '0` 恒零但注释声称清低位
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:1148-1160`
- 代码摘录:
  ```systemverilog
  end else if (PMPGranularity == 1) begin : g_pmp_g1
    always_comb begin
      logic [PMPGranularity-1:0] mask_bits;   // [0:0]，1 bit
      mask_bits = pmp_addr[i][PMPGranularity-1:0];  // 取 1 bit
      pmp_addr_rdata[i] = pmp_addr[i];
      if ((pmp_cfg[i].mode == PMP_MODE_OFF) || (pmp_cfg[i].mode == PMP_MODE_TOR)) begin
        pmp_addr_rdata[i][PMPGranularity-1:0] = mask_bits & '0;  // 1bit & 0 = 恒0
      end
    end
  ```
  `mask_bits & '0` 恒为 0——等效于直接赋 0。虽功能结果与"清低位"目标一致（PMPGranularity-1:0 = bit 0，应清零），但 `mask_bits` 变量完全冗余，且若粒度增加导致 `mask_bits` 宽度>1，`& '0` 将错误地清所有位而非保留高位。实际 g_pmp_g2 分支（line 1162-1175）用了 `napot_mask` 拼接方式，两分支逻辑不一致。
- lens: L3 树内参考对比 + L4 结构 lint
- 预言机依据:
  1. ibex_pkg.sv:686 `PmpAddrRst` 全零 + RISC-V spec pmpaddr 字节形约束——PMPGranularity>0 时低位必须为 0
  2. g_pmp_g2 分支（line 1162-1175）用 `{pmp_addr[i], napot_mask}` 拼接——同一功能两个不同实现模式，g_pmp_g1 的 `mask_bits & '0` 惯用法与 g_pmp_g2 不一致
  3. RISC-V Privileged Spec §3.7：pmpaddr 读出值的低位取决于 mode 和 granularity
  4. 单一依据为主，存疑
- 建议验证型: 脚本验证（PMPGranularity=1，mode=TOR/OFF → 读 pmpaddr 低位应为 0；当前实现正确但脆弱）

---

### CAND-ibex-pmp-07

- 疑点: PMP 地址粒度 g_pmp_g2 (Granularity>=2) 拼接位宽可能不匹配——`{pmp_addr[i], napot_mask}` 拼接宽度 vs PMPAddrWidth
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv:1162-1175`
- 代码摘录:
  ```systemverilog
  end else begin : g_pmp_g2
    always_comb begin
      logic [PMPGranularity-2:0] napot_mask;
      napot_mask = {(PMPGranularity){1'b1}};
      pmp_addr_rdata[i] = {pmp_addr[i], napot_mask};
      if ((pmp_cfg[i].mode == PMP_MODE_OFF) || (pmp_cfg[i].mode == PMP_MODE_TOR)) begin
        pmp_addr_rdata[i][PMPGranularity-2:0] = '0;
      end
    end
  ```
  `pmp_addr[i]` 宽度 = PMPAddrWidth = 33 - PMPGranularity（line 152）
  `napot_mask` 宽度 = PMPGranularity - 1
  拼接宽度 = PMPAddrWidth + (PMPGranularity - 1) = (33 - PMPGranularity) + (PMPGranularity - 1) = 32
  但 `pmp_addr_rdata[i]` 宽度 = 32（line 252: `logic [31:0] pmp_addr_rdata`）
  → 拼接宽度恰好匹配。**但** `pmp_addr_rdata[i]` 在 csr_pmp_addr_o 被拼接为 `{pmp_addr_rdata[i], 2'b00}`（line 1265），形成 34 位——原始 pmpaddr 为 34 位，但 rdata 只有 32 位。当 PMPGranularity=0 时 PMPAddrWidth=32，rdata 覆盖全部位；当 PMPGranularity>0 时 PMPAddrWidth<32，rdata 少了高位——但 pmp_addr 本身就只存 PMPAddrWidth 位，高位由 mode 决定（NAPOT 全 1 / TOR/OFF 不关心），所以拼接 `napot_mask` 低位实际上正确填充了 NAPOT pattern。**功能可能正确**，但 `{pmp_addr[i], napot_mask}` 静默依赖 pmp_addr 宽度+napot_mask 宽度=32 的不变量——若 PMPAddrWidth 定义改变将静默截断或扩展。
- lens: L4 结构 lint
- 预言机依据:
  1. line 152 `PMPAddrWidth = (PMPGranularity > 0) ? 33 - PMPGranularity : 32`——宽度约束
  2. line 1265 `csr_pmp_addr_o[i] = {pmp_addr_rdata[i], 2'b00}`——rdata 到 34 位输出
  3. 单一依据，存疑（功能可能正确，结构脆弱）
- 建议验证型: 脚本验证 PMPGranularity=2,4,16 场景下 pmpaddr 读出值与 spec 一致

---

### CAND-ibex-pmp-08

- 疑点: SEC_CM 声明覆盖缺口——PMP 无专属 sec_cm 条目，testplan 有 TODO 注释缺验证条目
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/rv_core_ibex/data/rv_core_ibex.hjson`（countermeasures 列表）+ `rv_core_ibex_testplan.hjson:344`
- 代码摘录:
  ```
  rv_core_ibex.hjson countermeasures 列表：13 条无 PMP 专属条目（仅有 BUS.INTEGRITY, EXCEPTION.CTRL_FLOW.LOCAL_ESC/GLOBAL_ESC 等非 PMP 专属条目）
  rv_core_ibex_testplan.hjson:344: // TODO: Need to add testplan entries for PMP and nested trap tests
  ```
- lens: L1 SEC_CM-vs-RTL（声明缺口）
- 预言机依据:
  1. rv_core_ibex.hjson:528 feature `RV_CORE_IBEX.CPU.EPMP` 声明 ePMP 支持——PMP 是安全关键功能
  2. countermeasures 列表（line 583-640）无 PMP 专属 sec_cm——PMP 错误报告、sticky 位、lock 语义均无对策声明
  3. rv_core_ibex_testplan.hjson:344 TODO 注释明确承认 PMP 验证缺失
  4. oracle-inventory §5.6 同一分析
  5. 综合 CAND-01（pmp_req_err 恒零）+ CAND-02（sticky 缺失）+ CAND-04（debug 窗口死）均无 sec_cm 覆盖
- 建议验证型: 代码审计（确认 sec_cm 声明缺口）

---

## 候选汇总

| 序号 | 疑点 | lens | 预言机强度 | 优先级 |
|---|---|---|---|---|
| 01 | pmp_req_err_o 恒零 | L1+L2 | 5 条树内依据 | **最高** |
| 02 | mseccfg MML/MMWP 缺 sticky | L2 | 4 条树内依据 | **最高** |
| 03 | access_fault_check MMWP/MML 未实现 | L2+L3 | 5 条树内依据 | **最高** |
| 04 | debug 窗口 `丨` 误用 | L4 | 4 条树内依据 | **高** |
| 05 | pmp_mseccfg vs pmp_mseccfg_q 混用 | L4 | 2 条（存疑） | 低 |
| 06 | g_pmp_g1 mask_bits & '0 冗余 | L3+L4 | 3 条（存疑） | 低 |
| 07 | g_pmp_g2 拼接位宽隐含约束 | L4 | 2 条（存疑） | 低 |
| 08 | SEC_CM 声明缺口 | L1 | 5 条树内依据 | 中 |
