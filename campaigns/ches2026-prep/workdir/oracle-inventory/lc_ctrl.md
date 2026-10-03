# lc_ctrl 盲预言机目录

## 元信息
- 树: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
- 扫描范围: hw/ip/lc_ctrl/{rtl,data}
- SEC_CM 声明数: 16 / SVA 数: 42 / testplan 条目数: 15

## 一、SEC_CM 声明 ↔ RTL 锚点
| # | SEC_CM 声明 (hjson:line) | RTL 锚点 (file:line) | 检验要点 |
|---|---|---|---|
| 1 | BUS.INTEGRITY (lc_ctrl.hjson:585) | lc_ctrl.sv:155, lc_ctrl.sv:198 | intg_err_o 接到 fatal_bus_integ_error，必须触发 alert_tx_o[2] (fatal_bus_integ_error) |
| 2 | TRANSITION.CONFIG.REGWEN (lc_ctrl.hjson:588) | lc_ctrl.sv:146, lc_ctrl.sv:397, lc_ctrl.sv:406 | REGWEN = lc_idle_d 且仅 mutex 已 claim 后才置 1；FSM 忙时置 0 锁住 transition CSRs |
| 3 | MANUF.STATE.SPARSE (lc_ctrl.hjson:596) | lc_ctrl_state_pkg.sv:96 | lc_state_e 编码满足 min_hw=5, max_hw=17, min_hd=5；所有非 RAW 状态每个 OTP word 非零 |
| 4 | TRANSITION.CTR.SPARSE (lc_ctrl.hjson:608) | lc_ctrl_state_pkg.sv:159 | lc_cnt_e 编码同上约束；所有非 0 状态每个 OTP word 非零 |
| 5 | MANUF.STATE.BKGN_CHK (lc_ctrl.hjson:620) | lc_ctrl_state_decode.sv:97, lc_ctrl_state_decode.sv:131, lc_ctrl_state_decode.sv:149 | 连续解码 lc_state_i、secrets_valid_i；invalid 则 state_invalid_error_o[1/3/5] 置 1 → FSM → InvalidSt |
| 6 | TRANSITION.CTR.BKGN_CHK (lc_ctrl.hjson:627) | lc_ctrl_state_decode.sv:127, lc_ctrl_state_decode.sv:142 | 解码 lc_cnt_i；invalid 则 state_invalid_error_o[2/4] 置 1；非 RAW 且 cnt=0 为 error |
| 7 | STATE.CONFIG.SPARSE (lc_ctrl.hjson:637) | lc_ctrl_state_decode.sv:29, lc_ctrl_state_transition.sv:129, lc_ctrl_state_transition.sv:178, lc_ctrl_fsm.sv:733 | dec_lc_state_o 用 replicated enum（6×5bit）填充 32bit CSR；token_idx 用不同副本索引 |
| 8 | MAIN.FSM.SPARSE (lc_ctrl.hjson:645) | lc_ctrl_pkg.sv:251 | fsm_state_e 16bit sparse 编码，min_hd=5；PRIM_FLOP_SPARSE_FSM 实例化 |
| 9 | KMAC.FSM.SPARSE (lc_ctrl.hjson:648) | lc_ctrl_kmac_if.sv:125 | kmac_if state_e 8bit sparse 编码，min_hd=5；PRIM_FLOP_SPARSE_FSM 实例化 |
| 10 | MAIN.FSM.LOCAL_ESC (lc_ctrl.hjson:651) | lc_ctrl_fsm.sv:573 | state_invalid_error 非 0 或 token_if_fsm_err_i → fsm_state_d=InvalidSt（非 EscalateSt 时） |
| 11 | MAIN.FSM.GLOBAL_ESC (lc_ctrl.hjson:658) | lc_ctrl_fsm.sv:570, lc_ctrl.sv:660 | esc_scrap_state0_i || esc_scrap_state1_i → fsm_state_d=EscalateSt |
| 12 | MAIN.CTRL_FLOW.CONSISTENCY (lc_ctrl.hjson:664) | lc_ctrl_fsm.sv:203 | FSM 只线性前推，无回跳弧；SecCmCFILinear_A 断言 + 4 个 SecCmCFITerminal*_A 断言 |
| 13 | INTERSIG.MUBI (lc_ctrl.hjson:670) | lc_ctrl.sv:88, lc_ctrl.sv:104, lc_ctrl.sv:110 | lc_dft_en_o/lc_hw_debug_en_o/lc_clk_byp_req_o/lc_flash_rma_req_o 用 lc_tx_t (MUBI4) 编码，经 prim_lc_sender 输出 |
| 14 | TOKEN_VALID.CTRL.MUBI (lc_ctrl.hjson:673) | lc_ctrl.sv:85 | test_tokens_valid_i/rma_token_valid_i 来自 OTP，是 lc_tx_t MUBI 编码；经 prim_lc_sync 缓冲后索引 token mux |
| 15 | TOKEN.DIGEST (lc_ctrl.hjson:676) | lc_ctrl.sv:80, lc_ctrl_fsm.sv:447, lc_ctrl_fsm.sv:483, lc_ctrl_fsm.sv:674 | token 经 KMAC cSHAKE128(lc_ctrl) hash；TokenHashSt+TokenCheck0St+TokenCheck1St 三重比较 hashed_token_i[31:0]==hashed_token_mux[31:0] |
| 16 | TOKEN_MUX.CTRL.REDUN (lc_ctrl.hjson:679) | lc_ctrl_fsm.sv:662 | token mux 分 lower/upper 两半，分别用 test_tokens_valid[0]/[1] 和 rma_token_valid[0]/[1] 独立索引 |
| 17 | TOKEN_VALID.MUX.REDUN (lc_ctrl.hjson:685) | lc_ctrl_fsm.sv:710 | token_idx0/idx1 用 dec_lc_state_o[0]/[1] 和 trans_target_i[0]/[1] 不同副本索引；token_idx0!=token_idx1 → trans_invalid_error_o |

## 二、行为性描述句（hjson 原文 → 检验点）
| # | hjson 原文 (file:line) | 检验点 |
|---|---|---|
| 1 | "The REGWEN is governed by hardware, and is only set to 1 if the interface mutex has been successfully claimed." (lc_ctrl.hjson:591-593) | TRANSITION_REGWEN 仅在 mutex claim 成功且 FSM idle 时为 1；lc_ctrl.sv:397/406 赋值 lc_idle_d |
| 2 | "Also, the REGWEN is set to 0 while a state transition is in progress" (lc_ctrl.hjson:593-594) | FSM 非 IdleSt 时 lc_idle_d=0 → REGWEN=0，transition CSRs 不可写 |
| 3 | "If any mismatch is detected, local escalation is triggered (MAIN.FSM.LOCAL_ESC)." (lc_ctrl.hjson:624) | lc_state_decode 的 state_invalid_error_o 非 0 → lc_ctrl_fsm.sv:578 fsm_state_d=InvalidSt |
| 4 | "any non-RAW manufacturing state requires the transition counter to be nonzero" (lc_ctrl.hjson:631-633) | lc_ctrl_state_decode.sv:143: lc_state_i!=LcStRaw && lc_cnt_i==LcCnt0 → state_invalid_error_o[4]=1 |
| 5 | "the transition counter is used to enforce a limit of maximum 24 state transitions" (lc_ctrl.hjson:633-634) | lc_ctrl_state_transition.sv:109: LcCnt24 → trans_cnt_oflw_error_o=1；lc_ctrl_fsm.sv:402 溢出 → PostTransSt |
| 6 | "the main state FSM moves to the InvalidSt state" (lc_ctrl.hjson:655-656) | lc_ctrl_fsm.sv:578-579: state_invalid_error | token_if_fsm_err → InvalidSt |
| 7 | "the main state FSM moves to the EscalateSt state" (lc_ctrl.hjson:661-662) | lc_ctrl_fsm.sv:571: esc_scrap_state0_i || esc_scrap_state1_i → EscalateSt |
| 8 | "the FSM only progresses linearly in one direction. There are no transition arcs that loop back" (lc_ctrl.hjson:667-668) | SecCmCFILinear_A (lc_ctrl_fsm.sv:886) + 4 个 CFI terminal 断言 (lc_ctrl_fsm.sv:865-883) |
| 9 | "Life cycle control signals are multibit encoded." (lc_ctrl.hjson:671) | lc_tx_t = {On=4'b0101, Off=4'b1010}，全部广播经 prim_lc_sender；lc_ctrl_pkg.sv:85 CheckLcTxValsComplementary_A 断言 On==~Off |
| 10 | "tokens are hashed with cSHAKE128, using a custom 'LC_CTRL' prefix" (lc_ctrl.hjson:677) | lc_ctrl_kmac_if.sv 把 transition_token 送 KMAC app 接口；hashed_token_o 用于三重比较 |
| 11 | "all errors are terminal and require a reset cycle" (lc_ctrl.hjson:703 STATUS desc) | lc_ctrl.sv:543-552: error 位用 `q <= d | q` 粘性赋值，一旦置 1 只能 reset 清零 |
| 12 | "This error will move the life cycle state automatically to INVALID" (lc_ctrl.hjson:786-787 STATE_ERROR) | lc_ctrl_fsm.sv:558-559: InvalidSt → state_invalid_error_o=1 |
| 13 | "SecVolatileRawUnlockEn parameter must be set to 0 in production" (lc_ctrl.hjson:67-69) | lc_ctrl_fsm.sv:605-631: if(SecVolatileRawUnlockEn) 才生成 strap 延迟寄存器；else tie-off=0 |

## 三、SVA 清单（行为合同）
| # | 断言 (file:line) | 内容摘要 | 约束的预期行为 |
|---|---|---|---|
| 1 | CheckLcTxValsComplementary_A (lc_ctrl_pkg.sv:85) | On == ~Off | lc_tx_t 编码互补 |
| 2 | LcMuBiWidthCheck_A (lc_ctrl_pkg.sv:87) | $bits(TxWidth) == $bits(MuBi4Width) | lc_tx_t 与 mubi4_t 位宽匹配 |
| 3 | DecLcStateWidthCheck_A (lc_ctrl.sv:133) | CsrLcStateWidth == ExtDecLcStateWidth | CSR 与 RTL 状态宽一致 |
| 4 | DecLcCountWidthCheck_A (lc_ctrl.sv:134) | CsrLcCountWidth == DecLcCountWidth | CSR 与 RTL 计数宽一致 |
| 5 | DecLcIdStateWidthCheck_A (lc_ctrl.sv:135) | CsrLcIdStateWidth == ExtDecLcIdStateWidth | ID state 宽度一致 |
| 6 | NumTokenWordsCheck_A (lc_ctrl.sv:136) | NumTokenWords == LcTokenWidth/32 | token 字数 = 128/32 |
| 7 | OtpTestCtrlWidth_A (lc_ctrl.sv:137) | OtpTestCtrlWidth == CsrOtpTestCtrlWidth | OTP test ctrl 宽度一致 |
| 8 | LcKeymgrDivUnique0_A (lc_ctrl_signal_decode.sv:314) | RndCnstLcKeymgrDivInvalid 不在其他 4 个 div 中 | keymgr 分散值互异 |
| 9 | LcKeymgrDivUnique1_A (lc_ctrl_signal_decode.sv:319) | RndCnstLcKeymgrDivTestUnlocked 不在其他 4 个 div 中 | keymgr 分散值互异 |
| 10 | LcKeymgrDivUnique2_A (lc_ctrl_signal_decode.sv:324) | RndCnstLcKeymgrDivDev 不在其他 4 个 div 中 | keymgr 分散值互异 |
| 11 | LcKeymgrDivUnique3_A (lc_ctrl_signal_decode.sv:329) | RndCnstLcKeymgrDivRma 不在其他 4 个 div 中 | keymgr 分散值互异 |
| 12 | SignalsAreOffWhenNotEnabled_A (lc_ctrl_signal_decode.sv:335) | !lc_state_valid_i → 所有广播信号 == Off, div == Invalid | 状态无效时全部广播关闭 |
| 13 | FsmInScrap_A (lc_ctrl_signal_decode.sv:353) | FSM 在 Scrap/Escalate/Invalid → escalate_en == On | FSM 异常态触发升级 |
| 14 | StateInScrap_A (lc_ctrl_signal_decode.sv:369) | lc_state 无效 + FSM 在活跃态 → escalate_en == On | LC 状态无效触发升级 |
| 15 | LcStateKnown_A (lc_ctrl_fsm.sv:186) | lc_state_q 已知 | FSM 状态寄存器不 X |
| 16 | LcCntKnown_A (lc_ctrl_fsm.sv:187) | lc_cnt_q 已知 | 计数寄存器不 X |
| 17 | FsmStateKnown_A (lc_ctrl_fsm.sv:188) | fsm_state_q 已知 | FSM 寄存器不 X |
| 18 | EscStaysOnOnceAsserted_A (lc_ctrl_fsm.sv:845) | escalate_en 一旦 On 永远 On | 升级信号粘性 |
| 19 | ClkBypStaysOnOnceAsserted_A (lc_ctrl_fsm.sv:850) | clk_byp_req 一旦 On 永远 On | 时钟旁路请求粘性 |
| 20 | FlashRmaStaysOnOnceAsserted_A (lc_ctrl_fsm.sv:855) | flash_rma_req 一旦 On 永远 On | RMA 请求粘性 |
| 21 | NoClkBypInProdStates_A (lc_ctrl_fsm.sv:860) | PROD/PROD_END/DEV 时 clk_byp_req==Off | 生产态不请求外时钟 |
| 22 | SecCmCFITerminal0_A (lc_ctrl_fsm.sv:865) | PostTransSt → 只能留在 PostTrans/Invalid/Escalate | CFI 终态封闭 |
| 23 | SecCmCFITerminal1_A (lc_ctrl_fsm.sv:870) | ScrapSt → 只能留在 Scrap/Invalid/Escalate | CFI 终态封闭 |
| 24 | SecCmCFITerminal2_A (lc_ctrl_fsm.sv:875) | EscalateSt → 只能留在 Escalate | CFI 终态封闭 |
| 25 | SecCmCFITerminal3_A (lc_ctrl_fsm.sv:880) | InvalidSt → 只能留在 Invalid/Escalate | CFI 终态封闭 |
| 26 | SecCmCFILinear_A (lc_ctrl_fsm.sv:886) | FSM 无回跳弧 | CFI 线性前推 |
| 27 | DataStable_A (lc_ctrl_kmac_if.sv:47) | req && !ack → $stable(transition_token_i) | 等 ACK 时 token 不变 |
| 28 | RegsTlOKnown_A (lc_ctrl.sv:832) | regs_tl_o 已知 | regs TL 输出无 X |
| 29 | DmiTlOKnown_A (lc_ctrl.sv:833) | dmi_tl_o 已知 | DMI TL 输出无 X |
| 30 | AlertTxKnown_A (lc_ctrl.sv:834) | alert_tx_o 已知 | Alert 输出无 X |
| 31 | PwrLcKnown_A (lc_ctrl.sv:835) | pwr_lc_o 已知 | Power mgr 输出无 X |
| 32 | LcOtpProgramKnown_A (lc_ctrl.sv:836) | lc_otp_program_o 已知 | OTP program 输出无 X |
| 33 | LcOtpTokenKnown_A (lc_ctrl.sv:837) | kmac_data_o 已知 | KMAC 接口输出无 X |
| 34-42 | LcDftEnKnown_A ... LcKeymgrDiv_A (lc_ctrl.sv:838-853) | 各广播输出已知 | 全部 9 条广播信号无 X |
| 43 | CtrlLcFsmCheck_A (lc_ctrl.sv:856) | FSM sparse error → alert[1] | MAIN.FSM.SPARSE 错误触发 fatal_state_error alert |
| 44 | CtrlLcStateCheck_A (lc_ctrl.sv:858) | State sparse error → alert[1] | MANUF.STATE.SPARSE 错误触发 alert |
| 45 | CtrlLcCntCheck_A (lc_ctrl.sv:864) | Cnt sparse error → alert[1] | TRANSITION.CTR.SPARSE 错误触发 alert |
| 46 | CtrlKmacIfFsmCheck_A (lc_ctrl.sv:870) | KMAC FSM error → alert[1] | KMAC.FSM.SPARSE 错误触发 alert |
| 47 | RegsWeOnehotCheck_A (lc_ctrl.sv:877) | Reg WE onehot error → alert[2] | BUS.INTEGRITY (reg_we) 错误触发 fatal_bus_integ_error alert |
| 48 | TapDmiWeOnehotCheck_A (lc_ctrl.sv:878) | TAP/DMI WE onehot error → alert[2] | BUS.INTEGRITY (TAP reg_we) 错误触发 alert |

## 四、树内参考
| # | 参考物 (绝对路径) | 类型 | 可对比什么 |
|---|---|---|---|
| 1 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/data/lc_ctrl_state.hjson | 规范注释 | 混淆常量 A0-A19/B0-B19/C0-C23/D0-D23 的 Hamming weight/distance 约束；可脚本化验证 |
| 2 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_state_pkg.sv | 参考实现 | A/B/C/D 常量声明，可对比 lc_ctrl_state.hjson 中生成的值 |
| 3 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_signal_decode.sv | 兄弟模块 | signal_decode 的 LcStProd case 在 unique case 中出现两次（行 116 独立 + 行 139-140 合并），潜在重复 case 值风险点 |
| 4 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_state_decode.sv | 兄弟模块 | state_decode 的 unique case 对 lc_state_i / lc_cnt_i / secrets_valid_i 连续检查，可对照 lc_ctrl_fsm 的 error 响应 |
| 5 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_state_transition.sv | 兄弟模块 | transition 合法性 + next state 生成，TransTokenIdxMatrix 可对照 hjson 的 transition desc |
| 6 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_kmac_if.sv | 兄弟模块 | KMAC serialization FSM，sparse 编码与 error 传播路径 |
| 7 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/data/lc_ctrl_sec_cm_testplan.hjson | testplan | 16 条 sec_cm testpoint 对照 hjson countermeasures 一一验证 |

## 五、特殊结构提示

### 1. 重复 case 值风险点
- **lc_ctrl_signal_decode.sv:93 unique case (lc_state_i) 中 LcStProd 出现两次**：
  - 第 116 行：`LcStProd:` 独立分支（与 LcStTestUnlocked0-6 组合），启用 dft_en/nvm_debug_en/hw_debug_en/cpu_en
  - 第 139 行：`LcStProd, LcStProdEnd:` 合并分支，启用 cpu_en/keymgr_en/owner_seed_sw_rw_en
  - 在 `unique case` 中，同一枚举值出现在两个分支属于 **编译错误/仿真未定义行为**。这是已知的 OT-027 类型结构性异常。
  - 检验要点：Lint/Verilator 应报 duplicate case；若 Lint 未捕获则注入者可利用此绕过

### 2. Token 位宽 vs 比较宽度
- Token 为 128bit (LcTokenWidth=128)，但三重比较只比 `hashed_token_i[31:0] == hashed_token_mux[31:0]`（lc_ctrl_fsm.sv:456, :497）
- 高 96bit 不比较——这是设计意图（降低面积），但需确认 hashed_token_mux 低 32bit 碰撞概率可忽略

### 3. 混淆常量必须脚本解码
- lc_ctrl_state_pkg.sv 中 RndCnstRawUnlockTokenHashed = 128'hF8FE11B88C36C8140252F036D23804DB
- AllZeroTokenHashed = 128'h3852305BAECF5FF1D5C1D25F6DB9058D
- 这些是 cSHAKE128 哈希后验值；验证正确性需跑 KMAC 脚本，不能心算

### 4. TRANSITION_CTRL.EXT_CLOCK_EN 的 rw1s 语义
- hjson 声明 swaccess="rw1s"（set-once sticky），即写 1 后不可回写 0
- RTL (lc_ctrl.sv:444/477) 用 `use_ext_clock_d |= ...`，符合 rw1s 语义
- 检验要点：确认 reg_top 生成的 we 逻辑与 rw1s 一致

### 5. SecVolatileRawUnlockEn 编译时门控
- 整个 volatile raw unlock 逻辑被 `if (SecVolatileRawUnlockEn)` 门控
- 生产态该参数=0，相关逻辑全部 tie-off
- 检验要点：确认 gen_no_strap_delay_regs 和 gen_volatile_raw_unlock_const 中 unused 信号吸收完整

### 6. 声明未用端口候选
- lc_ctrl_fsm.sv 输出 lc_check_byp_en_o 仅在 ClkMuxSt 时赋 On，其余态保持 Off
- hjson 中 lc_check_byp_en 存在但无 SEC_CM 声明；需确认下游（OTP check bypass）正确消费
