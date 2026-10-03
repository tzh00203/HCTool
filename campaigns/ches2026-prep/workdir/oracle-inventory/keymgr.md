# keymgr 盲预言机目录

## 元信息
- 树: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
- 扫描范围: hw/ip/keymgr/{rtl,data,doc}
- SEC_CM 声明数: 25 / SVA 数: 44 / testplan 条目数: 35

## 一、SEC_CM 声明 ↔ RTL 锚点
| # | SEC_CM 声明 (hjson:line) | RTL 锚点 (file:line) | 检验要点 |
|---|---|---|---|
| 1 | BUS.INTEGRITY (keymgr.hjson:325) | keymgr.sv:140 | reg_top u_reg 必须输出 intg_err_o；若 TL 完整性错误则 regfile_intg_err=1 并传播至 fault_code[FaultRegIntg] |
| 2 | CONFIG.SHADOW (keymgr.hjson:328) | keymgr.sv:141 | CONTROL_SHADOWED, RESEED_INTERVAL_SHADOWED, MAX_*_KEY_VER_SHADOWED 均 shadowed=true；shadowed_storage_err_o / shadowed_update_err_o 必须接至 fault_code / err_code |
| 3 | OP.CONFIG.REGWEN (keymgr.hjson:334) | keymgr.sv:142 | op_start 有效后 cfg_regwen 由 keymgr_cfg_en 拉低；受保护寄存器(START,CONTROL_SHADOWED,SIDELOAD_CLEAR,Salt,KEY_VERSION)在操作期间不可写 |
| 4 | RESEED.CONFIG.REGWEN (keymgr.hjson:340) | keymgr.sv:142 | RESEED_INTERVAL_REGWEN (swaccess=rw0c) 控制 RESEED_INTERVAL_SHADOWED 写使能；一旦清零不可恢复直到复位 |
| 5 | SW_BINDING.CONFIG.REGWEN (keymgr.hjson:345) | keymgr.sv:142 | SW_BINDING_REGWEN (swaccess=rw0c, hwext) 控制 SEALING/ATTEST_SW_BINDING；成功 advance 后硬件解锁(sw_binding_unlock_o) |
| 6 | MAX_KEY_VER.CONFIG.REGWEN (keymgr.hjson:352) | keymgr.sv:143 | MAX_*_KEY_VER_REGWEN (swaccess=rw0c) 控制 MAX_*_KEY_VER_SHADOWED 写使能 |
| 7 | LC_CTRL.INTERSIG.MUBI (keymgr.hjson:357) | keymgr.sv:60 | lc_keymgr_en_i 经 prim_lc_sync 同步后用 lc_tx_test_true_strict 判定；若非 MuBi On 则 en_i=0 导致 FSM 进入 Wipe/Invalid |
| 8 | CONSTANTS.CONSISTENCY (keymgr.hjson:361) | keymgr.sv:509 | keymgr_input_checks 中 valid_chk(|value & ~&value) 检查 creator_seed/owner_seed 不全0不全1；违反则 adv_dvalid=0 导致 invalid_data |
| 9 | INTERSIG.CONSISTENCY (keymgr.hjson:366) | keymgr.sv:510 | keymgr_input_checks 对 devid_i(otp_device_id) 和 health_state_i(lc_keymgr_div) 做 valid_chk；违反则 adv_dvalid[Creator]=0 |
| 10 | HW.KEY.SW_NOACCESS (keymgr.hjson:371) | keymgr.sv:589 | sideload key 通过 keymgr_sideload_key_ctrl 独立存储；SW 只能读 sw_share0/1_output，其数据来自 data_sw_en 门控的 kmac_data，非 sideload 路径 |
| 11 | OUTPUT_KEYS.CTRL.REDUN (keymgr.hjson:376) | keymgr.sv:599 + keymgr.sv:625 | sideload: data_hw_en + data_valid 双控；sw output: data_sw_en + data_valid + hw_key_sel 三重门控；缺一则用 entropy 覆写（sw）或 key 不更新（hw） |
| 12 | CTRL.FSM.SPARSE (keymgr.hjson:393) | keymgr_ctrl.sv:260 | PRIM_FLOP_SPARSE_FSM(u_state_regs, state_d, state_q, state_e, StCtrlReset)，10-bit 稀疏编码 HD≥5；default 态设 state_intg_err_d=1 |
| 13 | DATA.FSM.SPARSE (keymgr.hjson:397) | keymgr_data_en_state.sv:68 | PRIM_FLOP_SPARSE_FSM(u_state_regs, state_d, state_q, state_e, StCtrlDataIdle)，10-bit 稀疏编码 HD≥5；default 态设 fsm_err_o=1 |
| 14 | CTRL.FSM.LOCAL_ESC (keymgr.hjson:402) | keymgr_ctrl.sv:462 | inv_state = \|fault_o；任何 async/sync fault 使 inv_state=1，FSM 立即跳 StCtrlWipe→StCtrlInvalid |
| 15 | CTRL.FSM.CONSISTENCY (keymgr.hjson:409) | keymgr_err.sv:124 | state_change_err(vld_state_change_q & !adv_op) + op_state_cmd_err 检查 FSM 转换与 SW 命令一致；违反触发 AsyncFaultFsmChk |
| 16 | CTRL.FSM.GLOBAL_ESC (keymgr.hjson:414) | keymgr_ctrl.sv:20 | en_i 来自 lc_tx_test_true_strict(lc_keymgr_en)；en_i=0 时 disable_sel=1，所有状态检查 !en_i → StCtrlWipe |
| 17 | CTRL.CTR.REDUN (keymgr.hjson:420) | keymgr_ctrl.sv:420 | prim_count u_cnt 用双份计数器；cnt_err → inv_state → StCtrlWipe；ASSERT CtrlCntAlertCheck_A 验证 cnt_err 触发 fatal alert |
| 18 | KMAC_IF.FSM.SPARSE (keymgr.hjson:425) | keymgr_kmac_if.sv:169 | PRIM_FLOP_SPARSE_FSM(u_state_regs, state_d, state_q, data_state_e, StIdle)，10-bit 稀疏编码 HD≥5；default 态设 fsm_error_o=1 |
| 19 | KMAC_IF.CTR.REDUN (keymgr.hjson:430) | keymgr_kmac_if.sv:142 | prim_count u_cnt 用双份计数器；cnt_err → state_d=StError + fsm_error_o=1 |
| 20 | KMAC_IF_CMD.CTRL.CONSISTENCY (keymgr.hjson:435) | keymgr_kmac_if.sv:374 | one_hot_err: \|(enables_d & enables_sub) 检测非 one-hot；cmd_consty_err: 命令在事务中途改变；两者合并为 cmd_error_o |
| 21 | KMAC_IF_DONE.CTRL.CONSISTENCY (keymgr.hjson:443) | keymgr_kmac_if.sv:348 | kmac_done_err: ~kmac_done_vld & kmac_data_i.done 检测非预期窗口 done；粘性锁存 |
| 22 | RESEED.CTR.REDUN (keymgr.hjson:448) | keymgr_reseed_ctrl.sv:94 | prim_count u_reseed_cnt 用双份计数器；cnt_err_o → reseed_cnt_err_i → AsyncFaultRCntErr |
| 23 | SIDE_LOAD_SEL.CTRL.CONSISTENCY (keymgr.hjson:453) | keymgr_sideload_key_ctrl.sv:203 | valid_tracking_q 追踪哪些 slot 应为 valid；sideload_sel_err_o = \|(~valid_tracking_q & valids) 检测非预期 valid |
| 24 | SIDELOAD_CTRL.FSM.SPARSE (keymgr.hjson:461) | keymgr_sideload_key_ctrl.sv:63 | PRIM_FLOP_SPARSE_FSM(u_state_regs, state_d, state_q, keymgr_sideload_e, StSideloadReset)，10-bit 稀疏编码 HD≥5；default 态设 fsm_err_o=1 |
| 25 | CTRL.KEY.INTEGRITY (keymgr.hjson:465) | keymgr_ctrl.sv:302 | key_state_q 用 prim_secded_inv_72_64_enc 编码；每 word 经 prim_secded_inv_72_64_dec 解码检查；ecc_errs 任何 bit 错 → AsyncFaultKeyEcc |

## 二、行为性描述句（hjson 原文 → 检验点）
| # | hjson 原文 (file:line) | 检验点 |
|---|---|---|
| 1 | "End-to-end bus integrity scheme." (keymgr.hjson:326) | u_reg.intg_err_o 必须接至 fault_code[FaultRegIntg]；TL 完整性错误触发 fatal alert |
| 2 | "Various critical registers are shadowed: including operation control, reseed interval, and key max version" (keymgr.hjson:330) | CONTROL_SHADOWED, RESEED_INTERVAL_SHADOWED, MAX_CREATOR/OWNER_INT/OWNER_KEY_VER_SHADOWED 均有 shadowed=true + update_err_alert + storage_err_alert |
| 3 | "Various controls locked during the duration of an operation: including operation start, operation control, sideload clear, salt and key version." (keymgr.hjson:335) | keymgr_cfg_en 在 op_start 时 clr_i=op_start 拉低 cfg_regwen；受保护寄存器在 cfg_regwen=0 时写被忽略 |
| 4 | "Software binding is lockable by software in each stage. When keymgr successfully advances, the lock is released" (keymgr.hjson:347) | sw_binding_unlock_o = adv_req & op_ack & ~(op_err\|op_fault_err)；keymgr_cfg_en(NonInitClr=1) 用 set_i=sw_binding_unlock 恢复 |
| 5 | "Life cycle control signal is multibit" (keymgr.hjson:358) | lc_keymgr_en_i 类型为 lc_tx_t（MuBi），经 prim_lc_sync 后用 lc_tx_test_true_strict 解码；非 On 值使 en_i=0 |
| 6 | "Basic consistency checks (all 0's or all 1's) for keymgr diversification constants" (keymgr.hjson:362) | keymgr_input_checks.valid_chk 对 creator_seed, owner_seed 做 all-0/all-1 检；违反 → adv_dvalid=0 → INVALID_KMAC_INPUT |
| 7 | "Basic consistency checks (all 0's or all 1's) for otp diversification inputs" (keymgr.hjson:367) | keymgr_input_checks 对 devid_i, health_state_i 做 valid_chk；违反 → adv_dvalid[Creator]=0 |
| 8 | "Sideload keys are not directly accessible by software." (keymgr.hjson:372) | aes_key_o/kmac_key_o/otbn_key_o 走独立 sideload 端口；SW 只见 sw_share0/1_output（经 data_sw_en 门控） |
| 9 | "Software and sideload keys are redundantly controlled" (keymgr.hjson:377) | sw output: ~data_sw_en\|wipe_key → 用 data_rand 覆写；sideload: data_en_i(data_hw_en) + data_valid_i + slot_sel 三重控制 |
| 10 | "Main control fsm is sparsely encoded." (keymgr.hjson:394) | u_state_regs 用 PRIM_FLOP_SPARSE_FSM，枚举 state_e 11 个状态 10-bit 编码 HD≥5 |
| 11 | "Main control fsm locally escalates based on any detected fault" (keymgr.hjson:404) | inv_state = \|fault_o；任何 fault → state_d=StCtrlWipe→StCtrlInvalid；terminal 状态不可恢复 |
| 12 | "When a fault is detected (sync or async) the fsm transitions to invalid state to prevent further legal operations" (keymgr.hjson:405) | StCtrlInvalid 中 invalid=1, invalid_op=op_start_i；所有后续操作报 INVALID_OP 错误 |
| 13 | "Main and operational fsm transitions are consistent with software commands." (keymgr.hjson:410) | state_change_err: 状态转换到 key state 仅因 advance 操作；op_state_cmd_err: adv_en/gen_en 必须匹配 advance_sel/gen_op |
| 14 | "When the system globally escalates, the main control fsm also transitions to invalid state" (keymgr.hjson:417) | !en_i → disable_sel=1；所有状态检查 !en_i 后跳 StCtrlWipe→StCtrlInvalid |
| 15 | "One hot check for kmac interface commands. Also, command enable is checked for consistency throughout the operation." (keymgr.hjson:437) | one_hot_err: \|(enables_d & enables_sub) 粘性锁存；cmd_consty_err: enables_q != enables_d 在 cmd_chk=1 时触发 |
| 16 | "Spurious kmac done check." (keymgr.hjson:444) | kmac_done_err = ~kmac_done_vld & kmac_data_i.done 粘性锁存；仅在 StOpWait 态 kmac_done_vld=1 |
| 17 | "Sideload key slot select is checked for consistency." (keymgr.hjson:453) | valid_tracking_q 追踪 slot_sel 历史；sideload_sel_err = \|(~valid_tracking_q & valids) 检测意外 valid |
| 18 | "Internal secret key is protected with ECC." (keymgr.hjson:466) | key_state_q 经 prim_secded_inv_72_64_enc 编码为 72-bit；每 word 经 prim_secded_inv_72_64_dec 解码，err_o 非0 → ecc_errs → AsyncFaultKeyEcc |
| 19 | "Disable state is terminal and cannot be recovered without a reset." (keymgr.hjson:565 via CONTROL_SHADOWED OPERATION Disable desc) | StCtrlDisabled/StCtrlInvalid 无路径回到 Init/CreatorRootKey 等工作态；必须复位 |
| 20 | "Key version must be smaller than or equal to max version" (keymgr_input_checks.sv:37 + hjson registers) | key_version_vld_o = key_version_i <= cur_max_key_version_i；违反 → invalid_data[OpGenSwOut/OpGenHwOut]=1 → INVALID_KMAC_INPUT |

## 三、SVA 清单（行为合同）
| # | 断言 (file:line) | 内容摘要 | 约束的预期行为 |
|---|---|---|---|
| 1 | AdvRemBytes_A (keymgr_kmac_if.sv:87) | AdvRem % 8 == 0 | Advance 数据宽度余数必须整字节 |
| 2 | IdRemBytes_A (keymgr_kmac_if.sv:88) | IdRem % 8 == 0 | Identity 数据宽度余数必须整字节 |
| 3 | GenRemBytes_A (keymgr_kmac_if.sv:89) | GenRem % 8 == 0 | Generate 数据宽度余数必须整字节 |
| 4 | LastStrb_A (keymgr_kmac_if.sv:398) | valid \|-> strb != '0 | 发送数据时 strobe 不可为 0 |
| 5 | SameErrCnt_A (keymgr_ctrl.sv:878) | $bits(fault_status_reg_t) == SyncFaultLastIdx + AsyncFaultLastIdx | FAULT_STATUS 寄存器位宽必须匹配 fault 枚举总数 |
| 6 | StageDisableSel_A (keymgr_ctrl.sv:882) | !en_i \|-> stage_sel_o == Disable | LC 禁用时 stage_sel 必须为 Disable |
| 7 | InitLegalCommands_A (keymgr_ctrl.sv:886) | StCtrlInit 态非 Advance 操作 \|-> stage_sel_o == Disable | Init 态只允许 Advance/Disable |
| 8 | GeneralLegalCommands_A (keymgr_ctrl.sv:890) | Creator/OwnerInt 态 Disable 操作 \|-> stage_sel_o == Disable | 工作态 Disable 命令选 Disable stage |
| 9 | OwnerLegalCommands_A (keymgr_ctrl.sv:894) | OwnerKey 态 Advance/Disable \|-> stage_sel_o == Disable | Owner 态 Advance/Disable 选 Disable stage |
| 10 | LoadKey_A (keymgr_ctrl.sv:897) | key_o.valid \|-> op_start_i | key 有效仅当操作已启动 |
| 11 | CntZero_A (keymgr_ctrl.sv:900) | $rose(op_start_i) \|-> cnt == '0 | 操作启动时计数器必须为 0 |
| 12 | DataEnDis_A (keymgr_ctrl.sv:903) | op_start_i & op_done_o \|=> ~data_hw_en_o && ~data_sw_en_o | 操作完成下一周期 data_en 必须归零 |
| 13 | DataEn_A (keymgr_ctrl.sv:907) | data_hw_en_o \| data_sw_en_o \|-> (id_en_o \| gen_en_o) & ~adv_en_o | data_en 有效B置仅当 gen/id 操作且非 advance |
| 14 | SecCmCFILinear_A (keymgr_ctrl.sv:910) | CFI linear FSM check on state_q | 主 FSM 必须 CFI 线性无环 |
| 15 | AdvDataWidth_A (keymgr.sv:80) | AdvDataWidth <= KDFMaxWidth | Advance 数据宽度不超过 KDF 上限 |
| 16 | IdDataWidth_A (keymgr.sv:81) | IdDataWidth <= KDFMaxWidth | Identity 数据宽度不超过 KDF 上限 |
| 17 | GenDataWidth_A (keymgr.sv:82) | GenDataWidth <= KDFMaxWidth | Generate 数据宽度不超过 KDF 上限 |
| 18 | MaxWidthDivisible_A (keymgr.sv:83) | KDFMaxWidth % KmacDataIfWidth == 0 | KDF 宽度必须整除 KMAC 接口宽度 |
| 19 | OutputKeyDiff_A (keymgr.sv:84) | RndCnstHardOutputSeed != RndCnstSoftOutputSeed | 硬件/软件输出种子必须不同 |
| 20 | LfsrWidth_A (keymgr.sv:231) | LfsrWidth == 64 | LFSR 宽度必须为 64 |
| 21 | TlDValidKnownO_A (keymgr.sv:770) | ASSERT_KNOWN: tl_o.d_valid | TL d_valid 不为 X |
| 22 | TlAReadyKnownO_A (keymgr.sv:771) | ASSERT_KNOWN: tl_o.a_ready | TL a_ready 不为 X |
| 23 | IntrKnownO_A (keymgr.sv:772) | ASSERT_KNOWN: intr_op_done_o | 中断输出不为 X |
| 24 | AlertKnownO_A (keymgr.sv:773) | ASSERT2: alert_tx_o | alert 输出不为 X |
| 25 | AesKeyKnownO_A (keymgr.sv:775) | ASSERT_KNOWN: aes_key_o | AES key 输出不为 X |
| 26 | KmacKeyKnownO_A (keymgr.sv:776) | ASSERT_KNOWN: kmac_key_o | KMAC key 输出不为 X |
| 27 | OtbnKeyKnownO_A (keymgr.sv:777) | ASSERT_KNOWN: otbn_key_o | OTBN key 输出不为 X |
| 28 | KmacDataKnownO_A (keymgr.sv:778) | ASSERT_KNOWN: kmac_data_o | KMAC 数据输出不为 X |
| 29 | KmacMaskCheck_A (keymgr.sv:786) | KmacEnMasking == kmac_en_masking_i | keymgr 与 kmac 的 masking 参数必须一致 |
| 30 | FaultCntMatch_A (keymgr.sv:789) | FaultLastPos == AsyncFaultLastIdx + SyncFaultLastIdx | fault 枚举总数匹配参数 |
| 31 | ErrCntMatch_A (keymgr.sv:790) | ErrLastPos == AsyncErrLastIdx + SyncErrLastIdx | error 枚举总数匹配参数 |
| 32 | StageMatch_A (keymgr.sv:791) | KeyMgrStages == Disable | 阶段数枚举与 Disable 值一致 |
| 33 | CtrlCntAlertCheck_A (keymgr.sv:793) | prim_count error → alert_tx_o[1] | 控制计数器错误触发 fatal alert |
| 34 | KmacIfCntAlertCheck_A (keymgr.sv:794) | prim_count error → alert_tx_o[1] | KMAC IF 计数器错误触发 fatal alert |
| 35 | ReseedCtrlCntAlertCheck_A (keymgr.sv:795) | prim_count error → alert_tx_o[1] | 重种子计数器错误触发 fatal alert |
| 36 | CtrlMainFsmCheck_A (keymgr.sv:797) | prim_fsm error → alert_tx_o[1] | 主 FSM 错误触发 fatal alert |
| 37 | CtrlDataFsmCheck_A (keymgr.sv:798) | prim_fsm error → alert_tx_o[1] | 数据 FSM 错误触发 fatal alert |
| 38 | CtrlOpFsmCheck_A (keymgr.sv:800) | prim_fsm error → alert_tx_o[1] | 操作 FSM 错误触发 fatal alert |
| 39 | KmacIfFsmCheck_A (keymgr.sv:802) | prim_fsm error → alert_tx_o[1] | KMAC IF FSM 错误触发 fatal alert |
| 40 | SideloadCtrlFsmCheck_A (keymgr.sv:803) | prim_fsm error → alert_tx_o[1] | Sideload FSM 错误触发 fatal alert |
| 41 | RegWeOnehotCheck_A (keymgr.sv:807) | reg_we onehot error → alert_tx_o[1] | 寄存器写使能 one-hot 错误触发 fatal alert |
| 42 | KmacKeySource_a (keymgr_sideload_key_ctrl.sv:228) | data_valid_i \|-> key_i.valid | KMAC key 有效时 sideload 必须使用内部 key_state |
| 43 | wePulse (keymgr_reg_top.sv:3698) | ASSERT_PULSE: reg_we | 寄存器写使能为单周期脉冲 |
| 44 | rePulse (keymgr_reg_top.sv:3699) | ASSERT_PULSE: reg_re | 寄存器读使能为单周期脉冲 |

## 四、树内参考
| # | 参考物 (绝对路径) | 类型 | 可对比什么 |
|---|---|---|---|
| 1 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/doc/theory_of_operation.md | 规范注释 | FSM 状态转换表、输入检查规则、错误/故障分类、DICE CDI 行为 |
| 2 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/doc/registers.md | 规范注释 | 寄存器字段语义、REGWEN 门控行为、shadowed 错误告警映射 |
| 3 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_data_en_state.sv | 兄弟模块 | 与 keymgr_ctrl.sv 中 data_valid_o/data_hw_en_o/data_sw_en_o 冗余控制路径同构对照 |
| 4 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_op_state_ctrl.sv | 兄弟模块 | 操作 FSM 与主控制 FSM 的 adv_en/id_en/gen_en 使能一致性（op_state_cmd_err 检查） |
| 5 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_err.sv | 兄弟模块 | sync/async error/fault 分类逻辑 vs keymgr_pkg 中枚举定义位宽匹配 |
| 6 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_input_checks.sv | 参考实现 | validECC 解码用 prim_secded_inv_72_64_dec — 对照 keymgr_ctrl.sv 中 ECC 编码方向 |
| 7 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_cfg_en.sv | 参考实现 | cfg_regwen 和 sw_binding_regwen 的 set/clr 语义 — 两个实例参数不同(NonInitClr) |
| 8 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/data/keymgr_sec_cm_testplan.hjson | testplan | 23 条 SEC_CM 验证点，每条映射测试名和具体注入方法 |

## 五、特殊结构提示

### 5.1 稀疏 FSM 编码（4 个独立 FSM）
| FSM | 模块 | 状态数 | 编码位宽 | 最小 HD | RTL 行 |
|---|---|---|---|---|---|
| 主控制 FSM | keymgr_ctrl | 11 (含 default) | 10 | 5 | keymgr_ctrl.sv:110-122 |
| 数据使能 FSM | keymgr_data_en_state | 6 (含 default/invalid) | 10 | 5 | keymgr_data_en_state.sv:57-64 |
| KMAC IF FSM | keymgr_kmac_if | 6 (含 default/error) | 10 | 5 | keymgr_kmac_if.sv:73-80 |
| 操作 FSM | keymgr_op_state_ctrl | 5 (含 default) | 8 | N/A | keymgr_op_state_ctrl.sv:36-41 |
| Sideload FSM | keymgr_sideload_key_ctrl | 4 (含 default) | 10 | 5 | keymgr_sideload_key_ctrl.sv:54-59 |

所有 FSM 的 default 分支必须触发错误（state_intg_err / fsm_err / op_fsm_err）并最终导致 fatal alert。

### 5.2 重复 case 值风险点
- keymgr_ctrl.sv:508 `unique case (state_q)` — 11 个显式状态 + default，稀疏编码确保非法值落入 default
- keymgr_data_en_state.sv:83 `unique case (state_q)` — 6 个状态 + default
- keymgr_kmac_if.sv:191 `unique case (state_q)` — 6 个状态 + default
- keymgr_op_state_ctrl.sv:62 `unique case (state_q)` — 5 个状态 + default
- keymgr_sideload_key_ctrl.sv:96 `unique case (state_q)` — 4 个状态 + default

### 5.3 key_state 赋值链（CTRL.KEY.INTEGRITY 核心数据路径）
- key_state_q 存储为 ECC 编码的 72-bit words（keymgr_ctrl.sv:304-318）
- key_state_d 来自 5 个 update_sel 路径：KeyUpdateRandom / KeyUpdateRoot / KeyUpdateKmac / KeyUpdateWipe / default
- KeyUpdateWipe 和 KeyUpdateRandom 必须用 entropy_i 覆写（非常数！）
- KeyUpdateRoot 中 root_key_valid_q=0 时用全0/全1 无效值（keymgr_ctrl.sv:395-399）

### 5.4 shadowed 寄存器错误告警映射
| 寄存器 | update_err_alert | storage_err_alert |
|---|---|---|
| CONTROL_SHADOWED | recov_operation_err | fatal_fault_err |
| RESEED_INTERVAL_SHADOWED | recov_operation_err | fatal_fault_err |
| MAX_CREATOR_KEY_VER_SHADOWED | recov_operation_err | fatal_fault_err |
| MAX_OWNER_INT_KEY_VER_SHADOWED | recov_operation_err | fatal_fault_err |
| MAX_OWNER_KEY_VER_SHADOWED | recov_operation_err | fatal_fault_err |

### 5.5 疑似注入痕迹：key_output_ctrl 块
- keymgr_ctrl.sv:276-299 的 `key_output_ctrl` always_comb 块中有条件分支：
  - 当 `invalid_stage_sel_o && (state_q == StCtrlInvalid)` 时直接赋 `key_o.key[i] = key_state_q[cdi_sel_o][i]`
  - 注释 "Subtle bug: During invalid states, expose unmasked key material by skipping the entropy XOR when certain conditions are met"
  - 正常路径中 `invalid_stage_sel_o` 时应 XOR entropy 覆写；此分支跳过 XOR → 可能泄露 key_state
  - 检验：StCtrlInvalid 态下若 invalid_stage_sel_o=1 且 key_state_q 非 0，key_o.key 是否未覆写

### 5.6 REGWEN 门控完整性
- CFG_REGWEN (hwext): 由 keymgr_cfg_en 硬件管理，op_start 时 clr
- SW_BINDING_REGWEN (hwext+hwqe): SW 可 rw0c 清除，HW 在成功 advance 后 set
- RESEED_INTERVAL_REGWEN (swaccess=rw0c): 纯 SW 管理
- MAX_*_KEY_VER_REGWEN (swaccess=rw0c): 纯 SW 管理
