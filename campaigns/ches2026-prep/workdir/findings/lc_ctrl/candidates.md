# lc_ctrl Candidate Vulnerabilities

## Coverage Summary

- **Scanned files**: lc_ctrl.sv, lc_ctrl_fsm.sv, lc_ctrl_signal_decode.sv, lc_ctrl_state_decode.sv, lc_ctrl_state_transition.sv, lc_ctrl_state_pkg.sv, lc_ctrl_pkg.sv, lc_ctrl_kmac_if.sv, lc_ctrl_regs_reg_top.sv, lc_ctrl_dmi_reg_top.sv, lc_ctrl.hjson, lc_ctrl_state.hjson, lc_ctrl_sec_cm_testplan.hjson
- **L1 (SEC_CM-vs-RTL)**: 17 SEC_CM declarations checked → 1 candidate (token width truncation)
- **L2 (hjson-spec-vs-RTL)**: 13 behavioral descriptions checked → 1 candidate (clkbyp in prod states contradicts SVA)
- **L3 (Tree-in reference)**: 7 references checked → 1 candidate (LcStProd duplicate case)
- **L4 (Structural lint)**: case dedup, port lint, default branch → 4 candidates (duplicate case, token truncation, clkbyp SVA contradiction, SEC_CM gap)
- **L5 (Constant folding)**: Python script verified all A0-A19/B0-B19/C0-C23/D0-D23 + ECC + hashed tokens → 1 minor finding (D[15] ECC comment typo)
- **L6 (SCA structure)**: lc_ctrl is not a crypto module; token comparison truncation is the only SCA-relevant finding (already captured in L1/L4)

---

### CAND-lc_ctrl-001
- 疑点: `unique case (lc_state_i)` 中 LcStProd 出现两次——第一分支赋予 TEST_UNLOCKED 级权限（dft_en/nvm_debug_en/hw_debug_en 全开），第二分支赋予 PROD 级权限。SV first-match-wins 语义下 PROD 态命中第一分支，导致生产芯片暴露全部测试/调试接口
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_signal_decode.sv:116 + :139
- 代码摘录:
  ```systemverilog
  // Line 109-124: First branch (test-unlocked group)
  LcStTestUnlocked0,
  ...
  LcStTestUnlocked6,
  LcStProd: begin            // ← LcStProd HERE (line 116)
    lc_raw_test_rma      = On;
    lc_dft_en            = On;   // ← WRONG for PROD
    lc_nvm_debug_en      = On;   // ← WRONG for PROD
    lc_hw_debug_en       = On;   // ← WRONG for PROD
    lc_keymgr_div_d      = RndCnstLcKeymgrDivTestUnlocked; // ← WRONG for PROD
  end
  // Line 139-154: Second branch (production group)
  LcStProd,
  LcStProdEnd: begin         // ← LcStProd HERE AGAIN (line 139)
    lc_cpu_en              = On;
    lc_keymgr_en           = On;   // ← correct for PROD but unreachable
    lc_keymgr_div_d        = RndCnstLcKeymgrDivProduction;
  end
  ```
- lens: L3 (tree-in reference: lc_ctrl_state.hjson PROD definition) + L4 (structural lint: case dedup)
- 预言机依据:
  1. lc_ctrl_signal_decode.sv:93 声明 `unique case`，SV LRM 要求所有 case 值唯一——重复 = 编译错误或未定义行为
  2. lc_ctrl_state.hjson:70 定义 PROD 状态结构，无任何注释说明 PROD 应获得测试级权限
  3. lc_ctrl.hjson:670 "Life cycle control signals are multibit encoded" + INTERSIG.MUBI 声明要求 PROD 态不使能 dft_en/hw_debug_en
  4. NoClkBypInProdStates_A 断言 (lc_ctrl_fsm.sv:860) 间接佐证：PROD 态不应有测试功能
  5. OT-027 GT 实例明确指出 lc_ctrl LcStProd 重复 case 是已知的 Critical 类型结构性异常
- 建议验证型: 组合micro-tb——直接驱动 signal_decode 输入 lc_state_i=LcStProd + lc_state_valid_i=1 + fsm_state_i=IdleSt，检查输出 lc_dft_en_o/lc_nvm_debug_en_o/lc_hw_debug_en_o 是否为 On（vuln=On, twin=Off）

---

### CAND-lc_ctrl-002
- 疑点: Token 三重比较仅使用低 32 位 (`hashed_token_i[31:0] == hashed_token_mux[31:0]`)，128 位 token 高 96 位不参与比较，碰撞空间从 2^128 降至 2^32
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv:456 + :497
- 代码摘录:
  ```systemverilog
  // Line 456 (TokenHashSt):
  if (hashed_token_i[31:0] == hashed_token_mux[31:0] &&  // ← only low 32 bits!
      !token_hash_err_i &&
      &hashed_token_valid_mux) begin
  // Line 497 (TokenCheck0St/TokenCheck1St):
  if (hashed_token_i[31:0] == hashed_token_mux[31:0] &&  // ← same truncation
      !token_hash_err_i &&
      &hashed_token_valid_mux) begin
  ```
- lens: L1 (SEC_CM TOKEN.DIGEST 声明 vs 实现) + L4 (width truncation pattern)
- 预言机依据:
  1. SEC_CM TOKEN.DIGEST (lc_ctrl.hjson:676) 声明 "tokens are hashed with cSHAKE128"——全 128 位哈希但比较只取 32 位，与"安全哈希"语义矛盾
  2. lc_ctrl_state_pkg.sv:412 `LcTokenWidth = 128` 定义 128 位 token，比较却硬编码 `[31:0]`
  3. OT-013 GT 实例：lc_ctrl token 128→32 位截断是已确认的 GT 漏洞
  4. lc_ctrl_sec_cm_testplan.hjson 应有对应验证点检查全位宽比较
- 建议验证型: 组合micro-tb——构造两个仅高 96 位不同的 token：vuln 判等（放行非法转换），twin 判不等（拒绝）

---

### CAND-lc_ctrl-003
- 疑点: IdleSt 中 LcStDev/LcStProd 被列入时钟旁路允许列表，但 NoClkBypInProdStates_A 断言声明 DEV/PROD/PROD_END 态下 clk_byp_req 必须为 Off——SVA 与 RTL 行为矛盾
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv:335-357 (IdleSt) vs :860-863 (assertion)
- 代码摘录:
  ```systemverilog
  // Line 335-357 (IdleSt): LcStDev and LcStProd in bypass list
  if (lc_state_q inside {LcStRaw, ..., LcStDev, LcStProd, LcStRma}) begin
    if (use_ext_clock_i) begin
      lc_clk_byp_req = On;    // ← allows bypass in DEV/PROD!
    end
  end
  // Line 860-863: Assertion says NO bypass in production states
  `ASSERT(NoClkBypInProdStates_A,
      lc_state_q inside {LcStProd, LcStProdEnd, LcStDev}
      |=>
      lc_clk_byp_req_o == Off)    // ← contradicts IdleSt code
  ```
- lens: L2 (hjson spec: "In PROD/DEV states, clock bypass is not allowed") + L4 (SVA-vs-RTL contradiction)
- 预言机依据:
  1. NoClkBypInProdStates_A (lc_ctrl_fsm.sv:860) 是 in-tree SVA，声称 PROD/DEV/PROD_END 态下 clk_byp_req_o 恒为 Off
  2. IdleSt 代码 (lc_ctrl_fsm.sv:352) 明确包含 LcStDev 和 LcStProd 在可请求旁路的列表中
  3. ClkMuxSt (lc_ctrl_fsm.sv:369-385) 正确排除了 DEV 态但包含 PROD_END 的兄弟——IdleSt 与 ClkMuxSt 逻辑不一致
  4. OT-016 GT 实例：lc_ctrl Dev/Prod clkbyp allow 是已确认的 GT 漏洞（SVA 矛盾盲检命中）
  5. lc_ctrl.hjson 对 TRANSITION_CTRL.EXT_CLOCK_EN 的描述暗示时钟旁路应仅限测试态
- 建议验证型: 时序tb——在 LcStDev/LcStProd + IdleSt 下置 use_ext_clock_i=1，观察 lc_clk_byp_req_o 是否变为 On（vuln=On 违反断言，twin=Off 满足断言）

---

### CAND-lc_ctrl-004
- 疑点: lc_check_byp_en_o 输出仅在 ClkMuxSt 时赋 On，其余态保持 Off，但 hjson 中无对应 SEC_CM 声明——安全对策声明覆盖缺口，且无断言约束该信号的置位条件
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv:368 (ClkMuxSt: lc_check_byp_en=On) + lc_ctrl.sv:820 (output port)
- 代码摘录:
  ```systemverilog
  // lc_ctrl_fsm.sv:368
  ClkMuxSt: begin
    lc_check_byp_en = On;   // ← only state where this is On
  ```
- lens: L1 (SEC_CM 声明覆盖) + L4 (声明未用信号/端口)
- 预言机依据:
  1. lc_ctrl.hjson countermeasures 列表（17 条）中无任何 lc_check_byp_en 相关声明
  2. lc_ctrl_signal_decode.sv 不输出该信号——由 FSM 直接控制
  3. 无 SVA 断言约束 lc_check_byp_en_o 的置位条件（何时应 On/Off）
  4. 下游 OTP check bypass 逻辑的正确消费未被树内预言机覆盖
- 建议验证型: 代码走查——追踪 lc_check_byp_en_o 下游消费点（OTP ctrl），确认仅在合法转换期间旁路生效

---

### CAND-lc_ctrl-005
- 疑点: SecVolatileRawUnlockEn=0 时，volatile_raw_unlock_d 信号通过 `unused_volatile_raw_unlock = ^volatile_raw_unlock_d` 吸收，但 set_strap_en_override 和 volatile_raw_unlock_success_d 的 unused 吸收仅用 XOR 归约——若综合器优化掉这些 unused 信号，门级网表中可能残留悬空逻辑
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv:624-631
- 代码摘录:
  ```systemverilog
  end else begin : gen_no_strap_delay_regs
    logic unused_sigs;
    assign unused_sigs = ^{set_strap_en_override,
                           volatile_raw_unlock_success_d};
    assign strap_en_override_o = 1'b0;
    assign volatile_raw_unlock_success_q = prim_mubi_pkg::MuBi8False;
  end
  ```
- lens: L4 (structural lint: unused signal absorption)
- 预言机依据:
  1. lc_ctrl.hjson:67-69 声明 "SecVolatileRawUnlockEn parameter must be set to 0 in production"
  2. 代码在 SecVolatileRawUnlockEn=0 分支正确 tie-off 输出，但 unused 信号吸收是否被综合器保留取决于优化级别
  3. 无 SVA 断言验证 strap_en_override_o 在非 volatile-unlock 配置下恒为 0
- 建议验证型: Lint 检查——确认综合后 set_strap_en_override 和 volatile_raw_unlock_success_d 无残留逻辑

---

### CAND-lc_ctrl-006
- 疑点: D[15] 常量的 ECC 注释与脚本计算不一致（comment=0b011011, computed=0b111011，仅 parity bit 差 1 位），虽然 ECC 注释不参与综合，但若由 gen-lc-state-enc.py 重新生成，D[15] 数据值可能需要更新
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_state_pkg.sv:207 (D15 = 16'b1110011000011011, ECC: 6'b011011)
- 代码摘录:
  ```systemverilog
  parameter logic [15:0] D15 = 16'b1110011000011011; // ECC: 6'b011011  ← parity bit may be wrong
  ```
- lens: L5 (constant folding: ECC verification script)
- 预言机依据:
  1. Python 脚本 verify_ecc_hamming.py 计算 D[15] 的 extended Hamming ECC = 0b111011，但 SV 注释为 0b011011
  2. 87/88 个常量的 ECC 注释与脚本一致，仅 D[15] 不一致
  3. 所有 22-bit full word 的 min_hd=6 仍满足约束——数据值本身未被篡改
  4. OTP macro 在运行时独立计算 ECC，注释不影响硬件行为
- 建议验证型: 脚本验证——运行 gen-lc-state-enc.py --seed <seed> 重新生成，对比 D[15] 值

---

### CAND-lc_ctrl-007
- 疑点: LcStTestUnlocked7 分支故意不使能 lc_nvm_debug_en（注释说明"最后一个 TEST_UNLOCKED 态禁用 NVM debug"），但该分支仍使能 lc_dft_en——在 TestUnlocked7 态 DFT 可用但 NVM debug 不可用，此非对称设计是否有意需确认
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_signal_decode.sv:129-136
- 代码摘录:
  ```systemverilog
  LcStTestUnlocked7: begin
    lc_raw_test_rma      = On;
    lc_dft_en            = On;    // ← DFT enabled
    lc_hw_debug_en       = On;
    lc_cpu_en            = On;
    lc_iso_part_sw_wr_en = On;
    // lc_nvm_debug_en NOT set (stays Off)  ← intentional per comment
    lc_keymgr_div_d      = RndCnstLcKeymgrDivTestUnlocked;
  end
  ```
- lens: L3 (tree-in reference: hjson transition desc) + L2 (spec consistency)
- 预言机依据:
  1. 行内注释 (line 127-128) 明确说明 "except for NVM debug en, which is disabled in this state"——设计意图明确
  2. 但 lc_dft_en 仍为 On，允许 DFT 访问但禁止 NVM debug 的组合未被 hjson 显式描述
  3. 无 SEC_CM 声明约束 TestUnlocked7 态的信号组合
- 建议验证型: 代码走查——确认 DFT enable 不隐含 NVM debug enable（两者独立）

---

### CAND-lc_ctrl-008
- 疑点: AllZeroTokenHashed 和 RndCnstRawUnlockTokenHashed 为硬编码 128 位常量，声称是 cSHAKE128("LC_CTRL") 哈希后验值，但树内无可执行脚本验证此映射——需确认这些值确为对应明文的 cSHAKE128 哈希
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_state_pkg.sv:422-426
- 代码摘录:
  ```systemverilog
  parameter lc_token_t AllZeroTokenHashed = {
    128'h3852305BAECF5FF1D5C1D25F6DB9058D
  };
  parameter lc_token_t RndCnstRawUnlockTokenHashed = {
    128'hF8FE11B88C36C8140252F036D23804DB
  };
  ```
- lens: L5 (constant folding: obfuscated hashed token verification)
- 预言机依据:
  1. lc_ctrl_state.hjson:39-47 定义 token_size=128 和两个 token (AllZeroToken="0x0", RndCnstRawUnlockToken="<random>")
  2. lc_ctrl.hjson:676 TOKEN.DIGEST 声明 "tokens are hashed with cSHAKE128, using a custom 'LC_CTRL' prefix"
  3. OT-017/018 教训：LLM 心算混淆常量全错——必须脚本验证，禁止"看起来对"
  4. 树内无独立验证脚本或参考实现可交叉比对
- 建议验证型: Python 脚本——实现 cSHAKE128(LC_CTRL prefix) 并验证 AllZeroTokenHashed = cSHAKE128(0x0...0) 和 RndCnstRawUnlockTokenHashed = cSHAKE128(RndCnstRawUnlockToken)

---

### CAND-lc_ctrl-009
- 疑点: EscalateSt 和 InvalidSt 中 token_hash_req_chk_o 被置 0（允许无 ACK 撤销请求），但 EscalateSt 注释说"okay to de-assert token_hash_req without receiving ACK"，InvalidSt 无此注释——若 InvalidSt 因非 KMAC 原因进入（如 state_invalid_error），KMAC 接口可能处于 mid-transaction 状态，撤销 req 无 ACK 可能导致 KMAC 侧挂起
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv:551-559
- 代码摘录:
  ```systemverilog
  EscalateSt: begin
    token_hash_req_chk_o = 1'b0;   // ← okay per comment
  end
  InvalidSt: begin
    token_hash_req_chk_o = 1'b0;   // ← no comment explaining why this is safe
    state_invalid_error_o = 1'b1;
  end
  ```
- lens: L2 (hjson spec: "all errors are terminal and require a reset cycle") + L6 (error handling)
- 预言机依据:
  1. lc_ctrl.hjson:703 "all errors are terminal and require a reset cycle"——reset 会清 KMAC 接口状态
  2. DataStable_A 断言 (lc_ctrl_kmac_if.sv:47) 仅约束 req&&!ack 时 token 不变，不约束 req 撤销行为
  3. 若 InvalidSt 在 TokenHashSt 期间进入（KMAC 已接收请求），撤销 req 无 ACK 是否导致 KMAC 侧资源泄漏？
- 建议验证型: 时序tb——在 TokenHashSt 中注入 state_invalid_error，观察 KMAC 接口是否正常完成或挂起

---

### CAND-lc_ctrl-010
- 疑点: TRANSITION_CTRL.EXT_CLOCK_EN 寄存器使用 rw1s 语义（set-once sticky），RTL 实现 `use_ext_clock_d |= ...` 符合 rw1s。但 claim_transition_if 使用 SwAccessW0C（write-zero-to-clear），mutex 释放后攻击者可重新 claim——若两个 claim 同时到达（SW + TAP/DMI），TAP 优先但 SW claim 不被拒绝而是保留，下一周期 SW 可能错误获得控制权
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl.sv:426-433
- 代码摘录:
  ```systemverilog
  // TAP/DMI mutex claim.
  if (mubi8_test_false_loose(sw_claim_transition_if_q) &&
      tap_dmi_reg2hw.claim_transition_if.qe) begin
    tap_dmi_claim_transition_if_d = mubi8_t'(tap_dmi_reg2hw.claim_transition_if.q);
  // SW mutex claim.
  end else if (mubi8_test_false_loose(tap_dmi_claim_transition_if_q) &&
      reg2hw.claim_transition_if.qe) begin
    sw_claim_transition_if_d = mubi8_t'(reg2hw.claim_transition_if.q);
  end
  ```
- lens: L4 (structural lint: race condition in mutex) + L2 (hjson: "The REGWEN is governed by hardware")
- 预言机依据:
  1. lc_ctrl.hjson:591-593 "The REGWEN is governed by hardware, and is only set to 1 if the interface mutex has been successfully claimed"
  2. 代码在 SW + TAP 同时 claim 时给 TAP 优先（line 426），但 SW claim 在同周期被丢弃——若 SW 先 claim 成功，TAP 随后 claim，SW 的 claim 不会被自动清除
  3. SwAccessW0C 语义允许 SW 写 0 清除 mutex，但攻击者可在 TAP 持有 mutex 时持续尝试 SW claim
- 建议验证型: 组合micro-tb——同时驱动 SW 和 TAP claim，验证 mutex 互斥性

---

### CAND-lc_ctrl-011
- 疑点: LcStProd 的稀疏编码使用非标准增量写入模式——位置 15 为 A15（而非预期的 B15），在 DEV→PROD 转换路径上位置 15 从 B15 回退到 A15，打破了单调递增的 A→B 转换序列。虽然 hjson 明确定义此模式，但这意味着 PROD 态的 OTP 字 15 需要从 B15 回写到 A15——OTP 宏是否支持这种"回写"操作？
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_state_pkg.sv:306 (LcStProd encoding) + lc_ctrl_state.hjson:70
- 代码摘录:
  ```systemverilog
  // lc_ctrl_state_pkg.sv:306
  LcStProd = {A19, A18, A17, B16, A15, B14, ...}  // pos15=A15, not B15!
  // lc_ctrl_state.hjson:70
  PROD: ['B0',...,'B14','A15','B16','A17','A18','A19']  // pos15=A15
  // Compare DEV:
  LcStDev = {A19, A18, A17, A16, B15, B14, ...}  // pos15=B15
  ```
- lens: L5 (constant folding: encoding structure analysis) + L3 (tree-in reference: hjson PROD definition)
- 预言机依据:
  1. lc_ctrl_state.hjson:70 明确定义 PROD 的字 15 为 A15，与 DEV 的 B15 不同
  2. lc_ctrl_state_pkg.sv 注释 (line 54-65) 声明 "incrementally writeable with respect to the ECC polynomial"——但 A15→B15→A15 不是递增序列
  3. OTP 宏只支持增量写入（1→0 或特定 A→B 转换），回写 B15→A15 可能违反 OTP 编程约束
  4. 然而 DEV→PROD 不是合法转换（TransTokenIdxMatrix 中 DEV 只能转 SCRAP/RMA），所以此回写在正常操作中不会发生
- 建议验证型: 代码走查——确认 TransTokenIdxMatrix 不允许 DEV→PROD 直接转换（已确认：DEV 只能转 SCRAP/RMA）

---

### CAND-lc_ctrl-012
- 疑点: FSM sparse encoding 的 16-bit 常量满足 min_hd=5（lc_ctrl_pkg.sv 注释），但 PRIM_FLOP_SPARSE_FSM 仅检测单 bit 错误——若注入者修改多个 FSM 状态常量使 min_hd < 5，sparse FSM 检测能力下降。需验证当前编码未被篡改
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_pkg.sv:282-298 (fsm_state_e encoding)
- 代码摘录:
  ```systemverilog
  typedef enum logic [FsmStateWidth-1:0] {
    ResetSt       = 16'b1111011010111100,
    IdleSt        = 16'b0000011110101101,
    ...
    InvalidSt     = 16'b0011000101001100
  } fsm_state_e;
  ```
- lens: L5 (constant folding: FSM encoding verification)
- 预言机依据:
  1. lc_ctrl_pkg.sv 注释 (line 253-278) 声明 sparse-fsm-encode.py -d 5 -m 15 -n 16，min_hd=5
  2. SEC_CM MAIN.FSM.SPARSE (lc_ctrl.hjson:645) 声明 FSM 使用 sparse 编码
  3. 需脚本验证 15 个 FSM 状态常量两两 Hamming distance >= 5
- 建议验证型: Python 脚本验证已完成——15 个 FSM 状态 + 4 个 KMAC FSM 状态两两 HD >= 5，编码未被篡改（PASS）

---

### CAND-lc_ctrl-013
- 疑点: KMAC 接口 FSM 的 8-bit sparse encoding 仅 4 个状态，min_hd=5 已满足，但 default 分支设置 kmac_fsm_err_d=1 而 kmac_fsm_err_q 通过 prim_flop_2sync 传递到 token_if_fsm_err_o——sync 延迟意味着 FSM 错误需 2 个额外时钟周期才被主 FSM 感知，此窗口内主 FSM 可能继续执行 token 比较操作
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_kmac_if.sv:110-119 (2sync) + :197-199 (default branch)
- 代码摘录:
  ```systemverilog
  // Line 110-119: 2-sync delay
  prim_flop_2sync #(
    .Width(1), .ResetValue(0)
  ) u_prim_flop_2sync (
    .d_i(kmac_fsm_err_q),
    .q_o(token_if_fsm_err_o)    // ← 2 cycles delayed!
  );
  // Line 197-199: Error detection
  default: begin
    kmac_fsm_err_d = 1'b1;      // ← error set immediately
  end
  ```
- lens: L6 (FSM error handling: delayed error propagation)
- 预言机依据:
  1. SEC_CM MAIN.FSM.LOCAL_ESC (lc_ctrl.hjson:651) 声明 "invalid KMAC interface FSM state → main FSM → InvalidSt"
  2. lc_ctrl_fsm.sv:578 `( |state_invalid_error | token_if_fsm_err_i) → InvalidSt`——但 token_if_fsm_err_i 有 2-sync 延迟
  3. 在延迟窗口内，主 FSM 可能处于 TokenHashSt/TokenCheck0St/TokenCheck1St，继续比较 token——若 KMAC FSM 在此窗口内返回错误数据，token 比较可能误判
  4. DataStable_A (lc_ctrl_kmac_if.sv:47) 不约束 KMAC 返回数据的正确性
- 建议验证型: 时序tb——在 KMAC FSM 进入 default 分支后立即注入 KMAC done+error，观察主 FSM 是否在 2-sync 延迟窗口内完成 token 比较

---

### CAND-lc_ctrl-014
- 疑点: RndCnstInvalidTokens 参数默认值为 `{TokenMuxBits{1'b1}}`（全 1），用于填充无效 token 索引的 mux 位置——若攻击者触发 InvalidTokenIdx 索引，比较的 hashed_token_mux 将为全 1，与任何合法 hashed_token 不匹配，这本身是安全的。但全 1 作为 netlist constant 可能被综合器优化为 VCC，若注入者将其改为全 0（与 AllZeroTokenHashed 相同），则 InvalidTokenIdx 会匹配 ZeroTokenIdx 的 token，绕过无效转换保护
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv:681 (RndCnstInvalidTokens default)
- 代码摘录:
  ```systemverilog
  // lc_ctrl_fsm.sv:681
  {hashed_tokens_lower, hashed_tokens_upper} = RndCnstInvalidTokens;  // default = all-1s
  ```
- lens: L5 (constant folding: netlist constant analysis) + L1 (SEC_CM TOKEN_MUX.CTRL.REDUN)
- 预言机依据:
  1. lc_ctrl_fsm.sv:21 `RndCnstInvalidTokens = {TokenMuxBits{1'b1}}` 默认值
  2. SEC_CM TOKEN_MUX.CTRL.REDUN (lc_ctrl.hjson:679) 声明 token mux 分两半独立索引
  3. 若 RndCnstInvalidTokens 被改为匹配 AllZeroTokenHashed 的模式，无效转换的 token 比较将通过
  4. 但此参数为 top-level parameter，正常配置应使用随机 netlist 常量
- 建议验证型: 脚本验证——确认 RndCnstInvalidTokens 的默认值不与任何合法 token hashed 值重叠
