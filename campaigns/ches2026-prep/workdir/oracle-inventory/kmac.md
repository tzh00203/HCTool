# kmac 盲预言机目录

## 元信息
- 树: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
- 扫描范围: hw/ip/kmac/{rtl,data,doc}
- SEC_CM 声明数: 13 / SVA 数: 51 / testplan 条目数: 14 (sec_cm) + 16 (func)

## 一、SEC_CM 声明 ↔ RTL 锚点

| # | SEC_CM 声明 (hjson:line) | RTL 锚点 (file:line) | 检验要点 |
|---|---|---|---|
| 1 | BUS.INTEGRITY (kmac.hjson:298) | kmac.sv:1398 | kmac_reg_top 的 intg_err_o 必须连到 alert_fatal 路径; 检查 kmac.sv:1446 `alert_fatal` 包含 `alert_intg_err` |
| 2 | LC_ESCALATE_EN.INTERSIG.MUBI (kmac.hjson:303) | kmac.sv:1510 | lc_escalate_en_i 经 prim_lc_sync 同步后 6 份; `lc_tx_or_hi` 将 local fatal alert 合入; 检查 kmac.sv:1513-1514 各 copy 被 OR 进 lc_escalate_en[i] |
| 3 | SW_KEY.KEY.MASKING (kmac.hjson:307) | kmac.sv:488 | KEY_SHARE0/1 两个 share 寄存器异或还原; 检查 kmac.sv:489-498 sw_key_data_reg[0] 来自 key_share0, sw_key_data_reg[1] 来自 key_share1; EnMasking==0 时 share1 置 0 |
| 4 | KEY.SIDELOAD (kmac.hjson:311) | kmac_app.sv:766 | keymgr_key_i 经 keymgr_key 数组处理; EnMasking==1 两 share 分别赋值 (line 769-771); EnMasking==0 XOR 合并 (line 773-778) |
| 5 | CFG_SHADOWED.CONFIG.SHADOW (kmac.hjson:315) | kmac.sv:1395 | kmac_reg_top 的 shadowed_storage_err_o 和 shadowed_update_err_o 分别连到 alert_fatal 和 alert_recov_operation (kmac.sv:1429,1446) |
| 6 | FSM.SPARSE (kmac.hjson:318) | kmac_core.sv:165, kmac_app.sv:322, kmac_entropy.sv:490, keccak_round.sv:183, kmac_errchk.sv:185 | 各 FSM 均用 `PRIM_FLOP_SPARSE_FSM` 实例化; 检查 `u_state_regs` 存在且编码非连续 |
| 7 | CTR.REDUN (kmac.hjson:321) | kmac_core.sv:410, keccak_round.sv:555, sha3pad.sv:190 | kmac_core 用 `prim_count` 做 key_index_count; keccak_round 用 `prim_count` 做 round_count; sha3pad 用 `prim_count` 做 sentmsg_count; 检查 err_o 连到 alert_fatal |
| 8 | PACKER.CTR.REDUN (kmac.hjson:324) | kmac_msgfifo.sv:107 | prim_packer 的 .EnProtection(EnMasking) 参数; EnMasking==1 时 packer 内部 dup counter 启用 |
| 9 | CFG_SHADOWED.CONFIG.REGWEN (kmac.hjson:327) | kmac.sv:482 | hw2reg.cfg_regwen.d = engine_stable (= sha3_fsm==StIdle); 空闲时 en=1 可写, 非空闲时 en=0 锁定 |
| 10 | FSM.GLOBAL_ESC (kmac.hjson:330) | kmac.sv:846, kmac_core.sv:245, kmac_app.sv:567, sha3.sv:318, sha3pad.sv:491, keccak_round.sv:397, kmac_entropy.sv:731, kmac_errchk.sv:450 | 各 FSM 在 lc_escalate_en 有效时无条件跳转 TerminalError; 检查各 `lc_tx_test_true_loose(lc_escalate_en)` 条件 |
| 11 | FSM.LOCAL_ESC (kmac.hjson:333) | kmac.sv:846, kmac_core.sv:245, kmac_app.sv:567, sha3.sv:318, sha3pad.sv:491, keccak_round.sv:397, kmac_entropy.sv:731, kmac_errchk.sv:450 | sparse FSM error 信号连到 alert_fatal → alerts_q[1] → alert_to_lc_tx → lc_tx_or_hi → 各 FSM 跳 TerminalError |
| 12 | LOGIC.INTEGRITY (kmac.hjson:336) | kmac_app.sv:679, kmac_app.sv:690, kmac_app.sv:701, kmac_app.sv:709, keccak_round.sv:456 | kmac_app 用 4 个 prim_sec_anchor_buf 保护 mux_sel 和 reg_state_valid; keccak_round 用 1 个 prim_sec_anchor_buf 保护 rst_n |
| 13 | ABSORBED.CTRL.MUBI (kmac.hjson:340) | sha3pad.sv:290 | absorbed_o 类型 mubi4_t; absorbed_d 在 always_comb 中计算后 always_ff 寄存输出 |
| 14 | SW_CMD.CTRL.SPARSE (kmac.hjson:344) | kmac_pkg.sv:71, kmac.sv:282 | kmac_cmd_e 稀疏编码 (min HD=3); sw_cmd 经 kmac_errchk 过滤无效命令; 检查 CmdNone=6'b000000, CmdStart=29, CmdProcess=46, CmdManualRun=49, CmdDone=22 |

## 二、行为性描述句（hjson 原文 → 检验点）

| # | hjson 原文 (file:line) | 检验点 |
|---|---|---|
| 1 | "fatal_fault_err: This fatal alert is triggered when a fatal error is detected... The KMAC unit cannot recover from such an error and needs to be reset." (kmac.hjson:69-78) | alert_fatal 一旦置位不可自清 (kmac.sv:1456-1464 status_alert_fatal_fault 只升不降); 需 reset 才能恢复 |
| 2 | "Data storage and secret key are two share to guard against 1st order attack." (kmac.hjson:306) | KEY_SHARE0 和 KEY_SHARE1 两套寄存器; EnMasking==1 时两 share 均有效, ==0 时 share1 忽略; 检查 kmac.sv:488-498 |
| 3 | "CFG_SHADOWED is protected by REGWEN" (kmac.hjson:326) | hw2reg.cfg_regwen.d = engine_stable; 非 Idle 时 cfg_shadowed 不可写; 检查 kmac.sv:482-483 |
| 4 | "Escalation moves all sparse FSMs into an invalid state." (kmac.hjson:329) | lc_escalate_en 有效 → 所有 8 个 sparse FSM 跳 TerminalError; 检查 kmac.sv:849, kmac_core.sv:248, kmac_app.sv:567 行附近 |
| 5 | "Local fatal faults move all sparse FSMs into an invalid state." (kmac.hjson:332) | alert_fatal → alerts_q[1] → alert_to_lc_tx → lc_tx_or_hi 注入 lc_escalate_en; 同 #4 路径 |
| 6 | "absorbed signal is mubi4_t type to protect against FI attacks." (kmac.hjson:339) | sha3pad.sv:291 absorbed_o 声明为 prim_mubi_pkg::mubi4_t; 复位值 MuBi4False (line 293) |
| 7 | "sw_cmd and related signals are sparse encoded to protect against FI attacks." (kmac.hjson:343) | kmac_cmd_e 6-bit 稀疏编码 (kmac_pkg.sv:96-105); kmac_errchk 检查非法值 (kmac_errchk.sv:185-209) |
| 8 | "The reset net for the internal state register and critical nets around the output register are buried." (kmac.hjson:335) | keccak_round.sv:456-463 rst_ni 经 prim_sec_anchor_buf 后才接 keccak state register 的 rst_n |
| 9 | "If the mode field is set to SHAKE or cSHAKE, only 128 and 256 strength can be selected. Other value will result error when hashing starts." (kmac.hjson:399-400) | kmac_errchk 检查 mode+strength 合法性; 检查 ErrUnexpectedModeStrength 错误码 (kmac_pkg.sv:433) |

## 三、SVA 清单（行为合同）

| # | 断言 (file:line) | 内容摘要 | 约束的预期行为 |
|---|---|---|---|
| 1 | kmac.sv:181 `ASSERT_INIT PrefixRegSameToPrefixPkg_A | NumWordsPrefix*4 == NSRegisterSize | 前缀寄存器大小与 package 常量一致 |
| 2 | kmac.sv:186 `ASSERT_INIT NumEntriesRegSameToNumEntriesPkg_A | NumEntriesMsgFifo == MsgFifoDepth | FIFO 深度参数一致 |
| 3 | kmac.sv:191 `ASSERT_INIT EntrySizeRegSameToEntrySizePkg_A | NumBytesMsgFifoEntry*8 == MsgWidth | FIFO 条目字节宽度一致 |
| 4 | kmac.sv:354 `ASSERT_STATIC_LINT_ERROR KmacSecCmdDelayNonDefault | SecCmdDelay==0 | 非默认值产生 lint 错误, 防止意外使能 |
| 5 | kmac.sv:429 `ASSERT_KNOWN KmacCmd_A | sw_cmd 已知值 | 命令信号不为 X |
| 6 | kmac.sv:853 `ASSERT_KNOWN KmacStKnown_A | kmac_st 已知值 | 顶层 FSM 状态不为 X |
| 7 | kmac.sv:1483 `ASSERT_INIT NumAlerts2_A | NumAlerts==2 | 必须恰好 2 个 alert |
| 8 | kmac.sv:1543 `ASSERT_INIT SecretKeyDivideBy32_A | MaxKeyLen%32==0 | 密钥长度对齐 |
| 9 | kmac.sv:1546 `ASSUME CmdSparse_M | cmd.qe → cmd.q 属于合法稀疏命令 | SW 只写合法稀疏命令 |
| 10 | kmac.sv:1550 `ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT SentMsgCountCheck_A | sentmsg_count error → alert[1] | 消息计数器错误触发 fatal alert |
| 11 | kmac.sv:1552 `ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT RoundCountCheck_A | round_count error → alert[1] | 轮计数器错误触发 fatal alert |
| 12 | kmac.sv:1554 `ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT KeyIndexCountCheck_A | key_index_count error → alert[1] | 密钥索引计数器错误触发 fatal alert |
| 13 | kmac.sv:1558 `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT KmacCoreFsmCheck_A | kmac_core FSM error → alert[1] | kmac_core FSM 错误触发 fatal alert |
| 14 | kmac.sv:1559 `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT KmacAppFsmCheck_A | kmac_app FSM error → alert[1] | kmac_app FSM 错误触发 fatal alert |
| 15 | kmac.sv:1560 `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT SHA3FsmCheck_A | sha3 FSM error → alert[1] | sha3 FSM 错误触发 fatal alert |
| 16 | kmac.sv:1561 `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT SHA3padFsmCheck_A | sha3pad FSM error → alert[1] | sha3pad FSM 错误触发 fatal alert |
| 17 | kmac.sv:1562 `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT KeccackFsmCheck_A | keccak_round FSM error → alert[1] | keccak_round FSM 错误触发 fatal alert |
| 18 | kmac.sv:1564 `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT ErrorCheckFsmCheck_A | errchk FSM error → alert[1] | errchk FSM 错误触发 fatal alert |
| 19 | kmac.sv:1565 `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT KmacFsmCheck_A | 顶层 kmac FSM error → alert[1] | 顶层 kmac FSM 错误触发 fatal alert |
| 20 | kmac.sv:1569 `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT EntropyFsmCheck_A | entropy FSM error → alert[1] (仅 EnMasking==1) | entropy FSM 错误触发 fatal alert |
| 21 | kmac.sv:1572 `ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT HashCountCheck_A | hash_count error → alert[1] (仅 EnMasking==1) | 哈希计数器错误触发 fatal alert |
| 22 | kmac.sv:1534-1540 `ASSERT_KNOWN ×7 | 所有输出信号已知 | 输出不为 X |
| 23 | kmac_app.sv:319 `ASSERT_STATIC_LINT_ERROR KmacSecIdleAcceptSwMsgNonDefault | SecIdleAcceptSwMsg==0 | 非默认值 lint 错误 |
| 24 | kmac_app.sv:903 `ASSERT_INIT SideloadKeySameToDigest_A | KeyMgrKeyW ≤ AppDigestW | sideload 密钥宽度不超过摘要宽度 |
| 25 | kmac_app.sv:904 `ASSERT_INIT AppIntfInRange_A | AppDigestW ∈ {128,192,256,384,512} | 摘要宽度在合法范围内 |
| 26 | kmac_core.sv:380 `ASSERT_INIT MaxKeyLenMatchToKey512_A | MaxKeyLen==512 | 密钥最大长度为 512 |
| 27 | kmac_core.sv:470 `ASSUME KmacEnStable_M | kmac_en 变化仅在 StKmacIdle/StTerminalError | kmac_en 在运算中不变 |
| 28 | kmac_core.sv:471 `ASSUME ModeStable_M | mode 变化仅在 StKmacIdle/StTerminalError | mode 在运算中不变 |
| 29 | kmac_core.sv:472 `ASSUME StrengthStable_M | strength 变化仅在 StKmacIdle/StTerminalError | strength 在运算中不变 |
| 30 | kmac_core.sv:476 `ASSUME KeyLengthStableWhenValid_M | key_valid 且非新上升沿 → key_len 稳定 | 密钥长度在有效期间不变 |
| 31 | kmac_core.sv:477 `ASSUME KeyDataStableWhenValid_M | key_valid 且非新上升沿 → key_data 稳定 | 密钥数据在有效期间不变 |
| 32 | kmac_msgfifo.sv:279 `ASSUME PackerDoneValid_a | process_i → flush_st==FlushIdle | process 仅在 flush 空闲时有效 |
| 33 | kmac_msgfifo.sv:282 `ASSUME MessageValid_a | fifo_valid_i → flush_st==FlushIdle | 消息仅在 flush 空闲时有效 |
| 34 | keccak_round.sv:587 `ASSERT_INIT WidthDivisableByDInWidth_A | Width % DInWidth == 0 | Keccak 状态宽度可被输入宽度整除 |
| 35 | keccak_round.sv:593 `ASSUME OneHot0ValidAndRun_A | $onehot0({valid_i, run_i}) | valid 和 run 互斥 |
| 36 | keccak_round.sv:596 `ASSUME ValidRunAssertStIdle_A | valid_i‖run_i → keccak_st==Idle | 输入仅在空闲时有效 |
| 37 | keccak_round.sv:599 `ASSUME ClearAssertStIdle_A | clear_i → keccak_st==Idle | 清除仅在空闲时有效 |
| 38 | kmac_entropy.sv:352 `ASSERT_KNOWN ModeKnown_A | mode_i 已知 | 熵模式不为 X |
| 39 | kmac_entropy.sv:457 `ASSUME ConsumeNotAssertWhenNotValid_M | consume 仅在 rand_valid 时有效 | 熵消费仅在有效时 |
| 40 | kmac_entropy.sv:738 `ASSERT_KNOWN RandStKnown_A | st 已知 | 熵 FSM 状态不为 X |
| 41 | kmac_entropy.sv:761 `ASSERT_INIT EdnBusWidth_A | ENDPOINT_BUS_WIDTH==32 | EDN 总线宽度为 32 |
| 42 | kmac_entropy.sv:774 `ASSERT_I PermutationCheck_A | 排列校验通过 | 熵排列常量正确 |
| 43 | sha3pad.sv:739 `ASSERT_INIT PrefixLessThanBlock_A | PrefixSize/8 < KeccakRate[4] | 前缀大小不超过块大小 |
| 44 | sha3pad.sv:745 `ASSERT_INIT MsgWidthidth_A | MsgWidth==64 | 消息宽度为 64 |
| 45 | sha3pad.sv:748-750 `ASSUME StartPulse_A/ProcessPulse_A/DonePulse_A | 控制 signal 单脉冲 | start/process/done 为单拍脉冲 |
| 46 | sha3pad.sv:761 `ASSUME StartProcessDoneMutex_a | start/process/done 互斥 | 控制信号不同时有效 |
| 47 | sha3pad.sv:769 | //`ASSUME Sequence_a (被注释!) | start→process→absorbed→done 序列 | **已降级/注释掉**: 命令序列约束未激活 |
| 48 | sha3pad.sv:808 `ASSUME MessageCondition_M | msg_valid&&msg_ready → process_valid&&!process_i | 消息仅在非 process 时接受 |
| 49 | sha3pad.sv:820 `ASSUME ModeStableDuringOp_M | mode 在运算中稳定 | 模式在运算期间不变 |
| 50 | sha3pad.sv:822 `ASSUME StrengthStableDuringOp_M | strength 在运算中稳定 | 强度在运算期间不变 |
| 51 | sha3.sv:525 `ASSUME SwRunInSqueezing_a | run_i → error_o.valid ‖ st==StSqueeze | run 仅在 squeeze 或错误态有效 |

## 四、树内参考

| # | 参考物 (绝对路径) | 类型 | 可对比什么 |
|---|---|---|---|
| 1 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac_reduced.sv | 参考实现 | 精简版 KMAC+SHA3+PRNG, 无 TL-UL; **消息掩码用动态 msg_mask (line 152-158) vs kmac.sv 用 static_mask (line 911-920)——关键对比点** |
| 2 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac_pkg.sv | 规范常量 | 稀疏编码值 (kmac_cmd_e, app_mux_sel_e, st_e)、LFSR seed/perm、错误码枚举 |
| 3 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/sha3_pkg.sv | 规范常量 | KeccakRate[5]、KeccakBitCapacity[5]、sha3_st_sparse_e 编码、keccak_st_e 编码 |

## 五、特殊结构提示

### 5-A. 常量替换动态值候选（HIGH PRIORITY）

**kmac.sv:906-927** — `g_msg_mask` 分支内, 声称 "Enhanced entropy masking with optimized performance", 但实际:
- `static_mask = {MsgWidth{1'b1}}` (全 1 常量) 替换了动态 `msg_mask` (来自 kmac_entropy 的 LFSR 输出)
- `msg_mask_permuted[i] = static_mask[RndCnstMsgPerm[i]]` → 等价于全 1 (常量排列全 1 仍全 1)
- `msg_data_masked[i] = msg_data[i] ^ ({MsgWidth{cfg_msg_mask}} & static_mask)` → 当 cfg_msg_mask=1 时 XOR 全 1 (取反), 非 PRNG 随机掩码
- 对比 **kmac_reduced.sv:152-166**: 正确实现用 `msg_mask[RndCnstMsgPerm[i]]` 和 `msg_masked[i] = msg[i] ^ msg_mask_permuted`
- **此为 SEC_CM MSG.MASKING (未在 hjson 声明但 kmac.hjson:560 `msg_mask` 字段暗示) 的实现缺陷: 动态 PRNG 掩码被常量全 1 替换, 破坏 SCA 对策**

### 5-B. 注释降级 SVA

**sha3pad.sv:769** — `//`ASSUME(Sequence_a, ...)` 被注释掉, 命令序列约束 (start→process→absorbed→done) 未被 SVA 强制执行; 上游可能靠 DV 环境 guarantee, 但 RTL 层无此合同

### 5-C. FSM TerminalError 延迟上报

**kmac_core.sv:227-235** — StTerminalError 中, `sparse_fsm_error_o` 需等 st_err_ct 累到 100 才置 1, 即错误检测延迟 100 周期; 其他 FSM (kmac_app, sha3, keccak_round, kmac_entropy) 均立即置 1; 检查此延迟是否符合预期

### 5-D. CFG_REGWEN 门控一致性

CFG_SHADOWED, ENTROPY_PERIOD, KEY_SHARE0/1, KEY_LEN, PREFIX 均声明 regwen: CFG_REGWEN; 检查 kmac_reg_top 中各寄存器的 we 信号是否均受 cfg_regwen_en 门控

### 5-E. KEY 侧载 vs SW 写入选择逻辑

kmac.sv:488 SW_KEY.KEY.MASKING 只管 SW 写入的 key share; sideload key 在 kmac_app.sv:766 处理; 检查 kmac_core 的 key_data_i 选择器: 当 sideload 有效时 SW key 是否被忽略 (不可泄露)

### 5-F. 熵模式不可逆转换

kmac.hjson:496-541 entropy_mode 一旦离开 idle_mode 不可返回 (仅 reset); 检查 kmac_entropy FSM 中 StRandReset → StRandIdle → StRandEdn 等状态转换是否无回跳路径
