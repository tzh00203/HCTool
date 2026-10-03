# otp_ctrl 盲预言机目录

## 元信息
- 树: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
- 扫描范围: hw/ip/otp_ctrl/rtl + hw/top_earlgrey/ip_autogen/otp_ctrl/rtl + hw/top_earlgrey/ip_autogen/otp_ctrl/data（hjson/SEC_CM 在 ip_autogen 下；ip_templates 下有 .tpl 版本）
- SEC_CM 声明数: 42 / SVA 数: 157 / sec_cm_testplan 条目数: 46

## 一、SEC_CM 声明 ↔ RTL 锚点
| # | SEC_CM 声明 (hjson:line) | RTL 锚点 (file:line) | 检验要点 |
|---|---|---|---|
| 1 | BUS.INTEGRITY (otp_ctrl.hjson:1864) | otp_ctrl.sv:125, otp_ctrl.sv:214 | intg_err_o 信号必须连到 fatal_bus_integ_error 锁存；两个来源：u_reg_core.intg_err_o 和 u_tlul_adapter_sram.intg_error_o |
| 2 | SECRET.MEM.SCRAMBLE (otp_ctrl.hjson:1867) | otp_ctrl_part_pkg.sv:49; otp_ctrl_part_buf.sv:302,315; otp_ctrl_dai.sv:384,397,491,516; otp_ctrl.sv:872 | 分区读写需经 PRESENT cipher 加解密；RndCnstKey 3组128bit密钥在 part_pkg.sv:50；scrmbl 模块执行加解密 |
| 3 | PART.MEM.DIGEST (otp_ctrl.hjson:1870) | otp_ctrl_part_pkg.sv:56; otp_ctrl_part_buf.sv:483,519,531,545; otp_ctrl_dai.sv:540,553,581,604,634,645,660; otp_ctrl.sv:873 | 64bit digest 校验锁定分区；RndCnstDigestConst/RndCnstDigestIV 在 part_pkg.sv:59,66；digest非零即锁定写 |
| 4 | DAI.FSM.SPARSE (otp_ctrl.hjson:1873) | otp_ctrl_dai.sv:96 | sparse_fsm_flop 编码 FSM；非法态必须触发 fatal_check_error |
| 5 | KDI.FSM.SPARSE (otp_ctrl.hjson:1876) | otp_ctrl_kdi.sv:314 | sparse_fsm_flop 编码 FSM；非法态必须触发 fatal_check_error |
| 6 | LCI.FSM.SPARSE (otp_ctrl.hjson:1879) | otp_ctrl_lci.sv:82 | sparse_fsm_flop 编码 FSM；非法态必须触发 fatal_check_error |
| 7 | PART.FSM.SPARSE (otp_ctrl.hjson:1882) | otp_ctrl_part_buf.sv:120; otp_ctrl_part_unbuf.sv:90 | buf/unbuf 分区 FSM 均用 sparse_fsm_flop |
| 8 | SCRMBL.FSM.SPARSE (otp_ctrl.hjson:1885) | otp_ctrl_scrmbl.sv:242 | scramble datapath FSM 用 sparse_fsm_flop |
| 9 | TIMER.FSM.SPARSE (otp_ctrl.hjson:1888) | otp_ctrl_lfsr_timer.sv:209 | LFSR timer FSM 用 sparse_fsm_flop |
| 10 | DAI.CTR.REDUN (otp_ctrl.hjson:1891) | otp_ctrl_dai.sv:781 | prim_count cross-counter 实例 u_prim_count；cnt_err 需连到 fatal_check_error |
| 11 | KDI_SEED.CTR.REDUN (otp_ctrl.hjson:1894) | otp_ctrl_kdi.sv:217 | prim_count u_prim_count_seed；seed 计数冗余 |
| 12 | KDI_ENTROPY.CTR.REDUN (otp_ctrl.hjson:1897) | otp_ctrl_kdi.sv:235 | prim_count u_prim_count_entropy；entropy 计数冗余 |
| 13 | LCI.CTR.REDUN (otp_ctrl.hjson:1900) | otp_ctrl_lci.sv:243 | prim_count u_prim_count；LCI 地址计数冗余 |
| 14 | PART.CTR.REDUN (otp_ctrl.hjson:1903) | otp_ctrl_part_buf.sv:623 | prim_count u_prim_count；分区地址计数冗余 |
| 15 | SCRMBL.CTR.REDUN (otp_ctrl.hjson:1906) | otp_ctrl_scrmbl.sv:285 | prim_count u_prim_count；scramble 计数冗余 |
| 16 | TIMER_INTEG.CTR.REDUN (otp_ctrl.hjson:1909) | otp_ctrl_lfsr_timer.sv:147 | prim_count u_prim_count_integ；integrity check 定时器冗余 |
| 17 | TIMER_CNSTY.CTR.REDUN (otp_ctrl.hjson:1912) | otp_ctrl_lfsr_timer.sv:165 | prim_count u_prim_count_cnsty；consistency check 定时器冗余 |
| 18 | TIMER.LFSR.REDUN (otp_ctrl.hjson:1915) | otp_ctrl_lfsr_timer.sv:93 | prim_double_lfsr u_prim_double_lfsr；LFSR 双份冗余 |
| 19 | DAI.FSM.LOCAL_ESC (otp_ctrl.hjson:1918) | otp_ctrl_dai.sv:689 | cnt_err 或 fatal_macro/check_error 时 FSM 跳 ErrorSt |
| 20 | LCI.FSM.LOCAL_ESC (otp_ctrl.hjson:1921) | otp_ctrl_lci.sv:227 | cnt_err 时 FSM 跳 terminal error state |
| 21 | KDI.FSM.LOCAL_ESC (otp_ctrl.hjson:1924) | otp_ctrl_kdi.sv:562 | cnt_err 时 FSM 跳 terminal error state |
| 22 | PART.FSM.LOCAL_ESC (otp_ctrl.hjson:1927) | otp_ctrl_part_buf.sv:600,607; otp_ctrl_part_unbuf.sv:319 | ECC 错误或 cnt_err 时跳 terminal state |
| 23 | SCRMBL.FSM.LOCAL_ESC (otp_ctrl.hjson:1930) | otp_ctrl_scrmbl.sv:435 | cnt_err 时跳 terminal error state |
| 24 | TIMER.FSM.LOCAL_ESC (otp_ctrl.hjson:1933) | otp_ctrl_lfsr_timer.sv:356 | cnt_err 或 chk_timeout 时跳 ErrorSt |
| 25 | DAI.FSM.GLOBAL_ESC (otp_ctrl.hjson:1936) | otp_ctrl_dai.sv:689 | lc_escalate_en_i=On 时 FSM 跳 ErrorSt |
| 26 | LCI.FSM.GLOBAL_ESC (otp_ctrl.hjson:1939) | otp_ctrl_lci.sv:227 | lc_tx_test_true_loose(escalate_en_i) 时跳 terminal |
| 27 | KDI.FSM.GLOBAL_ESC (otp_ctrl.hjson:1942) | otp_ctrl_kdi.sv:562 | escalate_en 时跳 terminal |
| 28 | PART.FSM.GLOBAL_ESC (otp_ctrl.hjson:1945) | otp_ctrl_part_buf.sv:607; otp_ctrl_part_unbuf.sv:326 | escalate_en 时跳 terminal |
| 29 | SCRMBL.FSM.GLOBAL_ESC (otp_ctrl.hjson:1948) | otp_ctrl_scrmbl.sv:435 | escalate_en 时跳 terminal |
| 30 | TIMER.FSM.GLOBAL_ESC (otp_ctrl.hjson:1951) | otp_ctrl_lfsr_timer.sv:356 | escalate_en 时跳 ErrorSt |
| 31 | PART.DATA_REG.INTEGRITY (otp_ctrl.hjson:1954) | otp_ctrl_part_buf.sv:664; otp_ctrl_part_unbuf.sv:373 | 64bit ECC 保护 buf 寄存器；otp_ctrl_ecc_reg 示例 Width==64 断言 (ecc_reg.sv:30) |
| 32 | PART.DATA_REG.BKGN_CHK (otp_ctrl.hjson:1957) | otp_ctrl_part_buf.sv:347,366,420,459,471,484,520,532,546; otp_ctrl.sv:628 | lfsr_timer 定期触发 integrity/consistency check；digest 重算比对 |
| 33 | PART.MEM.REGREN (otp_ctrl.hjson:1960) | otp_ctrl.sv:305 | named_part_access_pre(reg2hw) 提取 SW 分区 read_lock CSR；READ_LOCK 寄存器 rw0c 控制 |
| 34 | PART.MEM.SW_UNREADABLE (otp_ctrl.hjson:1963) | otp_ctrl_part_buf.sv:732; otp_ctrl_part_unbuf.sv:443 | digest 锁定后 secret 分区对 SW 不可读；read_lock=MuBi8True 屏蔽 TL-UL 读 |
| 35 | PART.MEM.SW_UNWRITABLE (otp_ctrl.hjson:1966) | otp_ctrl_part_buf.sv:712; otp_ctrl_part_unbuf.sv:423 | digest 锁定后所有分区对 SW 不可写；write_lock=MuBi8True 屏蔽写 |
| 36 | LC_PART.MEM.SW_NOACCESS (otp_ctrl.hjson:1969) | otp_ctrl.sv:310,311 | part_access_pre[LifeCycleIdx].write_lock=MuBi8True; .read_lock=MuBi8True |
| 37 | ACCESS.CTRL.MUBI (otp_ctrl.hjson:1972) | otp_ctrl_part_buf.sv:54; otp_ctrl_dai.sv:44; otp_ctrl_part_unbuf.sv:44; otp_ctrl.sv:301 | 分区到 DAI 的 access control 信号用 mubi8 编码；prim_mubi8_sender 实例化 |
| 38 | TOKEN_VALID.CTRL.MUBI (otp_ctrl.hjson:1975) | otp_ctrl.sv:62,1376 | test_tokens_valid/rma_token_valid/secrets_valid 用 prim_lc_sender 输出 lc_tx_t MUBI |
| 39 | LC_CTRL.INTERSIG.MUBI (otp_ctrl.hjson:1978) | otp_ctrl.sv:55 | lc_creator_seed_sw_rw_en_i 等 5 路 lc_tx_t 输入经 prim_lc_sync 同步后用于访问控制 |
| 40 | DIRECT_ACCESS.CONFIG.REGWEN (otp_ctrl.hjson:1981) | otp_ctrl.sv:115 | DIRECT_ACCESS_REGWEN rw0c 控制 DAI CMD/ADDR/WDATA 寄存器写使能 |
| 41 | CHECK_TRIGGER.CONFIG.REGWEN (otp_ctrl.hjson:1984) | otp_ctrl.sv:115 | CHECK_TRIGGER_REGWEN rw0c 控制 CHECK_TRIGGER 寄存器写使能 |
| 42 | CHECK.CONFIG.REGWEN (otp_ctrl.hjson:1987) | otp_ctrl.sv:115 | CHECK_REGWEN rw0c 控制 CHECK_TIMEOUT/INTEGRITY_CHECK_PERIOD/CONSISTENCY_CHECK_PERIOD 寄存器写使能 |
| 43 | TEST.BUS.LC_GATED (sec_cm_testplan:258) | 缺失! | 测试总线受 lc_dft_en 门控；在 OTP 宏内部实现，开源 RTL 无锚点 |
| 44 | TEST_TL_LC_GATE.FSM.SPARSE (sec_cm_testplan:268) | 缺失! | 测试 TL-UL LC 门控 FSM sparse 编码；OTP 宏内部实现，开源 RTL 无锚点。注释掉的断言 otp_ctrl.sv:1493 |
| 45 | MACRO.MEM.INTEGRITY (sec_cm_testplan:293) | 缺失! | OTP 宏存储器 ECC 完整性；闭源 prim_otp 内部实现 |
| 46 | MACRO.MEM.CM (sec_cm_testplan:298) | 缺失! | OTP 宏附加对策；闭源 prim_otp 内部，测试标注 N/A |

## 二、行为性描述句（hjson 原文 → 检验点）
| # | hjson 原文 (file:line) | 检验点 |
|---|---|---|
| 1 | "Secret partitions are scrambled with a full-round PRESENT cipher." (otp_ctrl.hjson:1868) | SECRET 分区读写必须经 PRESENT 31-round 加解密；scrmbl 模块 NumPresentRounds=31 (top_specific_pkg.sv:66) |
| 2 | "Integrity of buffered partitions is ensured via a 64bit digest." (otp_ctrl.hjson:1871) | buf 分区 digest 非0→写锁定；digest=CREATOR_SW_CFG_DIGEST 等 CSR 暴露；digest 算法 Davies-Meyer on PRESENT |
| 3 | "This error should never occur during normal operation and is not recoverable." (otp_ctrl.hjson:2279 MACRO_ERROR) | MacroError → fatal_macro_error 锁存→alert 持续触发 |
| 4 | "An uncorrectable ECC error...This error should never occur during normal operation and is not recoverable." (otp_ctrl.hjson:2295) | MacroEccUncorrError → fatal_macro_error（非 VendorTest 分区）；VendorTest 分区降级为 corr error |
| 5 | "This error indicates that a locked memory region has been accessed." (otp_ctrl.hjson:2316 ACCESS_ERROR) | AccessError → otp_error 中断（可恢复）；不进入 terminal state |
| 6 | "An ECC, integrity or consistency mismatch...This error should never occur during normal operation and is not recoverable. This error triggers an fatal_check_error alert." (otp_ctrl.hjson:2323 CHECK_FAIL_ERROR) | CheckFailError → fatal_check_error 锁存→alert→所有 FSM 进入 terminal state |
| 7 | "The FSM...has reached an invalid state, or the FSM has been moved into a terminal error state due to an escalation action via lc_escalate_en_i." (otp_ctrl.hjson:2330 FSM_STATE_ERROR) | FsmStateError → fatal_check_error→本地 escalation→所有 FSM terminal |
| 8 | "This alert triggers if hardware detects an uncorrectable error during an OTP transaction" (otp_ctrl.hjson:72 fatal_macro_error) | fatal_macro_error 一旦锁存不解除（需 reset）；otp_ctrl.sv:416-418 锁存逻辑 |
| 9 | "This alert triggers if any of the background checks fails." (otp_ctrl.hjson:75 fatal_check_error) | fatal_check_error 一旦锁存不解除；包括 digest/ECC/consistency/timeout/FSM 错误 |
| 10 | "The life cycle partition is not directly readable nor writable via software." (otp_ctrl.hjson:1970) | part_access_pre[LifeCycleIdx] 的 read_lock/write_lock 均=MuBi8True (otp_ctrl.sv:311-312) |
| 11 | "Secret buffered partitions become unreadable to software once they are locked via the digest." (otp_ctrl.hjson:1964) | digest 锁定后 secret 分区 read_lock=MuBi8True；TL-UL 读返回 AccessError |
| 12 | "All partitions become unwritable by software once they are locked via the digest." (otp_ctrl.hjson:1967) | digest 锁定后 write_lock=MuBi8True；DAI 写返回 AccessError |
| 13 | "Unbuffered ('software') partitions can be read-locked via a CSR until the next system reset." (otp_ctrl.hjson:1961) | READ_LOCK CSR rw0c 控制；regwen=DIRECT_ACCESS_REGWEN |
| 14 | "This signal moves all FSMs within OTP into the error state." (otp_ctrl.hjson:1752 lc_escalate_en) | lc_escalate_en_i 经 prim_lc_sync 同步后分发到所有子 FSM；GLOBAL_ESC 逻辑 |
| 15 | "OTP initialization failure triggers fatal alert" (testplan:86) | init 阶段 ECC uncorr error→fatal_macro_error→alert |
| 16 | "if lc_escalation_en is enabled, verify that alert is triggered and OTP_CTRL entered terminal state" (testplan:166) | escalate_en→所有 FSM ErrorSt→fatal_check_error→alert |

## 三、SVA 清单（行为合同）
| # | 断言 (file:line) | 内容摘要 | 约束的预期行为 |
|---|---|---|---|
| 1 | OtpIfWidth_A (otp_ctrl.sv:89) | OtpIfWidth == ScrmblBlockWidth | OTP 接口宽度必须等于 scramble block 宽度 |
| 2 | OtpErrorCode0_A..4_A (otp_ctrl.sv:92-98) | 5 个错误码与 macro_pkg 一致 | otp_ctrl 与 otp_ctrl_macro_pkg 错误枚举同步 |
| 3 | PartSelMustBeOnehot_A (otp_ctrl.sv:240) | $onehot0(tlul_part_sel_oh) | TL-UL 窗口分区选择最多一个有效 |
| 4 | CreatorRootKeyShare0Size_A (otp_ctrl.sv:1425) | KeyMgrKeyWidth == CreatorRootKeyShare0Size*8 | 根密钥宽度匹配 |
| 5 | CreatorRootKeyShare1Size_A (otp_ctrl.sv:1426) | KeyMgrKeyWidth == CreatorRootKeyShare1Size*8 | 根密钥宽度匹配 |
| 6 | FlashDataKeySeedSize_A (otp_ctrl.sv:1427) | FlashKeySeedWidth == FlashDataKeySeedSize*8 | Flash 种子宽度匹配 |
| 7 | FlashAddrKeySeedSize_A (otp_ctrl.sv:1428) | FlashKeySeedWidth == FlashAddrKeySeedSize*8 | Flash 种子宽度匹配 |
| 8 | SramDataKeySeedSize_A (otp_ctrl.sv:1429) | SramKeySeedWidth == SramDataKeySeedSize*8 | SRAM 种子宽度匹配 |
| 9 | RmaTokenSize_A (otp_ctrl.sv:1431) | LcTokenWidth == RmaTokenSize*8 | RMA token 宽度匹配 |
| 10 | TestUnlockTokenSize_A (otp_ctrl.sv:1432) | LcTokenWidth == TestUnlockTokenSize*8 | 解锁 token 宽度匹配 |
| 11 | TestExitTokenSize_A (otp_ctrl.sv:1433) | LcTokenWidth == TestExitTokenSize*8 | 退出 token 宽度匹配 |
| 12 | LcStateSize_A (otp_ctrl.sv:1434) | LcStateWidth == LcStateSize*8 | LC 状态宽度匹配 |
| 13 | LcTransitionCntSize_A (otp_ctrl.sv:1435) | LcCountWidth == LcTransitionCntSize*8 | LC 计数器宽度匹配 |
| 14 | KeyNonceSize0_A..6_A (otp_ctrl_kdi.sv:66-72) | 7 个 KDI 密钥/nonce 宽度 ≤256 且 64 整除 | KDI 密钥衍生宽度约束 |
| 15 | EntropyWidthDividesDigestBlockWidth_A (otp_ctrl_kdi.sv:75) | ScrmblKeyWidth % EdnDataWidth == 0 | EDN 宽度整除 scramble 密钥宽度 |
| 16 | NonceWidth_A (otp_ctrl_kdi.sv:78) | NumNonceChunks*ScrmblBlockWidth == SramNonceWidth | nonce chunk 数量约束 |
| 17 | OffsetMustBeBlockAligned_A (otp_ctrl_part_unbuf.sv:82; otp_ctrl_part_buf.sv:104) | 分区偏移 block 对齐 | 分区偏移必须按 scramble block 对齐 |
| 18 | SizeMustBeBlockAligned_A (otp_ctrl_part_unbuf.sv:83; otp_ctrl_part_buf.sv:105) | 分区大小 block 对齐 | 分区大小必须按 scramble block 对齐 |
| 19 | DigestOffsetMustBeRepresentable_A (otp_ctrl_part_unbuf.sv:84; otp_ctrl_part_buf.sv:106) | digest 偏移可表示 | digest 偏移必须在整数范围内 |
| 20 | LcValueMustBeWiderThanNativeOtpWidth_A (otp_ctrl_lci.sv:76) | LcValueWidth >= OtpWidth | LC 值宽度不少于 OTP 原生宽度 |
| 21 | NumMaxPresentRounds_A (otp_ctrl_scrmbl.sv:140) | NumPresentRounds <= 31 | PRESENT 加密轮数上限 31 |
| 22 | OtpPartBufSize_A (otp_ctrl_part_buf.sv:825) | Info.size > ScrmblBlockWidth/8 | buf 分区大小必须大于 1 个 block |
| 23 | CheckNativeOtpWidth0_A,1_A (otp_ctrl_dai.sv:89-90) | ScrmblBlockWidth%OtpWidth==0, 32%OtpWidth==0 | OTP 原生宽度整除约束 |
| 24 | PartEndMax_A (otp_ctrl_dai.sv:717) | PartEndInt <= (1<<OtpByteAddrWidth) | 分区结束地址不溢出 |
| 25 | EdnIsWideEnough_A (otp_ctrl_lfsr_timer.sv:117) | EdnDataWidth >= LfsrWidth | EDN 宽度不少于 LFSR 宽度 |
| 26 | WidthMustBe64bit_A (otp_ctrl_ecc_reg.sv:30) | Width == 64 | ECC 寄存器必须 64bit |
| 27 | CtrlDaiFsmCheck_A (otp_ctrl.sv:1451) | ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT | DAI FSM 错误触发 alert |
| 28 | CtrlKdiFsmCheck_A (otp_ctrl.sv:1453) | ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT | KDI FSM 错误触发 alert |
| 29 | CtrlLciFsmCheck_A (otp_ctrl.sv:1455) | ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT | LCI FSM 错误触发 alert |
| 30 | CtrlLfsrTimerFsmCheck_A (otp_ctrl.sv:1457) | ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT | Timer FSM 错误触发 alert |
| 31 | CtrlScrambleFsmCheck_A (otp_ctrl.sv:1459) | ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT | Scrmbl FSM 错误触发 alert |
| 32 | CtrlPartUnbufFsmCheck_A (otp_ctrl.sv:1122) | ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT | Unbuf 分区 FSM 错误触发 alert |
| 33 | CtrlPartBufFsmCheck_A (otp_ctrl.sv:1177) | ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT | Buf 分区 FSM 错误触发 alert |
| 34 | CtrlPartLcFsmCheck_A (otp_ctrl.sv:1246) | ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT | LC 分区 FSM 错误触发 alert |
| 35 | CntIntegCheck_A (otp_ctrl.sv:1463) | ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT | Integrity check 计数器错误触发 alert |
| 36 | CntCnstyCheck_A (otp_ctrl.sv:1465) | ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT | Consistency check 计数器错误触发 alert |
| 37 | CntDaiCheck_A (otp_ctrl.sv:1467) | ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT | DAI 计数器错误触发 alert |
| 38 | CntKdiSeedCheck_A (otp_ctrl.sv:1469) | ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT | KDI seed 计数器错误触发 alert |
| 39 | CntKdiEntropyCheck_A (otp_ctrl.sv:1471) | ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT | KDI entropy 计数器错误触发 alert |
| 40 | CntLciCheck_A (otp_ctrl.sv:1473) | ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT | LCI 计数器错误触发 alert |
| 41 | CntScrmblCheck_A (otp_ctrl.sv:1475) | ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT | Scrmbl 计数器错误触发 alert |
| 42 | CntPartBufCheck_A (otp_ctrl.sv:1179) | ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT | Part buf 计数器错误触发 alert |
| 43 | CntPartLcCheck_A (otp_ctrl.sv:1248) | ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT | Part LC 计数器错误触发 alert |
| 44 | DoubleLfsrCheck_A (otp_ctrl.sv:1479) | ASSERT_PRIM_DOUBLE_LFSR_ERROR_TRIGGER_ALERT | 双份 LFSR 错误触发 alert |
| 45 | RegWeOnehotCheck_A (otp_ctrl.sv:1483) | ASSERT_PRIM_REG_WE_ONEHOT_ERROR_TRIGGER_ALERT | reg_we one-hot 错误触发 alert |
| 46 | **[注释/降级]** TlLcGateFsm_A (otp_ctrl.sv:1493) | ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT 被注释 | TL-UL LC gate FSM 错误应触发 alert——**当前未激活** |
| 47 | **[注释/降级]** PrimFsmCheck_A (otp_ctrl.sv:1495) | ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT 被注释 | prim_otp FSM 错误应触发 alert——**当前未激活** |
| 48 | **[注释/降级]** PrimRegWeOnehotCheck_A (otp_ctrl.sv:1497) | ASSERT_PRIM_REG_WE_ONEHOT_ERROR_TRIGGER_ALERT 被注释 | prim_otp reg_we 错误应触发 alert——**当前未激活** |
| 49 | wePulse (otp_ctrl_core_reg_top.sv:2566) | ASSERT_PULSE reg_we | 写使能脉冲检测 |
| 50 | rePulse (otp_ctrl_core_reg_top.sv:2567) | ASSERT_PULSE reg_re | 读使能脉冲检测 |
| 51-100 | ASSERT_KNOWN 系列 (otp_ctrl.sv:1437-1448; otp_ctrl_kdi.sv:592-602; otp_ctrl_part_unbuf.sv:167,488-500; otp_ctrl_part_buf.sv:774-791; otp_ctrl_dai.sv:840-855; otp_ctrl_lci.sv:294-302; otp_ctrl_scrmbl.sv:162-165; otp_ctrl_ecc_reg.sv:99-103; otp_ctrl_lfsr_timer.sv:392-396) | 所有输出信号不为 X/Z | 已知值检查：确保所有输出接口信号不含 X |

## 四、树内参考
| # | 参考物 (绝对路径) | 类型 | 可对比什么 |
|---|---|---|---|
| 1 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_part_buf.sv vs otp_ctrl_part_unbuf.sv | 兄弟模块 | buf/unbuf 分区 FSM 结构同构：状态机、access control、ECC、digest 逻辑可互相比对 |
| 2 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_token_const.sv | 参考实现 | PRESENT cipher Davies-Meyer hash 计算；可用于验证 token hash 计算正确性 |
| 3 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_scrmbl.sv | 参考实现 | scramble datapath：PRESENT 加解密、digest 计算；enc/dec key LUT 预计算 |
| 4 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/otp_ctrl/rtl/otp_ctrl_pkg.sv | 规范注释 | 顶层常量定义：ScrmblKeyWidth=128, ScrmblBlockWidth=64, 密钥宽度参数 |
| 5 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_top_specific_pkg.sv | 规范注释 | RndCnstLfsrSeedDefault, RndCnstLfsrPermDefault, RndCnstScrmblKeyInitDefault 默认值 |
| 6 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_part_pkg.sv:50-71 | 规范注释 | 混淆常量：RndCnstKey (3×128bit), RndCnstDigestConst (4×128bit), RndCnstDigestIV (4×64bit)——**必须脚本解码验证** |
| 7 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_macro_pkg.sv | 规范注释 | OTP 宏命令 sparse 编码 (Read=7'b1000101, Write=7'b0110111, ReadRaw=7'b1111001, WriteRaw=7'b1100010, Init=7'b0101100)——Hamming distance 4 |
| 8 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_ecc_reg.sv | 参考实现 | ECC 寄存器实现：64bit 数据 + ECC 编码/解码；用于验证 PART.DATA_REG.INTEGRITY |

## 五、特殊结构提示

### 5.1 混淆常量（必须脚本验证）
- `otp_ctrl_part_pkg.sv:50-71`: RndCnstKey, RndCnstDigestConst, RndCnstDigestIV 是编译时随机常量。这些是 **obfuscated constant mismatch** 的候选——必须用脚本（非心算）验证解码后值是否与文档匹配。
- `otp_ctrl_pkg.sv:63-74`: OTP_LC_DATA_DEFAULT 中的 `valid: (1'b1 && 1'b1) || (1'b0 && 1'b0)` 和 `state: lc_ctrl_state_pkg::LcStTestUnlocked0 | (lc_ctrl_state_pkg::LcStRma & {8{(&1'b1)}})` 包含混淆表达式——需脚本化常量折叠验证。
- `otp_ctrl_pkg.sv:121-130`: OTP_KEYMGR_KEY_DEFAULT 中 4 个 256bit 十六进制常量。
- `otp_ctrl_pkg.sv:157-163`: FLASH_OTP_KEY_RSP_DEFAULT 中混淆表达式如 `(~(|4'h0)) || (&(~4'hF))`, `((1'b1 << 1) >> 1) !== 1'b0`。

### 5.2 注释掉的 SVA（候选漏洞信号）
- `otp_ctrl.sv:1493-1498`: 3 个 ASSERT_PRIM_* 断言被注释掉，对应 TEST_TL_LC_GATE.FSM.SPARSE 和 prim_otp 内部 FSM/REG_WE 检查。这是 **sec-cm-mismatch** 的候选：SEC_CM 声明存在但断言未激活。

### 5.3 SEC_CM 声明无 RTL 锚点
- **TEST.BUS.LC_GATED**: sec_cm_testplan 有条目但 hjson countermeasures 无声明、RTL 无锚点——OTP 宏内部实现。
- **TEST_TL_LC_GATE.FSM.SPARSE**: 同上，注释掉的断言 otp_ctrl.sv:1493 是唯一痕迹。
- **MACRO.MEM.INTEGRITY / MACRO.MEM.CM**: 闭源 prim_otp 内部，开源 RTL 完全不可见。

### 5.4 分区访问控制 MUBI 编码
- `otp_ctrl_part_buf.sv:695-740` 和 `otp_ctrl_part_unbuf.sv:406-451`: prim_mubi8_sender 实例化链——write_lock/read_lock 信号从分区 FSM 输出经 MUBI8 sender 传播到 DAI。检验要点：MUBI8 值必须为 MuBi8True/MuBi8False，中间值应触发错误。
- `otp_ctrl_part_pkg.sv:528-549`: part_access_pre 初始化使用 MuBi8False/MuBi8True 常量。

### 5.5 Fatal alert 锁存语义
- `otp_ctrl.sv:414-451`: fatal_macro_error_q, fatal_check_error_q, fatal_bus_integ_error_q 一旦置1不再清除（需 reset）。锁存后所有 FSM 进入 terminal state（lc_escalate_en[k] = lc_ctrl_pkg::On）。
- **检验要点**：锁存条件必须覆盖所有致命错误源，不能遗漏。

### 5.6 分区锁定与 digest 语义
- 5 个 unbuffered 分区 (VendorTest, CreatorSwCfg, OwnerSwCfg, RotCreatorAuthCodesign, RotCreatorAuthState)：digest 由 SW 通过 DAI 写入，写后锁定。
- 6 个 buffered 分区 (HwCfg0, HwCfg1, Secret0, Secret1, Secret2, LifeCycle)：digest 由 HW 计算，初始化后锁定。
- LifeCycle 分区：DAI 完全不可访问（LC_PART.MEM.SW_NOACCESS）。

### 5.7 OTP 宏命令 sparse 编码
- `otp_ctrl_macro_pkg.sv:57-64`: 5 个命令码 Hamming distance = 4，这是 FSM sparse encoding 的另一种形式。注入者如果替换命令码可能导致 OTP 宏行为异常。
