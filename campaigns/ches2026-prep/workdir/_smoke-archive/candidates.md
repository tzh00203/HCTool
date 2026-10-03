# lc_ctrl 候选漏洞清单

## 覆盖摘要

- **扫描范围**: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/` (12 文件)
- **预言机弹药**: `oracle-inventory/lc_ctrl.md` (17 SEC_CM, 14 行为描述, 45 SVA, 9 树内参考)
- **Lens 产出**:
  - L1 SEC_CM-vs-RTL: 1 条 (CAND-1, LcStProd 信号解码与 SEC_CM 声明矛盾)
  - L2 hjson-spec-vs-RTL: 1 条 (CAND-1, 与 access_signals_table/function_signals_table 矛盾)
  - L3 树内参考对比: 1 条 (CAND-1, 与 doc/lc_ctrl_access_signals_table.md 矛盾)
  - L4 结构 lint: 2 条 (CAND-1 重复 case 项, CAND-2 位宽截断)
  - L5 常量折叠: 0 条 (脚本验证: 所有 21 个 LC state 枚举值唯一, 25 个 counter 枚举值唯一; 16-bit HD <6 但 ECC 位补足, 需 DPI 验证)
  - L6 SCA 结构: 0 条 (lc_ctrl 无密码数据通路)
- **未覆盖区域**: FSM 状态转移矩阵完整遍历 (21×21=441 条边仅抽查关键边); OTP ECC 多项式无法在树内获取, Hamming distance ≥6 声明无法完全脚本验证; RndCnstInvalidTokens 填充正确性需运行时验证

---

### CAND-lc_ctrl-1
- 疑点: `lc_ctrl_signal_decode.sv` 中 `unique case (lc_state_i)` 的 `LcStProd` 出现在两个 case 分支, SystemVerilog first-match-wins 语义导致 PROD 状态按 TEST_UNLOCKED0 权限解码, 完全破坏 PROD/TEST_UNLOCKED 安全边界
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_signal_decode.sv:109-123` (第一次出现, 与 LcStTestUnlocked0..6 同组) 及 `:139-154` (第二次出现, 与 LcStProdEnd 同组, 死代码)
- 代码摘录:
  ```systemverilog
  // Line 109-123: FIRST match — LcStProd gets TEST_UNLOCKED permissions
  LcStTestUnlocked0,
  LcStTestUnlocked1,
  LcStTestUnlocked2,
  LcStTestUnlocked3,
  LcStTestUnlocked4,
  LcStTestUnlocked5,
  LcStTestUnlocked6,
  LcStProd: begin          // <-- LcStProd HERE (first match wins)
    lc_raw_test_rma      = On;
    lc_dft_en            = On;
    lc_nvm_debug_en      = On;
    lc_hw_debug_en       = On;
    lc_cpu_en            = On;
    lc_iso_part_sw_wr_en = On;
    lc_keymgr_div_d      = RndCnstLcKeymgrDivTestUnlocked;
  end
  // Line 139-154: SECOND match — DEAD CODE for LcStProd
  LcStProd,
  LcStProdEnd: begin
    lc_cpu_en              = On;
    lc_keymgr_en           = On;
    lc_owner_seed_sw_rw_en = On;
    lc_iso_part_sw_wr_en   = On;
    lc_iso_part_sw_rd_en   = On;
    lc_keymgr_div_d        = RndCnstLcKeymgrDivProduction;
    lc_creator_seed_sw_rw_en = lc_tx_t'(~secrets_valid_i);
    lc_seed_hw_rd_en = secrets_valid_i;
  end
  ```
- lens: L4 (结构 lint: 重复 case 值) + L1 (SEC_CM INTERSIG.MUBI / TOKEN_VALID.CTRL.MUBI 声明与实际信号矛盾) + L2 (hjson 行为描述矛盾) + L3 (树内参考 doc/lc_ctrl_access_signals_table.md 矛盾)
- 预言机依据:
  1. **结构 lint (L4)**: `unique case` 中 LcStProd 出现两次, 违反 SystemVerilog `unique` 语义要求每个值只出现一次; first-match-wins 使第二次出现为死代码
  2. **SEC_CM INTERSIG.MUBI (L1)**: SEC_CM #13 声明 lc_clk_byp_ack_i/lc_flash_rma_ack_i 使用 MUBI 编码, 但因 LcStProd 解码错误, PROD 状态下 lc_hw_debug_en=On 允许通过 TAP 访问调试功能, 绕过 MUBI 门控的安全检查
  3. **access_signals_table.md (L3)**: 树内参考文档 `doc/lc_ctrl_access_signals_table.md` 明确列出 PROD 应有: CREATOR_SEED_SW_RW_EN=Y*, OWNER_SEED_SW_RW_EN=Y, SEED_HW_RD_EN=Y*, ISO_PART_SW_RD_EN=Y, ISO_PART_SW_WR_EN=Y; 但实际解码给出: CREATOR_SEED_SW_RW_EN=Off, OWNER_SEED_SW_RW_EN=Off, SEED_HW_RD_EN=Off, ISO_PART_SW_RD_EN=Off, ISO_PART_SW_WR_EN=On — 4/5 信号值错误
  4. **function_signals_table.md (L3)**: 树内参考文档 `doc/lc_ctrl_function_signals_table.md` 列出 PROD: NVM_DEBUG_EN=(blank/Off), HW_DEBUG_EN=(blank/Off), KEYMGR_EN=Y*; 实际解码给出: NVM_DEBUG_EN=On, HW_DEBUG_EN=On, KEYMGR_EN=Off — 3 个信号错误
  5. **SVA SignalsAreOffWhenNotEnabled_A (L1)**: `lc_ctrl_signal_decode.sv:335` 断言 `!lc_state_valid_i |=>` 所有输出为 Off; 但此断言不检查 lc_state_valid_i=1 时的具体信号值, 因此不捕获此漏洞
  6. **keymgr_div 唯一性断言 (L1)**: `lc_ctrl_signal_decode.sv:314-329` 的 ASSERT_INIT 保证 4 个 div 值互不相同, 但 PROD 错误地使用 TestUnlocked div 而非 Production div, 导致 keymgr 无法区分 PROD 和 TEST_UNLOCKED 状态
- 安全影响汇总: 在 PROD 生命周期状态下, 攻击者获得: (a) NVM debug enable → 可读 NVM 数据; (b) HW debug enable → 可通过 TAP 访问 CPU 调试; (c) keymgr_div=TestUnlocked → keymgr 使用错误 diversification 值; (d) owner_seed/iso_part_rd/creator_seed 全部关闭 → SW 无法访问生产所需的 seed 和分区
- 建议验证型: 组合 micro-tb — 驱动 lc_state_i=LcStProd + fsm_state_i=IdleSt + lc_state_valid_i=1, 检查 signal_decode 所有输出 vs doc/lc_ctrl_access_signals_table.md + doc/lc_ctrl_function_signals_table.md 预期值; twin 对比: vuln 中 lc_hw_debug_en_o=On, twin 中 lc_hw_debug_en_o=Off

---

### CAND-lc_ctrl-2
- 疑点: Token 比较仅检查 `hashed_token_i[31:0] == hashed_token_mux[31:0]`, 128-bit hashed token 的上 96 位未参与比较, 将暴力破解空间从 2^128 降至 2^32
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv:456` (TokenHashSt) 及 `:497` (TokenCheck0St/TokenCheck1St)
- 代码摘录:
  ```systemverilog
  // Line 456-458: TokenHashSt — only [31:0] compared
  if (hashed_token_i[31:0] == hashed_token_mux[31:0] &&
      !token_hash_err_i &&
      &hashed_token_valid_mux) begin
    fsm_state_d = FlashRmaSt;
  end

  // Line 497-499: TokenCheck0St/TokenCheck1St — same truncation
  if (hashed_token_i[31:0] == hashed_token_mux[31:0] &&
      !token_hash_err_i &&
      &hashed_token_valid_mux) begin
  ```
- lens: L4 (结构 lint: 比较位宽截断) + L1 (SEC_CM TOKEN.DIGEST 声明与实现矛盾)
- 预言机依据:
  1. **SEC_CM TOKEN.DIGEST (L1)**: SEC_CM #15 声明 token 经 KMAC cSHAKE128 哈希后做三次比较; hjson sec_cm_testplan 明确说 "hashed token is checked three times overall in TokenHashSt, TokenCheck0St and TokenCheck1St" — 暗示全 128 位比较, 但实际仅比较低 32 位
  2. **LcTokenWidth=128 (L1)**: `lc_ctrl_state_pkg.sv:412` 声明 `LcTokenWidth = 128`, token 为 128-bit; `hashed_token_i` 和 `hashed_token_mux` 均为 `lc_token_t` (128-bit), 但比较仅使用 `[31:0]` 切片
  3. **NumTokenWords=4 (L1)**: `lc_ctrl_reg_pkg.sv:13` 声明 `NumTokenWords = 4` (4×32=128 bit), ASSERT_INIT `NumTokenWordsCheck_A` 验证 `NumTokenWords == LcTokenWidth/32` — 确认 token 应为 128 bit 全宽比较
  4. **KMAC 接口返回 128-bit hash (L1)**: `lc_ctrl_kmac_if.sv:75` 截取 `digest_share0[LcTokenWidth-1:0] ^ digest_share1[LcTokenWidth-1:0]` 得到完整 128-bit hash, 但 FSM 仅使用低 32 位
  5. **GT 先例 OT-013 (L4)**: 知识库 `vuln-patterns/rtl/width-truncation/PATTERN.md` 记录 OT-013 为 lc_ctrl token 截断至 [31:0] 的 GT 实例, 与此发现完全一致
- 安全影响: 攻击者仅需猜测/暴力破解 32-bit token 低半部分即可通过 token 检查, 使生命週期转换 (如 TEST_UNLOCKED→PROD, DEV→RMA) 的 token 保护失效; 2^32 ≈ 4.3×10^9 次尝试在硬件上可行
- 建议验证型: micro-tb — 构造两个 128-bit token, 仅低 32 位相同、高 96 位不同; vuln 接受 (FSM 进入 FlashRmaSt), twin 拒绝 (FSM 进入 PostTransSt + token_invalid_error_o=1)

---

### CAND-lc_ctrl-3
- 疑点: `lc_ctrl_fsm.sv` IdleSt 中 LcStProd 被包含在 clk_byp_req 允许列表, 但 ClkMuxSt 中 PROD 不在 ext_clock 允许列表, 且 SVA `NoClkBypInProdStates_A` 断言 PROD/PROD_END/DEV 状态下 lc_clk_byp_req_o==Off — 代码与断言矛盾
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv:335-353` (IdleSt clk_byp_req 列表) 及 `:369-396` (ClkMuxSt ext_clock 列表) 及 `:860-863` (NoClkBypInProdStates_A 断言)
- 代码摘录:
  ```systemverilog
  // Line 335-353: IdleSt — LcStProd included in clk_byp_req list
  if (lc_state_q inside {LcStRaw,
                         LcStTestLocked0, ..., LcStTestLocked6,
                         LcStTestUnlocked0, ..., LcStTestUnlocked7,
                         LcStDev,
                         LcStProd,    // <-- PROD can request ext clock
                         LcStRma}) begin
    if (use_ext_clock_i) begin
      lc_clk_byp_req = On;
    end
  end

  // Line 369-385: ClkMuxSt — LcStProd NOT in ext_clock list
  if (lc_state_q inside {LcStRaw,
                         LcStTestLocked0, ..., LcStTestLocked6,
                         LcStTestUnlocked0, ..., LcStTestUnlocked7,
                         LcStRma}) begin  // <-- No LcStProd here!
    ...
  end else begin
    fsm_state_d = CntIncrSt;  // PROD skips directly
  end

  // Line 860-863: SVA contradicts IdleSt code
  `ASSERT(NoClkBypInProdStates_A,
      lc_state_q inside {LcStProd, LcStProdEnd, LcStDev}
      |=>
      lc_clk_byp_req_o == Off)
  ```
- lens: L4 (结构 lint: 代码与 SVA 断言矛盾) + L2 (hjson 行为描述矛盾)
- 预言机依据:
  1. **SVA NoClkBypInProdStates_A (L4)**: `lc_ctrl_fsm.sv:860-863` 断言 PROD/PROD_END/DEV 状态下 lc_clk_byp_req_o==Off, 但 IdleSt 代码允许 PROD 设置 lc_clk_byp_req=On (当 use_ext_clock_i=1), 经 prim_lc_sender 寄存后 lc_clk_byp_req_o=On, 直接违反此断言
  2. **ClkMuxSt 不等待 ack (L4)**: PROD 在 ClkMuxSt 走 else 分支直接进 CntIncrSt, 不等待 clock manager 的 ack, 说明 PROD 不应使用 ext clock — 与 IdleSt 允许 PROD 请求 ext clock 矛盾
  3. **hjson "volatile RAW UNLOCK" 描述 (L2)**: hjson 说 ext_clock_en 仅用于 RAW/TEST*/RMA 状态的转换, 但 IdleSt 代码允许 PROD 使用
- 安全影响: [minor] 若断言被注入者删除或弱化, PROD 状态下 SW 可设置 ext_clock_en=1 并在转换期间请求外部时钟, 可能干扰时钟切换逻辑; 若断言保留, 则存在 code-assertion 不一致, Formal verification 会报 violation
- 建议验证型: SVA 检查 — 在 Formal 工具中运行 `NoClkBypInProdStates_A`, 若代码保留 IdleSt 中 LcStProd 的 ext_clock 允许, 断言会 FAIL; micro-tb: 置 lc_state_q=LcStProd, use_ext_clock_i=1, 检查 lc_clk_byp_req_o 是否为 On

---

### CAND-lc_ctrl-4
- 疑点: `lc_ctrl_state_pkg.sv` 中 LcStProd 编码使用 `{A19, A18, A17, B16, A15, B14, ...}`, 注意位置 3 为 B16 而位置 4 为 A15 — 这打破了标准递增写入模式 (通常连续位置应从 A 切换到 B 且不回退), 需验证此编码是否与 gen-lc-state-enc.py 生成模板一致
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_state_pkg.sv:306`
- 代码摘录:
  ```systemverilog
  LcStProd = {A19, A18, A17, B16, A15, B14, B13, B12, B11, B10,
              B9, B8, B7, B6, B5, B4, B3, B2, B1, B0}
  // Note: position 3 = B16, position 4 = A15
  // This is NON-MONOTONE: B16 then A15 (B→A transition)
  // Compare LcStDev:
  LcStDev = {A19, A18, A17, A16, B15, B14, ...}  // A16→B15 (A→B, monotone)
  // Compare LcStProdEnd:
  LcStProdEnd = {A19, A18, B17, A16, A15, B14, ...}  // B17→A16→A15 (B→A→A)
  ```
- lens: L5 (常量折叠: 编码模式异常) + L3 (树内参考: lc_ctrl_encoding_table.md)
- 预言机依据:
  1. **递增写入模式 (L3)**: 所有其他 LC state 编码遵循单调递增写入模式 — 从高位到低位, 值从 A 切换到 B 后不再回退到 A; LcStProd 的 B16→A15 是唯一违反此规则的编码
  2. **gen-lc-state-enc.py 模板 (L3)**: 树内参考 `lc_ctrl_state_pkg.sv.tpl` 是生成模板, 需用相同种子重新运行 gen-lc-state-enc.py 验证 LcStProd 编码是否匹配; 若不匹配则为注入篡改
  3. **OTP ECC 写入顺序 (L5)**: 递增写入要求新状态只能翻转 OTP 中尚未从 A→B 翻转的位置; B16→A15 意味着 LcStProd 相比 LcStDev 翻转了位置 3 (A16→B16) 但位置 4 保持 A15, 然后到 LcStProdEnd 又翻转位置 2 (A17→B17) 和位置 3 回退 (B16→A16), 此回退在 OTP ECC 物理上是否可实现取决于 ECC 多项式
- 安全影响: [minor] 若 LcStProd 编码被篡改 (不匹配生成脚本输出), 则 OTP 编程时可能写入非法编码值, 导致 state_invalid_error 触发或 LC 状态损坏; 若编码正确 (生成脚本确实产生此非单调模式), 则无安全影响
- 建议验证型: 脚本 — 运行 `gen-lc-state-enc.py --seed 40182201019264397688411770949626922549663256047001778394918990008320537410392`, 对比输出与 lc_ctrl_state_pkg.sv 中 LcStProd/LcStProdEnd 编码 bit-exact

---

### CAND-lc_ctrl-5
- 疑点: `lc_ctrl_fsm.sv` 中 `state_invalid_error_o` 在 FSM default 分支 (line 564) 和 InvalidSt (line 559) 被设置为 1'b1, 但 LOCAL_ESC 检查 (line 578) 的条件是 `(|state_invalid_error | token_if_fsm_err_i) && (fsm_state_q != EscalateSt)`, 当 FSM 已进入 InvalidSt 时 state_invalid_error_o=1 会再次触发, 但 InvalidSt 内部已设 state_invalid_error_o=1, 形成自我确认环 — 需确认 InvalidSt 下的 state_invalid_error 是否能正确传播到 lc_ctrl.sv 的 fatal_state_error_q
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv:556-580`
- 代码摘录:
  ```systemverilog
  InvalidSt: begin
    token_hash_req_chk_o = 1'b0;
    state_invalid_error_o = 1'b1;  // Set in InvalidSt
  end
  default: begin
    fsm_state_d = InvalidSt;
    state_invalid_error_o = 1'b1;  // Set in default
  end
  // LOCAL_ESC check (after case):
  end else if ((|state_invalid_error | token_if_fsm_err_i) &&
               (fsm_state_q != EscalateSt)) begin
    fsm_state_d = InvalidSt;
    state_invalid_error_o = 1'b1;
  end
  ```
- lens: L1 (SEC_CM MAIN.FSM.LOCAL_ESC 语义验证)
- 预言机依据:
  1. **SEC_CM MAIN.FSM.LOCAL_ESC (L1)**: SEC_CM #10 声明 "state_invalid_error 或 token_if_fsm_err 非零且 FSM 非 EscalateSt → fsm_state_d=InvalidSt"; 代码实现与此一致, 但需验证 state_invalid_error 在 InvalidSt 下是否持续为 1 以保持 fatal_state_error_q 粘性置位
  2. **SVA CtrlLcStateCheck_A (L1)**: `lc_ctrl.sv:858-863` 断言 sparse FSM 错误触发 alert[1], 其 disabling 条件包含 `fsm_state_q inside {ResetSt, EscalateSt, PostTransSt, InvalidSt, ScrapSt}` — InvalidSt 被排除, 意味着在 InvalidSt 下此断言不检查 alert, 但 state_invalid_error 仍应为 1
  3. **hjson "all errors are terminal" (L2)**: hjson 行为描述 #1 声明所有 error 位一旦置 1 只能复位清零; lc_ctrl.sv:548 `fatal_state_error_q <= state_invalid_error_d | fatal_state_error_q` 为自或逻辑, 满足粘性要求 — state_invalid_error_d=1 时 fatal_state_error_q 锁定为 1
- 安全影响: [minor] 验证确认: state_invalid_error_o 在 InvalidSt 下持续为 1, 通过 lc_ctrl.sv:807 连接到 state_invalid_error_d, 再通过粘性位 fatal_state_error_q 驱动 alert[1]; 传播链完整, 无漏洞; 但若注入者将 InvalidSt 中的 `state_invalid_error_o = 1'b1` 改为 `state_invalid_error_o = 1'b0`, 则 error 不传播, alert 不触发 — 这是一个单行修改即可破坏的脆弱点
- 建议验证型: micro-tb — 置 fsm_state_q=InvalidSt, 检查 state_invalid_error_o==1; 检查 fatal_state_error_q 在下一周期为 1; 检查 alert_tx_o[1] 拉起

---

### CAND-lc_ctrl-6
- 疑点: `lc_ctrl_fsm.sv` 中 `hashed_token_valid_mux` 为 2-bit 信号, 由 `hashed_tokens_valid0[token_idx0]` 和 `hashed_tokens_valid1[token_idx1]` 独立索引; 当 token_idx0≠token_idx1 时 `trans_invalid_error_o` 已触发, 但若两索引恰好指向同一 valid 值 (如 ZeroTokenIdx), 则 `&hashed_token_valid_mux` 通过而 `trans_invalid_error_o` 也触发 — FSM 先检查 trans_invalid_error_o 再检查 token, 需确认错误优先级正确
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv:746-753`
- 代码摘录:
  ```systemverilog
  assign hashed_token_valid_mux = {hashed_tokens_valid0[token_idx0],
                                   hashed_tokens_valid1[token_idx1]};
  // trans_invalid_error_o includes index mismatch:
  assign trans_invalid_error_o = trans_invalid_error || (token_idx0 != token_idx1);
  // In TokenCheck0St/TokenCheck1St, trans_invalid_error_o checked FIRST:
  if (trans_invalid_error_o) begin
    fsm_state_d = PostTransSt;  // Error takes priority
  end else begin
    // Then token comparison...
  end
  ```
- lens: L1 (SEC_CM TOKEN_MUX.CTRL.REDUN / TOKEN_VALID.MUX.REDUN 语义验证)
- 预言机依据:
  1. **SEC_CM TOKEN_MUX.CTRL.REDUN (L1)**: SEC_CM #16 声明 "token_idx0≠idx1→TRANSITION_ERROR"; 代码 `trans_invalid_error_o = trans_invalid_error || (token_idx0 != token_idx1)` 正确实现
  2. **SEC_CM TOKEN_VALID.MUX.REDUN (L1)**: SEC_CM #17 声明两份 valid 信号独立驱动, 不一致→TRANSITION_ERROR; 代码 hashed_tokens_valid0/valid1 分别使用 test_tokens_valid[4]/[5] 和 [6]/[7] 以及 rma_token_valid[2]/[3], 确实独立
  3. **错误优先级 (L1)**: TokenCheck0St/TokenCheck1St 中 trans_invalid_error_o 检查在 token 比较之前, 确保索引不一致时直接进 PostTransSt 而非继续 token 比较; TokenHashSt 中无 trans_invalid_error_o 检查, 但 TokenHashSt 后必定经过 TokenCheck0St/1St 会再次检查
- 安全影响: [minor] 验证确认错误优先级正确 — trans_invalid_error_o 在 TokenCheck0St/1St 中优先于 token 比较; TokenHashSt 中无此检查但后续状态会捕获; 无独立漏洞, 但若注入者删除 TokenCheck0St 中的 trans_invalid_error_o 检查, 则索引不一致的 token 可能通过 — 单点脆弱
- 建议验证型: micro-tb — 置 token_idx0≠token_idx1, 驱动 FSM 至 TokenCheck0St, 验证 fsm_state_d=PostTransSt 且 trans_invalid_error_o=1

---

### CAND-lc_ctrl-7
- 疑点: `lc_ctrl_kmac_if.sv` 的 KMAC FSM (FirstSt→SecondSt→WaitSt→DoneSt) 在 DoneSt 为终态无出弧, 但 default 分支仅设置 `kmac_fsm_err_d = 1'b1` 而不主动将 FSM 转到安全状态 — 错误信号需经 2-sync (`u_prim_flop_2sync`) 传播到 LC 域的 `token_if_fsm_err_o`, 再由 FSM 的 LOCAL_ESC 检查捕获; 需验证 2-sync 延迟期间 KMAC 侧 FSM 是否可能被再次触发
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_kmac_if.sv:197-199` 及 `:110-119`
- 代码摘录:
  ```systemverilog
  // Line 197-199: KMAC FSM default branch
  default: begin
    kmac_fsm_err_d = 1'b1;  // Error flag set, but FSM stays in illegal state
  end

  // Line 110-119: 2-sync propagation to LC domain
  prim_flop_2sync #(
    .Width(1),
    .ResetValue(0)
  ) u_prim_flop_2sync (
    .d_i(kmac_fsm_err_q),   // KMAC-side registered error
    .q_o(token_if_fsm_err_o) // LC-side error (2 cycles delayed)
  );
  ```
- lens: L1 (SEC_CM KMAC.FSM.SPARSE 语义验证) + L4 (FSM 错误处理)
- 预言机依据:
  1. **SEC_CM KMAC.FSM.SPARSE (L1)**: SEC_CM #9 声明 kmac_if FSM 使用 sparse 编码, 非法态触发 token_if_fsm_err; 代码实现 sparse FSM (`PRIM_FLOP_SPARSE_FSM` at line 203) 且 default 分支设置 kmac_fsm_err_d=1
  2. **2-sync 延迟 (L4)**: 错误信号从 KMAC 时钟域传播到 LC 时钟域需 2 个 KMAC 时钟周期; 在此延迟期间, KMAC FSM 停留在非法 sparse 编码值, `kmac_data_o` 输出保持默认 ('0), 不会发送额外数据到 KMAC
  3. **LOCAL_ESC 捕获 (L1)**: `lc_ctrl_fsm.sv:578` 的 LOCAL_ESC 检查包含 `token_if_fsm_err_i`, 一旦 2-sync 传播完成, LC FSM 进入 InvalidSt
  4. **PRIM_FLOP_SPARSE_FSM (L1)**: sparse FSM 寄存器在非法编码值时自动输出 error, 与 kmac_fsm_err_d 共同确保错误被检测
- 安全影响: [minor] 验证确认: KMAC FSM 错误通过 2-sync 传播到 LC FSM 的 LOCAL_ESC, 延迟期间 KMAC 接口输出全零 (安全默认), 无数据泄露; 但若注入者删除 `kmac_fsm_err_d = 1'b1` (改为 0), 则 KMAC FSM 非法态不报告错误, LOCAL_ESC 不触发 — 单点脆弱
- 建议验证型: 时序 tb — 注入 KMAC FSM 非法态, 计数 2-sync 延迟周期, 验证 token_if_fsm_err_o 在 2 周期后拉起; 验证 LC FSM 在随后 1 周期进入 InvalidSt; SVA 检查 CtrlKmacIfFsmCheck_A
