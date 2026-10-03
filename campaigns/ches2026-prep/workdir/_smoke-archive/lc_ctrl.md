# lc_ctrl 盲预言机目录

## 元信息
- 树: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
- 扫描范围: hw/ip/lc_ctrl/{rtl,data,doc}
- SEC_CM 声明数: 17 / SVA 数: 37 / testplan 条目数: 17(sec_cm) + 12(func) = 29

## 一、SEC_CM 声明 ↔ RTL 锚点
| # | SEC_CM 声明 (hjson:line) | RTL 锚点 (file:line) | 检验要点 |
|---|---|---|---|
| 1 | BUS.INTEGRITY (lc_ctrl.hjson:586) | lc_ctrl.sv:155, lc_ctrl.sv:198 `// SEC_CM: BUS.INTEGRITY` | TL-UL integrity 错误触发 fatal_bus_integ_error 粘性位（lc_ctrl.sv:550-552），alert_tx_o[2] 拉起 |
| 2 | TRANSITION.CONFIG.REGWEN (lc_ctrl.hjson:589) | lc_ctrl.sv:146, lc_ctrl.sv:397, lc_ctrl.sv:406 `// SEC_CM: TRANSITION.CONFIG.REGWEN` | transition_regwen 在 mutex 未 claim 或 FSM 非 IdleSt 时为 0；transition_cmd/transition_target/transition_token 仅在 regwen=1 可写 |
| 3 | MANUF.STATE.SPARSE (lc_ctrl.hjson:597) | lc_ctrl_state_pkg.sv:96 `// SEC_CM: MANUF.STATE.SPARSE` | A0-B19 共 20 组 16bit 值，Hamming dist≥6；gen-lc-state-enc.py 种子可重算验证 |
| 4 | TRANSITION.CTR.SPARSE (lc_ctrl.hjson:609) | lc_ctrl_state_pkg.sv:159 `// SEC_CM: TRANSITION.CTR.SPARSE` | C0-D23 共 24 组 16bit 值，同上种子可重算验证 |
| 5 | MANUF.STATE.BKGN_CHK (lc_ctrl.hjson:621) | lc_ctrl_state_decode.sv:97, lc_ctrl_state_decode.sv:131, lc_ctrl_state_decode.sv:149 `// SEC_CM: MANUF.STATE.BKGN_CHK` | (1) lc_state_i 非法编码→state_invalid_error_o[1]=1; (2) secrets_valid_i 非 On/Off→state_invalid_error_o[3]=1; (3) secrets_valid=On 但 lc_state 在 test/raw→state_invalid_error_o[5]=1 |
| 6 | TRANSITION.CTR.BKGN_CHK (lc_ctrl.hjson:628) | lc_ctrl_state_decode.sv:127, lc_ctrl_state_decode.sv:142 `// SEC_CM: TRANSITION.CTR.BKGN_CHK` | (1) lc_cnt_i 非法编码→state_invalid_error_o[2]=1; (2) 非 Raw 且 lc_cnt==LcCnt0→state_invalid_error_o[4]=1 |
| 7 | STATE.CONFIG.SPARSE (lc_ctrl.hjson:638) | lc_ctrl_state_decode.sv:29, lc_ctrl_state_transition.sv:129, lc_ctrl_state_transition.sv:178, lc_ctrl_fsm.sv:733 `// SEC_CM: STATE.CONFIG.SPARSE` | dec_lc_state 使用 DecLcStateNumRep=6 次冗余复制填充 30bit；prim_sec_anchor_buf 缓冲解码结果 |
| 8 | MAIN.FSM.SPARSE (lc_ctrl.hjson:646) | lc_ctrl_pkg.sv:251 `// SEC_CM: MAIN.FSM.SPARSE` | `PRIM_FLOP_SPARSE_FSM` 实例化（lc_ctrl_fsm.sv:588），fsm_state_e 用 sparse 编码 |
| 9 | KMAC.FSM.SPARSE (lc_ctrl.hjson:649) | lc_ctrl_kmac_if.sv:125 `// SEC_CM: KMAC.FSM.SPARSE` | kmac_if 内部 FSM 用 sparse 编码；非法态触发 token_if_fsm_err |
| 10 | MAIN.FSM.LOCAL_ESC (lc_ctrl.hjson:652) | lc_ctrl_fsm.sv:573 `// SEC_CM: MAIN.FSM.LOCAL_ESC` | state_invalid_error 或 token_if_fsm_err 非零且 FSM 非 EscalateSt→fsm_state_d=InvalidSt（lc_ctrl_fsm.sv:578-579） |
| 11 | MAIN.FSM.GLOBAL_ESC (lc_ctrl.hjson:660) | lc_ctrl_fsm.sv:570, lc_ctrl.sv:660 `// SEC_CM: MAIN.FSM.GLOBAL_ESC` | esc_scrap_state0/1_tx 断言→fsm_state_d=EscalateSt；lc_escalate_en 永久拉起为 On |
| 12 | MAIN.CTRL_FLOW.CONSISTENCY (lc_ctrl.hjson:665) | lc_ctrl_fsm.sv:203 `// SEC_CM: MAIN.CTRL_FLOW.CONSISTENCY` | `ASSERT_FPV_LINEAR_FSM(SecCmCFILinear_A, fsm_state_q, fsm_state_e)` 在 lc_ctrl_fsm.sv:886 验证 FSM 只前进不回退 |
| 13 | INTERSIG.MUBI (lc_ctrl.hjson:671) | lc_ctrl.sv:88, lc_ctrl.sv:104, lc_ctrl.sv:110 `// SEC_CM: INTERSIG.MUBI` | lc_clk_byp_ack_i、lc_flash_rma_ack_i 用 lc_tx_t (4bit MUBI)；不一致值触发 OTP_ERROR / FLASH_RMA_ERROR |
| 14 | TOKEN_VALID.CTRL.MUBI (lc_ctrl.hjson:675) | lc_ctrl.sv:85 `// SEC_CM: TOKEN_VALID.CTRL.MUBI` | test_tokens_valid / rma_token_valid 从 OTP 读入为 lc_tx_t；`lc_tx_test_true_strict` 判断有效性 |
| 15 | TOKEN.DIGEST (lc_ctrl.hjson:679) | lc_ctrl.sv:80, lc_ctrl_fsm.sv:447, lc_ctrl_fsm.sv:483, lc_ctrl_fsm.sv:674 `// SEC_CM: TOKEN.DIGEST` | token 经 KMAC cSHAKE128(LC_CTRL prefix) 哈希；TokenHashSt→TokenCheck0St→TokenCheck1St 三次比较（lc_ctrl_fsm.sv:456,497） |
| 16 | TOKEN_MUX.CTRL.REDUN (lc_ctrl.hjson:681) | lc_ctrl_fsm.sv:662 `// SEC_CM: TOKEN_MUX.CTRL.REDUN` | token mux 分 upper/lower 两半，分别用 token_idx0/token_idx1 索引；idx0≠idx1→TRANSITION_ERROR |
| 17 | TOKEN_VALID.MUX.REDUN (lc_ctrl.hjson:686) | lc_ctrl_fsm.sv:710 `// SEC_CM: TOKEN_VALID.MUX.REDUN` | hashed_tokens_valid0/valid1 分别由独立 OTP token_valid 位驱动（lc_ctrl_fsm.sv:716-730）；不一致或 valid≠1→TRANSITION_ERROR |

## 二、行为性描述句（hjson 原文 → 检验点）
| # | hjson 原文 (file:line) | 检验点 |
|---|---|---|
| 1 | "all errors are terminal and require a reset cycle" (lc_ctrl.hjson:704) | STATUS 各 error 位一旦置 1，只能靠 rst_ni 复位清零；检查 fatal_*_error_q 赋值逻辑是否有清零路径（lc_ctrl.sv:547-552 无清零，仅 reset 分支 lc_ctrl.sv:518-525 清零） |
| 2 | "This alert triggers if an error occurred during an OTP programming operation." (lc_ctrl.hjson:42) | fatal_prog_error_q 粘性置位由 otp_prog_error_d 触发（lc_ctrl.sv:547），驱动 alert_tx_o[0] |
| 3 | "This alert triggers if an error in the life cycle state or life cycle controller FSM is detected." (lc_ctrl.hjson:45) | fatal_state_error_q 粘性置位由 state_invalid_error_d 触发（lc_ctrl.sv:548），驱动 alert_tx_o[1] |
| 4 | "Disable (0) or enable (1) volatile RAW UNLOCK capability... must be set to 0 in production" (lc_ctrl.hjson:61-69) | SecVolatileRawUnlockEn=0 时，VOLATILE_RAW_UNLOCK CSR 写 1 读回 0；volatile_raw_unlock_success_q 固定为 MuBi8False（lc_ctrl_fsm.sv:630） |
| 5 | "The life cycle controller allows up to 24 transition attempts" (lc_ctrl.hjson:1257) | dec_lc_cnt_o==24 时 LC_STATE 读为 SCRAP；TRANSITION_COUNT_ERROR 位置 1 |
| 6 | "transition into RMA is not possible from this state" (PROD_END, lc_ctrl.hjson:1064) | FSM 在 lc_state==LcStProdEnd 且 trans_target==DecLcStRma 时必须走 TOKEN_ERROR/TRANSITION_ERROR 路径 |
| 7 | "SCRAP is a final state" (lc_ctrl.hjson:549-553) | 进入 ScrapSt 后 FSM 无出弧（lc_ctrl_fsm.sv case ScrapSt 内仅有自环） |
| 8 | "the life cycle can be reverted to the configured state by performing a hard reset" (LOGICAL_SCRAP, lc_ctrl.hjson:579) | EscalateSt 为临时态，复位后从 OTP 重新加载 lc_state |
| 9 | "lc_clk_byp_ack_i inconsistent ... causes an OTP_ERROR" (sec_cm_testplan.hjson:170-180) | 未请求 ext_clk 时 ack≠Off→OTP_ERROR；请求 ext_clk 后在 ClkMuxSt 之后 ack≠On→OTP_ERROR |
| 10 | "lc_flash_rma_ack_i inconsistent ... causes a FLASH_RMA_ERROR" (sec_cm_testplan.hjson:182-190) | 未请求 RMA 时 ack≠Off→FLASH_RMA_ERROR；请求 RMA 后在 FlashRmaSt 之后 ack≠On→FLASH_RMA_ERROR |
| 11 | "token valid signals ... any value other than 'ON' will lead to a TOKEN_ERROR" (sec_cm_testplan.hjson:201-207) | 对 conditional transition，hashed_token_valid_mux 中任一 bit 为 0（即 token valid 非 On）→TOKEN_ERROR，FSM 不进 TransProgSt |
| 12 | "hashed token is checked three times overall in TokenHashSt, TokenCheck0St and TokenCheck1St" (sec_cm_testplan.hjson:228-230) | lc_ctrl_fsm.sv:456 TokenCheck0St 比较、lc_ctrl_fsm.sv:497 TokenCheck1St 比较均需与 TokenHashSt 哈希一致 |
| 13 | "token mux index inconsistency ... leads to TRANSITION_ERROR" (sec_cm_testplan.hjson:240-247) | token_idx0≠token_idx1→TRANSITION_ERROR，FSM 不进 TransProgSt |
| 14 | "values will be gated to zero ... in all other states" (OTP_VENDOR_TEST_CTRL, lc_ctrl.hjson:1086) | lc_state 非 RAW/TEST_*/RMA 时，otp_vendor_test_ctrl 输出被门控为零 |

## 三、SVA 清单（行为合同）
| # | 断言 (file:line) | 内容摘要 | 约束的预期行为 |
|---|---|---|---|
| 1 | `ASSERT_KNOWN(LcStateKnown_A, lc_state_q)` (lc_ctrl_fsm.sv:186) | lc_state_q 不能含 X/Z | FSM 寄存器初始化完整性 |
| 2 | `ASSERT_KNOWN(LcCntKnown_A, lc_cnt_q)` (lc_ctrl_fsm.sv:187) | lc_cnt_q 不能含 X/Z | 计数器初始化完整性 |
| 3 | `ASSERT_KNOWN(FsmStateKnown_A, fsm_state_q)` (lc_ctrl_fsm.sv:188) | fsm_state_q 不能含 X/Z | FSM 状态初始化完整性 |
| 4 | `ASSERT_FPV_LINEAR_FSM(SecCmCFILinear_A, fsm_state_q, fsm_state_e)` (lc_ctrl_fsm.sv:886) | FSM 状态只前进不回退 | MAIN.CTRL_FLOW.CONSISTENCY 兑现 |
| 5 | `ASSERT_STATIC_IN_PACKAGE(CheckLcTxValsComplementary_A, On==~Off)` (lc_ctrl_pkg.sv:85) | lc_tx_t On/Off 互为按位取反 | MUBI 编码正确性 |
| 6 | `ASSERT_STATIC_IN_PACKAGE(LcMuBiWidthCheck_A, $bits(TxWidth)==$bits(MuBi4Width))` (lc_ctrl_pkg.sv:87) | lc_tx_t 宽度=4 与 MuBi4 一致 | 类型转换安全 |
| 7 | `ASSERT_INIT(LcKeymgrDivUnique0_A, ...)` (lc_ctrl_signal_decode.sv:314) | RndCnstLcKeymgrDivInvalid 与其余四个 div 值互不相同 | keymgr diversification 值唯一性 |
| 8 | `ASSERT_INIT(LcKeymgrDivUnique1_A, ...)` (lc_ctrl_signal_decode.sv:319) | RndCnstLcKeymgrDivTestUnlocked 与其余互不相同 | 同上 |
| 9 | `ASSERT_INIT(LcKeymgrDivUnique2_A, ...)` (lc_ctrl_signal_decode.sv:324) | RndCnstLcKeymgrDivDev 与其余互不相同 | 同上 |
| 10 | `ASSERT_INIT(LcKeymgrDivUnique3_A, ...)` (lc_ctrl_signal_decode.sv:329) | RndCnstLcKeymgrDivRma 与其余互不相同 | 同上 |
| 11 | `ASSERT_INIT(DecLcStateWidthCheck_A, CsrLcStateWidth==ExtDecLcStateWidth)` (lc_ctrl.sv:133) | CSR 宽度与解码宽度一致 | 参数一致性 |
| 12 | `ASSERT_INIT(DecLcCountWidthCheck_A, CsrLcCountWidth==DecLcCountWidth)` (lc_ctrl.sv:134) | CSR counter 宽度一致 | 参数一致性 |
| 13 | `ASSERT_INIT(DecLcIdStateWidthCheck_A, CsrLcIdStateWidth==ExtDecLcIdStateWidth)` (lc_ctrl.sv:135) | CSR ID state 宽度一致 | 参数一致性 |
| 14 | `ASSERT_INIT(NumTokenWordsCheck_A, NumTokenWords==LcTokenWidth/32)` (lc_ctrl.sv:136) | token 字数与位宽匹配 | token 位宽一致性 |
| 15 | `ASSERT_INIT(OtpTestCtrlWidth_A, OtpTestCtrlWidth==CsrOtpTestCtrlWidth)` (lc_ctrl.sv:137) | OTP test ctrl 宽度匹配 | 参数一致性 |
| 16 | `ASSERT_KNOWN(RegsTlOKnown, regs_tl_o)` (lc_ctrl.sv:832) | regs TL 输出不含 X | 输出完整性 |
| 17 | `ASSERT_KNOWN(DmiTlOKnown, dmi_tl_o)` (lc_ctrl.sv:833) | DMI TL 输出不含 X | 输出完整性 |
| 18 | `ASSERT_KNOWN(AlertTxKnown_A, alert_tx_o)` (lc_ctrl.sv:834) | alert 输出不含 X | 输出完整性 |
| 19 | `ASSERT_KNOWN(PwrLcKnown_A, pwr_lc_o)` (lc_ctrl.sv:835) | pwr_lc 输出不含 X | 输出完整性 |
| 20 | `ASSERT_KNOWN(LcOtpProgramKnown_A, lc_otp_program_o)` (lc_ctrl.sv:836) | OTP program 输出不含 X | 输出完整性 |
| 21 | `ASSERT_KNOWN(LcOtpTokenKnown_A, kmac_data_o)` (lc_ctrl.sv:837) | KMAC 接口输出不含 X | 输出完整性 |
| 22 | `ASSERT_KNOWN(LcDftEnKnown_A, lc_dft_en_o)` (lc_ctrl.sv:838) | lc_dft_en 不含 X | 输出完整性 |
| 23 | `ASSERT_KNOWN(LcNvmDebugEnKnown_A, lc_nvm_debug_en_o)` (lc_ctrl.sv:839) | lc_nvm_debug_en 不含 X | 输出完整性 |
| 24 | `ASSERT_KNOWN(LcHwDebugEnKnown_A, lc_hw_debug_en_o)` (lc_ctrl.sv:840) | lc_hw_debug_en 不含 X | 输出完整性 |
| 25 | `ASSERT_KNOWN(LcCpuEnKnown_A, lc_cpu_en_o)` (lc_ctrl.sv:841) | lc_cpu_en 不含 X | 输出完整性 |
| 26 | `ASSERT_KNOWN(LcCreatorSwRwEn_A, lc_creator_seed_sw_rw_en_o)` (lc_ctrl.sv:842) | creator seed rw enable 不含 X | 输出完整性 |
| 27 | `ASSERT_KNOWN(LcOwnerSwRwEn_A, lc_owner_seed_sw_rw_en_o)` (lc_ctrl.sv:843) | owner seed rw enable 不含 X | 输出完整性 |
| 28 | `ASSERT_KNOWN(LcIsoSwRwEn_A, lc_iso_part_sw_rd_en_o)` (lc_ctrl.sv:844) | iso part rd enable 不含 X | 输出完整性 |
| 29 | `ASSERT_KNOWN(LcIsoSwWrEn_A, lc_iso_part_sw_wr_en_o)` (lc_ctrl.sv:845) | iso part wr enable 不含 X | 输出完整性 |
| 30 | `ASSERT_KNOWN(LcSeedHwRdEn_A, lc_seed_hw_rd_en_o)` (lc_ctrl.sv:846) | seed hw rd enable 不含 X | 输出完整性 |
| 31 | `ASSERT_KNOWN(LcKeymgrEnKnown_A, lc_keymgr_en_o)` (lc_ctrl.sv:847) | keymgr enable 不含 X | 输出完整性 |
| 32 | `ASSERT_KNOWN(LcEscalateEnKnown_A, lc_escalate_en_o)` (lc_ctrl.sv:848) | escalate enable 不含 X | 输出完整性 |
| 33 | `ASSERT_KNOWN(LcCheckBypassEnKnown_A, lc_check_byp_en_o)` (lc_ctrl.sv:849) | check bypass enable 不含 X | 输出完整性 |
| 34 | `ASSERT_KNOWN(LcClkBypReqKnown_A, lc_clk_byp_req_o)` (lc_ctrl.sv:850) | clk bypass request 不含 X | 输出完整性 |
| 35 | `ASSERT_KNOWN(LcFlashRmaSeedKnown_A, lc_flash_rma_seed_o)` (lc_ctrl.sv:851) | flash RMA seed 不含 X | 输出完整性 |
| 36 | `ASSERT_KNOWN(LcFlashRmaReqKnown_A, lc_flash_rma_req_o)` (lc_ctrl.sv:852) | flash RMA request 不含 X | 输出完整性 |
| 37 | `ASSERT_KNOWN(LcKeymgrDiv_A, lc_keymgr_div_o)` (lc_ctrl.sv:853) | keymgr div 输出不含 X | 输出完整性 |
| 38 | `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT(CtrlLcFsmCheck_A, ...)` (lc_ctrl.sv:856) | FSM sparse 错误触发 alert[1] | MAIN.FSM.SPARSE 兑现 |
| 39 | `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT(CtrlLcStateCheck_A, ...)` (lc_ctrl.sv:858) | LC state sparse 错误触发 alert[1] | MANUF.STATE.SPARSE 兑现 |
| 40 | `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT(CtrlLcCntCheck_A, ...)` (lc_ctrl.sv:864) | LC cnt sparse 错误触发 alert[1] | TRANSITION.CTR.SPARSE 兑现 |
| 41 | `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT(CtrlKmacIfFsmCheck_A, ...)` (lc_ctrl.sv:870) | KMAC IF FSM sparse 错误触发 alert[1] | KMAC.FSM.SPARSE 兑现 |
| 42 | `ASSERT_PRIM_REG_WE_ONEHOT_ERROR_TRIGGER_ALERT(RegsWeOnehotCheck_A, ...)` (lc_ctrl.sv:877) | reg we one-hot 错误触发 alert[2] | BUS.INTEGRITY 兑现 |
| 43 | `ASSERT_PRIM_REG_WE_ONEHOT_ERROR_TRIGGER_ALERT(TapDmiWeOnehotCheck_A, ...)` (lc_ctrl.sv:878) | TAP/DMI we one-hot 错误触发 alert[2] | BUS.INTEGRITY 兑现 |
| 44 | `ASSERT(SignalsAreOffWhenNotEnabled_A, ...)` (lc_ctrl_signal_decode.sv:335) | lc_state_valid_i=0 → 所有 broadcast 输出为 Off，keymgr_div=Invalid | 未初始化时信号安全 |
| 45 | `ASSERT(FsmInScrap_A, ...)` (lc_ctrl_signal_decode.sv:353) | FSM 在 Scrap/Invalid/Escalate 时所有 enable 信号为 Off | 终止态安全 |

## 四、树内参考
| # | 参考物 (绝对路径) | 类型 | 可对比什么 |
|---|---|---|---|
| 1 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/doc/theory_of_operation.md | 规范文档 | FSM 状态转移图、token 校验流程、access signal 真值表 |
| 2 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/doc/programmers_guide.md | 规范文档 | SW 视角的 transition 流程、volatile unlock 语义 |
| 3 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/doc/lc_ctrl_encoding_table.md | 规范文档 | A/B/C/D 编码表对照 lc_ctrl_state_pkg.sv 常量 |
| 4 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/doc/lc_ctrl_access_signals_table.md | 规范文档 | 各 LC state 下 broadcast signal (dft_en/hw_debug_en/cpu_en/...) 预期值 vs signal_decode 逻辑 |
| 5 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/doc/lc_ctrl_counter_table.md | 规范文档 | transition counter 行为 vs FSM CntIncrSt/CntProgSt |
| 6 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/doc/lc_ctrl_function_signals_table.md | 规范文档 | function signal 真值表 vs signal_decode case 分支 |
| 7 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_state_pkg.sv.tpl | 代码生成模板 | gen-lc-state-enc.py 的输出模板，可验证 state_pkg 生成一致性 |
| 8 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_lc_sender.sv | 兄弟原语 | 14 个 prim_lc_sender 实例（lc_ctrl_signal_decode.sv:224-290）的编码/解码逻辑 |
| 9 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_flop_2sync.sv | 兄弟原语 | 2-sync 同步器用于 otp_lc_data 初始化（lc_ctrl.sv:703）和 kmac_if（lc_ctrl_kmac_if.sv:111） |

## 五、特殊结构提示
1. **FSM case 分支完整性**：lc_ctrl_fsm.sv:244 `unique case (fsm_state_q)` 有 13 个状态（ResetSt→TransProgSt→IdleSt→ClkMuxSt→CntIncrSt→CntProgSt→TokenHashSt→TokenCheck0St→TokenCheck1St→FlashRmaSt→TransCheckSt→ScrapSt + default→EscalateSt/InvalidSt）。default 分支（:563）处理所有未列出的 sparse 态，走向 EscalateSt。若注入者删除 default 或将其改为 no-op 即为洞。
2. **state_decode case 分支完整性**：lc_ctrl_state_decode.sv:75 `unique case (lc_state_i)` 有 21 个合法态 + default→state_invalid_error_o[1]=1。lc_state_i 枚举有 NumLcStates=21 个值，case 刚好覆盖。
3. **token comparison 位宽**：lc_ctrl_fsm.sv:456 `hashed_token_i[31:0]==hashed_token_mux[31:0]` 分两半比较 128bit token（低 32bit + 高 96bit 两次）。若注入者截断比较位宽可绕过。
4. **token_idx 双份冗余**：token_idx0/token_idx1 分别由 dec_lc_state_o[0]/[1] 和 trans_target_i[0]/[1] 查 TransTokenIdxMatrix（lc_ctrl_fsm.sv:736-742）。两者必须一致；不一致→TRANSITION_ERROR。
5. **hashed_tokens_valid0/valid1 双份**：valid0 用 test_tokens_valid[4],test_tokens_valid[5],rma_token_valid[2]；valid1 用 [6],[7],[3]（lc_ctrl_fsm.sv:716-730）。OTP 输出两组独立 MUBI valid 信号做冗余校验。
6. **粘性 error 位**：fatal_prog_error_q / fatal_state_error_q / fatal_bus_integ_error_q 一旦置 1 只能复位清零（lc_ctrl.sv:547-552 自或逻辑）。若注入者将 `|=` 改为 `=` 则 error 可被后续正常操作覆盖。
7. **SecVolatileRawUnlockEn 门控**：当该参数=0 时 volatile_raw_unlock_success_q 固定 MuBi8False（lc_ctrl_fsm.sv:630），且 FSM 不走 volatile unlock 分支。若注入者将 generate if 条件改反可绕过。
8. **lc_keymgr_div 唯一性**：4 个 RndCnst div 值由 ASSERT_INIT 保证互不相同（lc_ctrl_signal_decode.sv:314-329）。若注入者使两个 div 值相等则 keymgr 无法区分 LC state。
9. **RndCnstInvalidTokens 填充**：未用 token 位置由 RndCnstInvalidTokens（1024bit 随机）填充（lc_ctrl_fsm.sv:681）。若注入者将其改为全零/全一则 invalid token 可被猜到。
10. **transition counter 上限**：NumLcCountStates=25，但 hjson 说最多 24 次（lc_ctrl.hjson:1257）。LcCnt24 对应 dec_lc_cnt=24，超过则 SCRAP。FSM CntIncrSt 中需检查 cnt<24 才递增，否则直接进 PostTransSt+TRANSITION_COUNT_ERROR。
