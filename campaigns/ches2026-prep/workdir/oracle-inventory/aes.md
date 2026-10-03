# aes 盲预言机目录

## 元信息
- 树: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
- 扫描范围: hw/ip/aes/{rtl,data,doc}
- SEC_CM 声明数: 27 / SVA 数: 54 / testplan 条目数: 42 (27 sec_cm + 15 functional)

## 一、SEC_CM 声明 ↔ RTL 锚点
| # | SEC_CM 声明 (hjson:line) | RTL 锚点 (file:line) | 检验要点 |
|---|---|---|---|
| 1 | BUS.INTEGRITY (aes.hjson:326) | aes.sv:89 | aes_reg_top 实例的 intg_err_o 必须连到 alert 逻辑；TL-UL integrity 覆盖端到端 |
| 2 | LC_ESCALATE_EN.INTERSIG.MUBI (aes.hjson:329) | aes.sv:110 | prim_lc_sync 实例化，lc_escalate_en_i 经 MUBI 同步后送控制 FSM；极性必须与 lc_ctrl_pkg::On 匹配 |
| 3 | MAIN.CONFIG.SHADOW (aes.hjson:332) | aes_ctrl_reg_shadowed.sv:121 | 每个字段独立 prim_subreg_shadow 实例；update_err→recov alert，storage_err→fatal alert |
| 4 | MAIN.CONFIG.SPARSE (aes.hjson:335) | aes_pkg.sv:93; aes_pkg.sv:99; aes_pkg.sv:114; aes_pkg.sv:121 | aes_op_e/aes_mode_e/key_len_e/prng_reseed_rate_e 均为 one-hot 枚举；非法值映射逻辑在 aes_ctrl_reg_shadowed.sv 内（看 default 分支映射目标） |
| 5 | AUX.CONFIG.SHADOW (aes.hjson:338) | aes.sv:90 | CTRL_AUX_SHADOWED 寄存器走 shadowed 路径；update/storage err alert 与主 CTRL 共用 |
| 6 | AUX.CONFIG.REGWEN (aes.hjson:341) | aes.sv:91 | CTRL_AUX_REGWEN 为 rw0c；清 0 后 CTRL_AUX_SHADOWED 不可写直到 reset |
| 7 | KEY.SIDELOAD (aes.hjson:344) | aes_core.sv:314 | key_init_sel==KEY_INIT_KEYMGR 时 key_init_d=key_sideload；侧载路径与 SW 路径互斥（同一 MUX） |
| 8 | KEY.SW_UNREADABLE (aes.hjson:347) | aes.sv:92 | KEY_SHARE0/1 的 swaccess="wo"；reg_top 不生成读路径 |
| 9 | DATA_REG.SW_UNREADABLE (aes.hjson:350) | aes.sv:93 | DATA_IN 的 swaccess="wo"；内部 state 不可 SW 读 |
| 10 | KEY.SEC_WIPE (aes.hjson:353) | aes_core.sv:313; aes_cipher_core.sv:436; aes_cipher_core.sv:457 | key_init_sel==KEY_INIT_CLEAR 时 key_init_d=prd_clearing_key_init（非常数，来自 LFSR PRNG）；cipher_core key_full_sel==KEY_FULL_CLEAR/default 时走 prd_clearing_key_i |
| 11 | IV.CONFIG.SEC_WIPE (aes.hjson:356) | aes_core.sv:339 | iv_sel==IV_CLEAR/default 时 iv_d=prd_clearing_data（非常数） |
| 12 | DATA_REG.SEC_WIPE (aes.hjson:359) | aes_core.sv:365; aes_core.sv:684; aes_cipher_core.sv:245; aes_cipher_control_fsm.sv:415 | data_in_prev_sel==DIP_CLEAR default 走 prd_clearing_data；data_in 寄存器 de 由 data_in_we 驱动；cipher_core state_sel==STATE_CLEAR 走 prd_clearing_state_i；cipher_ctrl data_out_clear 时 add_rk_sel=ADD_RK_INIT |
| 13 | DATA_REG.KEY.SCA (aes.hjson:362) | aes_cipher_control_fsm.sv:337; aes_cipher_core.sv:822 | 最后一轮后 state_sel_o=STATE_CLEAR；SVA AesSecCmDataRegKeySca 断言 state_q ≠ 上一轮 add_round_key_out（除非新初始态碰巧相等或 PRD 等于输出或 alert） |
| 14 | KEY.MASKING (aes.hjson:368) | aes_core.sv:464; aes_sbox.sv:68; aes_sbox_canright_masked.sv:433; aes_sbox_canright_masked_noreuse.sv:391; aes_sbox_dom.sv:983 | SecMasking=1 时 cipher_core 保持双 share；SBox 选 Dom/CanrightMasked/CanrightMaskedNoreuse；SVA AesSecCmKeyMaskingPrdSubBytes 断言每轮 SubBytes 前掩码 PRNG 已更新 |
| 15 | MAIN.FSM.SPARSE (aes.hjson:374) | aes_control_fsm.sv:631 | PRIM_FLOP_SPARSE_FSM 实例化，非法态→CTRL_ERROR→alert_o=1 |
| 16 | MAIN.FSM.REDUN (aes.hjson:377) | aes_control.sv:244 | Sp2VWidth 个独立 FSM rail（p/n 变体），输出 AND 合并、错误 OR 合并 |
| 17 | CIPHER.FSM.SPARSE (aes.hjson:380) | aes_cipher_control_fsm.sv:450 | PRIM_FLOP_SPARSE_FSM 实例化，非法态→CIPHER_CTRL_ERROR→alert_o=1 |
| 18 | CIPHER.FSM.REDUN (aes.hjson:383) | aes_cipher_control.sv:148 | Sp2VWidth 个独立 cipher_control_fsm rail，AND/OR 合并 |
| 19 | CIPHER.CTR.REDUN (aes.hjson:386) | aes_cipher_control.sv:149 | 与 CIPHER.FSM.REDUN 同一 gen_fsm 循环内，round_counter 双 rail 保护 |
| 20 | CTR.FSM.SPARSE (aes.hjson:389) | aes_ctr_fsm.sv:120 | PRIM_FLOP_SPARSE_FSM 实例化，非法态→CTR_ERROR→alert_o=1（延迟 100 周期后） |
| 21 | CTR.FSM.REDUN (aes.hjson:392) | aes_ctr.sv:105 | Sp2VWidth 个独立 ctr_fsm rail |
| 22 | CTRL.SPARSE (aes.hjson:395) | aes_control.sv:511; aes_cipher_control.sv:389; aes_ctr.sv:75; aes_sub_bytes.sv:37 | Sp2V/Sparsely-encoded 握手与 MUX 控制信号经 aes_sel_buf_chk 检查；非法值→sp_enc_err→FSM→ERROR |
| 23 | MAIN.FSM.GLOBAL_ESC (aes.hjson:398) | aes_control_fsm.sv:610 | lc_escalate_en_i 为 true_loose 时无条件跳 CTRL_ERROR |
| 24 | MAIN.FSM.LOCAL_ESC (aes.hjson:401) | aes_control_fsm.sv:611 | mux_sel_err_i || sp_enc_err_i || cipher_op_err 时跳 CTRL_ERROR |
| 25 | CIPHER.FSM.LOCAL_ESC (aes.hjson:407) | aes_cipher_control_fsm.sv:430 | mux_sel_err_i || sp_enc_err_i || rnd_ctr_err_i || op_err_i || alert_fatal_i 时跳 CIPHER_CTRL_ERROR |
| 26 | CTR.FSM.LOCAL_ESC (aes.hjson:413) | aes_ctr_fsm.sv:82 | incr_err_i || mr_err_i 时跳 CTR_ERROR |
| 27 | DATA_REG.LOCAL_ESC (aes.hjson:419) | aes_core.sv:982; aes_core.sv:988 | SVA AesSecCmDataRegLocalEscDataOut + AesSecCmDataRegLocalEscIv：alert_fatal_o 活跃时 data_out_q/iv_q 不得等于中间 state（state_done_transposed） |

## 二、行为性描述句（hjson 原文 → 检验点）
| # | hjson 原文 (file:line) | 检验点 |
|---|---|---|
| 1 | "The AES unit cannot recover from such an error and needs to be reset." (aes.hjson:230) | fatal_fault alert 触发后，idle_o 不会回到 1，status.idle 不会回 1，直到 rst_ni |
| 2 | "Key registers are cleared with pseudo-random data." (aes.hjson:354) | TRIGGER.KEY_IV_DATA_IN_CLEAR=1 后，KEY_SHARE0/1 寄存器值必须变为 prd_clearing_key_init（来自 LFSR，非常数） |
| 3 | "IV registers are cleared with pseudo-random data." (aes.hjson:357) | TRIGGER.KEY_IV_DATA_IN_CLEAR=1 后，IV 寄存器值变为 prd_clearing_data |
| 4 | "Data input/output and internal state registers are cleared with pseudo-random data." (aes.hjson:360) | TRIGGER.KEY_IV_DATA_IN_CLEAR=1 清输入，TRIGGER.DATA_OUT_CLEAR=1 清输出；cipher_core state_sel=STATE_CLEAR 走 prd_clearing_state_i |
| 5 | "Internal state register cleared with pseudo-random data at the end of the last round." (aes.hjson:364) | 最后一轮完成后 state_sel_o=STATE_CLEAR；SVA AesSecCmDataRegKeySca 验证 state_q≠上一输出（除非等价例外） |
| 6 | "1st-order domain-oriented masking of the cipher core including data path and key expand." (aes.hjson:370) | SecMasking=1 时 key_init_cipher 保持双 share 不合并；SBox 选 masked 变体；SVA AesSecCmKeyMaskingPrdSubBytes 确保每轮 PRD 更新 |
| 7 | "The main control FSM moves to a terminal error state upon local escalation." (aes.hjson:403) | mux_sel_err||sp_enc_err||cipher_op_err → aes_ctrl_ns=CTRL_ERROR → alert_o=1 且不恢复 |
| 8 | "The cipher core FSM moves to a terminal error state upon local escalation." (aes.hjson:409) | mux_sel_err||sp_enc_err||rnd_ctr_err||op_err||alert_fatal → CIPHER_CTRL_ERROR → alert_o=1 |
| 9 | "The CTR mode FSM moves to a terminal error state upon local escalation." (aes.hjson:415) | incr_err||mr_err → CTR_ERROR → alert_o=1（延迟 100 周期） |
| 10 | "Upon local escalation, the module doesn't output intermediate state." (aes.hjson:420) | alert_fatal_o 时 data_out_q≠state_done_transposed 且 iv_q≠state_done_transposed |
| 11 | "Upon reset, these registers are cleared with pseudo-random data." (aes.hjson:449) | KEY_SHARE0/1 reset 后值由 PRD 覆写（不是全 0） |
| 12 | "Upon reset, these registers are cleared with pseudo-random data." (aes.hjson:509) | IV 寄存器 reset 后值由 PRD 覆写 |
| 13 | "Upon reset, these registers are cleared with pseudo-random data." (aes.hjson:539) | DATA_IN 寄存器 reset 后值由 PRD 覆写 |
| 14 | "Upon reset, these registers are cleared with pseudo-random data." (aes.hjson:566) | DATA_OUT 寄存器 reset 后值由 PRD 覆写 |
| 15 | "If the AES unit is non-idle, writes to this register are ignored." (aes.hjson:591) | CTRL_SHADOWED 写操作在 status.idle=0 时被丢弃 |
| 16 | "This trigger is cleared to `0` if MANUAL_OPERATION=0 or if MODE=AES_NONE" (aes.hjson:848) | TRIGGER.START 在自动模式或 NONE 模式下被自动清 0 |
| 17 | "If this is cleared to 0, the Auxiliary Control Register cannot be written anymore." (aes.hjson:817) | CTRL_AUX_REGWEN=0 后，对 CTRL_AUX_SHADOWED 的写无效直到 reset |
| 18 | "A fatal fault has occurred and the AES unit needs to be reset" (aes.hjson:958) | STATUS.ALERT_FATAL_FAULT=1 后，任何操作不可恢复；需 rst_ni |

## 三、SVA 清单（行为合同）
| # | 断言 (file:line) | 内容摘要 | 约束的预期行为 |
|---|---|---|---|
| 1 | AesSecCmDataRegLocalEscDataOut (aes_core.sv:982) | alert_fatal_o 活跃且 cipher_crypt 刚完成时，data_out_q ≠ 中间 state（三种模式均验） | 本地升级时中间态不泄露到 DATA_OUT |
| 2 | AesSecCmDataRegLocalEscIv (aes_core.sv:988) | 同上但检验 IV 寄存器 | 本地升级时中间态不泄露到 IV |
| 3 | AesSecCmDataRegKeySca (aes_cipher_core.sv:822) | 最后一轮 state_we 时 state_q ≠ 上一 add_round_key_out（有例外条款） | 最后一轮后 state 被 PRD 覆写（SCA 对策） |
| 4 | AesSecCmKeyMaskingPrdSubBytes (aes_cipher_core.sv:840) | SubBytes 使能时 PRD 在 NumCyclesPerRound 内已更新（除非 force_masks） | 每次求值使用新鲜掩码 |
| 5 | AesSecCmKeyMaskingInitialPrngUpdateSubBytes (aes_cipher_core.sv:853) | 首次 SubBytes 前掩码 PRNG 已更新 | 初始掩码非常数 |
| 6 | AesSecCmKeyMaskingInitialPrngUpdateKeyExpand (aes_cipher_core.sv:860) | 首次 KeyExpand 前掩码 PRNG 已更新 | KeyExpand 使用新鲜掩码 |
| 7 | AesSecCmKeyMaskingStateShare (aes_cipher_core.sv:873) | 连续两轮 state_q[s] 不恒常（除非 force_masks 或 dec_key_gen） | 掩码使 state share 非静态 |
| 8 | AesSecCmKeyMaskingOutputShare (aes_cipher_core.sv:878) | 连续两轮输出 share 非恒常 | 掩码使输出 share 非静态 |
| 9 | AesModeValid (aes_core.sv:955) | !ctrl_err_storage → aes_mode_q ∈ {ECB,CBC,CFB,OFB,CTR,NONE} | 模式信号合法 |
| 10 | AesOpValid (aes_core.sv:963) | !ctrl_err_storage → aes_op_q ∈ {ENC,DEC} | 操作信号合法 |
| 11 | AesControlFsmCheck_A (aes.sv:257/262) | sparse FSM 非法态触发 alert_tx_o[1] | MAIN FSM 错误→fatal alert |
| 12 | AesCtrFsmCheck_A (aes.sv:271/276) | sparse FSM 非法态触发 alert_tx_o[1] | CTR FSM 错误→fatal alert |
| 13 | AesCipherControlFsmCheck_A (aes.sv:285/290) | sparse FSM 非法态触发 alert_tx_o[1] | CIPHER FSM 错误→fatal alert |
| 14 | RegWeOnehotCheck_A (aes.sv:298) | reg_we one-hot 错误→alert_tx_o[1] | 寄存器写使能 one-hot |
| 15 | TlODValidKnown (aes.sv:248) | tl_o.d_valid 复位后已知 | TL-UL 输出合法 |
| 16 | TlOAReadyKnown (aes.sv:249) | tl_o.a_ready 复位后已知 | TL-UL 输出合法 |
| 17 | IdleKnown (aes.sv:250) | idle_o 复位后已知 | idle 输出合法 |
| 18 | EdnReqKnown (aes.sv:251) | edn_o 复位后已知 | EDN 请求合法 |
| 19 | AlertTxKnown (aes.sv:252) | alert_tx_o 复位后已知 | alert 输出合法 |
| 20 | AesCoreSecMaskingNonDefault (aes_core.sv:952) | SecMasking==1（lint error 否则） | 防止意外关闭掩码 |
| 21 | AesSecMaskingNonDefault (aes_cipher_core.sv:799) | SecMasking==1（lint error） | 同上 |
| 22 | AesMaskedCoreAndSBox (aes_cipher_core.sv:802) | SecMasking=1 ↔ SBox masked；SecMasking=0 ↔ SBox unmasked | 掩码与 SBox 类型一致 |
| 23 | AesMaskedCoreAndSBox (aes_key_expand.sv:487) | 同上 | key_expand 掩码与 SBox 一致 |
| 24 | AesControlFsmSecMaskingNonDefault (aes_control_fsm.sv:844) | SecMasking==1 | FSM 防意外关掩码 |
| 25 | AesCipherControlFsmSecMaskingNonDefault (aes_cipher_control_fsm.sv:489) | SecMasking==1 | cipher FSM 同上 |
| 26 | AesCipherControlFsmSecSBoxImplNonDefault (aes_cipher_control_fsm.sv:493) | SecSBoxImpl==SBoxImplDom | 防止意外降级 SBox |
| 27 | AesSBoxSecSBoxImplNonDefault (aes_sbox.sv:29) | SecSBoxImpl==SBoxImplDom | SBox 顶层防降级 |
| 28 | AesSecStartTriggerDelayNonDefault (aes_control.sv:124) | SecStartTriggerDelay==0 | 防意外使能触发延迟 |
| 29 | AesSecSkipPRNGReseedingNonDefault (aes_prng_clearing.sv:55) | SecSkipPRNGReseeding==0 | 清除 PRNG 不跳 reseed |
| 30 | AesSecSkipPRNGReseedingNonDefault (aes_prng_masking.sv:76) | SecSkipPRNGReseeding==0 | 掩码 PRNG 不跳 reseed |
| 31 | AesSecAllowForcingMasksNonDefault (aes_prng_masking.sv:68) | SecAllowForcingMasks==0 | 防意外使能强制掩码 |
| 32 | AesKeyExpandSecMaskingNonDefault (aes_key_expand.sv:484) | SecMasking==1 | key_expand 防关掩码 |
| 33 | AesPrngWidth (aes_prng_clearing.sv:145) | Width==64 | 清除 PRNG 位宽固定 |
| 34 | SharePermutationCheck_A (aes_prng_clearing.sv:159) | RndCnstSharePerm 是有效置换（所有 bit 位被标记） | 置换常数正确 |
| 35 | PermutationCheck_A (aes_prng_masking.sv:146) | RndCnstLfsrPerm 是有效置换 | LFSR 置换常数正确 |
| 36 | AesModeValid (aes_control_fsm.sv:847) | !ctrl_err_storage → mode_i 合法 | FSM 内模式信号合法 |
| 37 | AesOpValid (aes_control_fsm.sv:855) | !ctrl_err_storage → op_i 合法 | FSM 内操作信号合法 |
| 38 | AesCiphOpValid (aes_control_fsm.sv:859) | !cipher_op_err → cipher_op_i ∈ {CIPH_FWD,CIPH_INV} | cipher 操作合法 |
| 39 | AesControlStateValid (aes_control_fsm.sv:863) | !alert_o → FSM 态合法 | MAIN FSM 无错误时态合法 |
| 40 | AesCtrStateValid (aes_ctr_fsm.sv:129) | !alert_o → FSM 态 ∈ {CTR_IDLE,CTR_INCR} | CTR FSM 无错误时态合法 |
| 41 | AesNumSlicesCtr (aes_control_fsm.sv:874) | NumSlicesCtr==8 | 参数校验 |
| 42 | AesNumSlicesCtr (aes_core.sv:969) | NumSlicesCtr==8 | 参数校验 |
| 43 | AesSelBufChkNum (aes_sel_buf_chk.sv:162) | Num ∈ {2,3,4,6} | sparse 编码参数合法 |
| 44 | AesWidthPRDSBox (aes_sbox.sv:86) | WidthPRDSBox==8 (Dom) | Dom SBox PRD 宽度 |
| 45 | AesWidthPRDSBox (aes_sbox.sv:109) | WidthPRDSBox==18 (CanrightMasked) | CanrightMasked SBox PRD 宽度 |
| 46 | AesWidthPRDSBox (aes_sbox.sv:131) | WidthPRDSBox==8 (CanrightMaskedNoreuse) | Noreuse SBox PRD 宽度 |
| 47 | wePulse (aes_reg_top.sv:1877) | reg_we 为脉冲（单周期） | 寄存器写使能脉冲语义 |
| 48 | rePulse (aes_reg_top.sv:1878) | reg_re 为脉冲（单周期） | 寄存器读使能脉冲语义 |
| 49 | AesDomIndepMulPower (aes_sbox_dom.sv:180) | NPower==4 或 NPower==2 | DOM 独立乘法幂次 |
| 50 | AesDomDepMulUnoptPower (aes_sbox_dom.sv:310) | NPower==4 或 NPower==2 | DOM 非优化依赖乘法 |
| 51 | AesDomDepMulPower (aes_sbox_dom.sv:576) | NPower==4 或 NPower==2 | DOM 依赖乘法幂次 |
| 52 | IdleNotIdle_A (dv/sva/aes_idle_check.sv:23) | idle 寄存器值 == idle_o（MUBI 编码） | idle 状态与寄存器一致 |
| 53 | reAfterRv (aes_reg_top.sv:1880) | reg_re/reg_we 上升沿后下一周期 d_valid | TL-UL 协议响应时序 |
| 54 | en2addrHit (aes_reg_top.sv:1882) | reg_we||reg_re → $onehot0(addr_hit) | 寄存器访问地址 one-hot |

## 四、树内参考
| # | 参考物 (绝对路径) | 类型 | 可对比什么 |
|---|---|---|---|
| 1 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/dv/aes_model_dpi/aes_model_dpi.c | 参考实现（C DPI model） | AES 加解密正确性：对比 RTL 输出与 C model 输出 |
| 2 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/dv/test_vectors/nist_vectors_pkg.sv | NIST 测试向量 | ECB/CBC/CFB/OFB/CTR 各模式的已知答案测试 |
| 3 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_sbox_dom.sv | 参考实现（DOM SBox） | KEY.MASKING 的核心实现；与 Canright masked 版本同构对比 |
| 4 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_sbox_canright_masked.sv | 兄弟模块（Canright masked SBox） | 与 aes_sbox_dom.sv 对比掩码方案结构差异 |
| 5 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_sbox_canright_masked_noreuse.sv | 兄弟模块（Canright masked no-reuse SBox） | 同上，对比 reuse vs no-reuse |
| 6 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_sbox_canright.sv | 兄弟模块（Canright unmasked SBox） | 非掩码参考，对比掩码版是否正确加入掩码逻辑 |
| 7 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_sbox_lut.sv | 兄弟模块（LUT SBox） | 最简实现，用作功能基线 |
| 8 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/dv/sva/aes_idle_check.sv | SVA 绑定（idle 检查） | idle_o 与寄存器 status.idle 一致性 |
| 9 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/dv/sva/aes_bind.sv | SVA 绑定（TL-UL + CSR + idle + reseed） | TL-UL 协议、CSR 语义、reseed 时序 |
| 10 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/doc/theory_of_operation.md | 规范文档 | 控制流、key schedule、模式实现的文字规范 vs RTL |
| 11 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_control_fsm_p.sv ↔ aes_control_fsm_n.sv | 兄弟模块（冗余 FSM rail 对） | p/n 变体结构对称性；不对称=潜在漏洞 |
| 12 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_cipher_control_fsm_p.sv ↔ aes_cipher_control_fsm_n.sv | 兄弟模块（冗余 cipher FSM rail 对） | 同上 |
| 13 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_ctr_fsm_p.sv ↔ aes_ctr_fsm_n.sv | 兄弟模块（冗余 CTR FSM rail 对） | 同上 |
| 14 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_reduced_round.sv | 参考实现（简化轮函数） | 面积优化版 vs 完整版，对比功能等价性 |

## 五、特殊结构提示

### 5.1 重复 SEC_CM 锚点（声明→多实现映射）
- **KEY.SEC_WIPE**: 3 个 RTL 锚点（aes_core.sv:313 初始 key, aes_cipher_core.sv:436 full key, aes_cipher_core.sv:457 dec key）— 缺任一即候选
- **DATA_REG.SEC_WIPE**: 4 个 RTL 锚点（aes_core.sv:365 data_in_prev, aes_core.sv:684 data_in, aes_cipher_core.sv:245 state, aes_cipher_control_fsm.sv:415 cipher data_out）— 缺任一即候选
- **KEY.MASKING**: 5 个 RTL 锚点（aes_core.sv:464 cipher_core 实例, aes_sbox.sv:68 顶层 SBox, aes_sbox_canright_masked.sv:433, aes_sbox_canright_masked_noreuse.sv:391, aes_sbox_dom.sv:983）— 需检查哪个 SBox 变体实际被综合
- **CTRL.SPARSE**: 4 个 RTL 锚点（aes_control.sv:511, aes_cipher_control.sv:389, aes_ctr.sv:75, aes_sub_bytes.sv:37）
- **MAIN.CONFIG.SPARSE**: 4 个 RTL 锚点全在 aes_pkg.sv（:93/:99/:114/:121），均为枚举类型定义

### 5.2 混淆常量风险点
- RndCnstClearingLfsrSeed (64-bit randtype=data) — 清除 PRNG 种子
- RndCnstClearingLfsrPerm (64-bit randtype=perm) — 清除 LFSR 置换
- RndCnstClearingSharePerm (64-bit randtype=perm) — 第二 share 置换
- RndCnstMaskingLfsrSeed (288-bit randtype=data) — 掩码 PRNG 种子
- RndCnstMaskingLfsrPerm (160-bit randtype=perm) — 掩码 LFSR 置换
- SVA PermutationCheck_A (aes_prng_masking.sv:146) 和 SharePermutationCheck_A (aes_prng_clearing.sv:159) 检验置换完整性但不检验值正确性——需要脚本化常量折叠验证

### 5.3 冗余 FSM 实例模式
- aes_control.sv Sp2VWidth 个 gen_fsm rail（p/n 变体）→ 输出 AND 合并 ctrl_we，错误 OR 合并 mr_alert
- aes_cipher_control.sv 同上模式 → out_valid AND 合并
- aes_ctr.sv 同上模式 → ready AND 合并
- **风险点**：rail 间不对称、AND/OR 极性反转、缓冲插入不完整

### 5.4 Shadowed 寄存器极性
- CTRL_SHADOWED: update_err→recov_ctrl_update_err, storage_err→fatal_fault
- CTRL_AUX_SHADOWED: 同上，且有 REGWEN 锁定
- **风险点**：shadowed storage_err 是否真正连到 fatal alert 路径

### 5.5 SEC_CM 锚点缺失检查
- hjson 声明 27 条 SEC_CM，RTL 锚点总计 42 个（多对多映射）；无声明的锚点缺失（每条 hjson 声明至少有一个 RTL 锚点）

### 5.6 CTR FSM 延迟告警
- aes_ctr_fsm.sv CTR_ERROR 态：alert_counter_q < 100 时 alert_o=0，仅计数器递增；到 100 才 alert_o=1
- **与其他 FSM（MAIN/CIPHER 立即 alert_o=1）不一致**——可能是设计意图也可能是指控点

### 5.7 参数化 vs 魔法数
- NumSlicesCtr 硬编码为 8（两处 ASSERT_INIT 校验）
- NumRegsKey/NumRegsIv/NumRegsData 为 local 参数（8/4/4），在 reg_top 中用作循环边界
- AES192Enable 控制是否支持 192-bit key
