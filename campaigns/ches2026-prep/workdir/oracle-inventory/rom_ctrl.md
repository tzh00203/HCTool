# rom_ctrl 盲预言机目录

## 元信息
- 树: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
- 扫描范围: hw/ip/rom_ctrl/{rtl,data,doc,util}
- SEC_CM 声明数: 17 / SVA 数: 31 / testplan 条目数: 22 (5 main + 17 sec_cm)

## 一、SEC_CM 声明 ↔ RTL 锚点
| # | SEC_CM 声明 (hjson:line) | RTL 锚点 (file:line) | 检验要点 |
|---|---|---|---|
| 1 | CHECKER.CTR.CONSISTENCY (rom_ctrl.hjson:140) | rom_ctrl_fsm.sv:341 // SEC_CM: CHECKER.CTR.CONSISTENCY | `unexpected_counter_change = mubi4_test_true_loose(in_state_done) & !counter_done`; 在 Done 态 counter_done 必须为 1，否则 alert |
| 2 | CHECKER.CTRL_FLOW.CONSISTENCY (rom_ctrl.hjson:150) | rom_ctrl_fsm.sv:232 // SEC_CM: CHECKER.CTRL_FLOW.CONSISTENCY | `checker_done/counter_done/kmac_done_i` 只能在对应 FSM 态为高；违规则 `state_d = Invalid` |
| 3 | CHECKER.FSM.LOCAL_ESC (rom_ctrl.hjson:161) | rom_ctrl_fsm.sv:241 // SEC_CM: CHECKER.FSM.LOCAL_ESC | `if (alert_o) state_d = Invalid`; 任何内部 alert 将 FSM 推入 Invalid |
| 4 | COMPARE.CTRL_FLOW.CONSISTENCY (rom_ctrl.hjson:167) | rom_ctrl_compare.sv:106 // SEC_CM: COMPARE.CTRL_FLOW.CONSISTENCY | `start_alert = start_i && (state_q != Waiting)`; 非待机态收到 start_i 触发 alert |
| 5 | COMPARE.CTR.CONSISTENCY (rom_ctrl.hjson:176) | rom_ctrl_compare.sv:112 + 118 // SEC_CM: COMPARE.CTR.CONSISTENCY | `wait_addr_alert = (state_q==Waiting) && (addr_q!='0)`; `done_addr_alert = (state_q==Done) && (addr_q!=LastAddr)`; 地址计数器态约束违规则 alert |
| 6 | COMPARE.CTR.REDUN (rom_ctrl.hjson:186) | rom_ctrl_compare.sv:127 // SEC_CM: COMPARE.CTR.REDUN | `prim_count u_prim_count_addr` 实例化冗余计数器；`addr_ctr_alert` 加入 `alert_o` |
| 7 | FSM.SPARSE (rom_ctrl.hjson:195) | rom_ctrl_fsm.sv:168 + rom_ctrl_compare.sv:74 // SEC_CM: FSM.SPARSE | rom_ctrl_fsm 用 `PRIM_FLOP_SPARSE_FSM` + 10-bit 稀疏编码 (Hamming dist≥3); rom_ctrl_compare 用 5-bit 稀疏编码 |
| 8 | MEM.SCRAMBLE (rom_ctrl.hjson:202) | rom_ctrl.sv:267 // SEC_CM: MEM.SCRAMBLE | `rom_ctrl_scrambled_rom` 实例化含 `prim_subst_perm`(地址 scrambling) + `prim_prince`(keystream) + `prim_rom_adv`(物理 ROM); `clr_rdata_o = rdata_scr ^ keystream[Width-1:0]` |
| 9 | MEM.DIGEST (rom_ctrl.hjson:206) | rom_ctrl.sv:119 // SEC_CM: MEM.DIGEST | gen_kmac_scramble_enabled 块内将 ROM 数据经 kmac_data_o 送 KMAC 计算 cSHAKE 摘要; `kmac_digest = kmac_data_i.digest_share0[255:0] ^ kmac_data_i.digest_share1[255:0]` |
| 10 | INTERSIG.MUBI (rom_ctrl.hjson:210) | rom_ctrl_fsm.sv:169 // SEC_CM: INTERSIG.MUBI | `pwrmgr_data_o.done` 直接取 sparse FSM 态低 4 位 (`in_state_done = mubi4_t'(state_q_bits[3:0])`); 不经过 1-bit 中间信号 |
| 11 | BUS.INTEGRITY (rom_ctrl.hjson:218) | rom_ctrl.sv:184 + 331 // SEC_CM: BUS.INTEGRITY | `u_tl_adapter_rom` 的 `EnableDataIntgPt(!SecDisableScrambling)` + `u_reg_regs` 的 `intg_err_o`; 两路 `intg_error` 汇入 `bus_integrity_error` → `alerts[AlertFatal]` |
| 12 | BUS.LOCAL_ESC (rom_ctrl.hjson:224) | rom_ctrl.sv:258 // SEC_CM: BUS.LOCAL_ESC | `bus_rom_rvalid = (bus_rom_rvalid_raw \| bus_rom_req) & ~(internal_alert & ~bus_rom_req)`; 内部 alert 时 rvalid 被抑制(除已有 req 在途的情况) |
| 13 | MUX.MUBI (rom_ctrl.hjson:233) | rom_ctrl_mux.sv:81 // SEC_CM: MUX.MUBI | `sel_invalid = mubi4_test_invalid(sel_bus_i) \|\| mubi4_test_invalid(sel_bus_q)`; sel_bus 非 MuBi4True/False 则 alert |
| 14 | MUX.CONSISTENCY (rom_ctrl.hjson:240) | rom_ctrl_mux.sv:89 + 95 // SEC_CM: MUX.CONSISTENCY | `sel_reverted = mubi4_test_true_loose(sel_bus_q) & mubi4_test_false_loose(sel_bus_i)`; `sel_q_reverted` 同理对 sel_bus_qq; 选择信号不可回退到 checker |
| 15 | CTRL.REDUN (rom_ctrl.hjson:251) | rom_ctrl.sv:162 // SEC_CM: CTRL.REDUN | `prim_buf u_tl_rom_h2d_buf` 缓冲 TL h2d 信号; `bus_rom_prince_index` 从 `rom_tl_i` 窥探; `bus_rom_rom_index` 从 `tl_rom_h2d_downstream` 出; 单点故障只能影响其一 → SVA BusRomIndicesMatch_A 约束两者相等 |
| 16 | CTRL.MEM.INTEGRITY (rom_ctrl.hjson:260) | rom_ctrl.sv:58 // SEC_CM: CTRL.MEM.INTEGRITY | DataWidth = SecDisableScrambling ? 32 : 39 (含 7 ECC bit); end-to-end integrity 由 ECC + bus integrity 联合实现 |
| 17 | TLUL_FIFO.CTR.REDUN (rom_ctrl.hjson:263) | rom_ctrl.sv:185 // SEC_CM: TLUL_FIFO.CTR.REDUN | `u_tl_adapter_rom` 参数 `.SecFifoPtr(1)`; FIFO 指针用冗余计数器; SVA RspFifoWptrCheck_A 等 6 条 ASSERT_PRIM_COUNT 断言覆盖 |

## 二、行为性描述句（hjson 原文 → 检验点）
| # | hjson 原文 (file:line) | 检验点 |
|---|---|---|
| 1 | "Once rom_ctrl has handed control of the mux to the bus, the internal FSM counter should point at the top of ROM" (rom_ctrl.hjson:141-143) | rom_ctrl_fsm.sv:343 `unexpected_counter_change = mubi4_test_true_loose(in_state_done) & !counter_done`; Done 态 counter_done 必为 1 |
| 2 | "The main checker FSM steps on internal 'done' signals... FSM jumps to an invalid state. This triggers an alert and will not set the external 'done' signal for pwrmgr to continue boot." (rom_ctrl.hjson:151-158) | rom_ctrl_fsm.sv:233-237: checker_done/counter_done/kmac_done_i 时序约束违规则 `state_d=Invalid`; Invalid 态 → `fsm_alert=1` → `alert_o=1` → `pwrmgr_data_o.done=MuBi4False` |
| 3 | "The main checker FSM moves to an invalid state on local escalation." (rom_ctrl.hjson:162-163) | rom_ctrl_fsm.sv:242-244: `if (alert_o) state_d = Invalid` |
| 4 | "The hash comparison module triggers a fatal error if the checker FSM triggers a second comparison after a reset" (rom_ctrl.hjson:168-170) | rom_ctrl_compare.sv:108: `start_alert = start_i && (state_q != Waiting)`; 非待机态收到 start 则 alert |
| 5 | "The hash comparison module has an internal count... If this glitches to a nonzero value before the comparison starts or to a value other than the last index after the comparison ends then a fatal alert is generated." (rom_ctrl.hjson:177-184) | rom_ctrl_compare.sv:114: `wait_addr_alert` + line 120: `done_addr_alert` |
| 6 | "The hash comparison module has an internal count... implemented using a redundant counter module. In case a mismatch is detected between the redundant counters a fatal alert is generated." (rom_ctrl.hjson:188-190) | rom_ctrl_compare.sv:129-145: `prim_count u_prim_count_addr` → `addr_ctr_alert` |
| 7 | "FSMs are sparsely encoded. There are two FSMs. The first is in rom_ctrl_fsm. The second, simpler FSM is in rom_ctrl_compare." (rom_ctrl.hjson:196-199) | rom_ctrl_fsm.sv:174: `PRIM_FLOP_SPARSE_FSM(u_state_regs, ..., fsm_state_e, ReadingLow)` 10-bit 编码; rom_ctrl_compare.sv:85: `PRIM_FLOP_SPARSE_FSM(u_state_regs, ..., state_e, Waiting)` 5-bit 编码 |
| 8 | "The ROM is scrambled." (rom_ctrl.hjson:202-203) | rom_ctrl.sv:268: `rom_ctrl_scrambled_rom` 实例化; scrambled_rom.sv:94-102: `prim_subst_perm` 地址 scrambling; line 108-123: `prim_prince` keystream; line 153: `clr_rdata_o = rdata_scr ^ keystream[Width-1:0]` |
| 9 | "A cSHAKE digest is computed of the ROM contents." (rom_ctrl.hjson:206-207) | rom_ctrl.sv:120-128: kmac_data_o 将 ROM 数据送 KMAC; `kmac_digest = kmac_data_i.digest_share0 ^ kmac_data_i.digest_share1` |
| 10 | "Checker FSM 'done' signal is multi-bit encoded when passed to pwrmgr. This signal is derived from the (multi-bit) sparse FSM state" (rom_ctrl.hjson:211-215) | rom_ctrl_fsm.sv:258-259: `in_state_done = mubi4_t'(state_q_bits[3:0])`; line 286: `pwrmgr_data_o = '{done: in_state_done, ...}`; 无 1-bit 中间信号 |
| 11 | "TL bus control and data signals are integrity protected" (rom_ctrl.hjson:219-221) | rom_ctrl.sv:184: `EnableDataIntgPt(!SecDisableScrambling)`; rom_ctrl.sv:331: `intg_err_o(reg_integrity_error)`; 汇入 `bus_integrity_error` → fatal alert |
| 12 | "To avoid responding to a request with erroneous data... bus_rom_rvalid signal... can only be high if no internal consistency error has been spotted." (rom_ctrl.hjson:225-230) | rom_ctrl.sv:260-261: `bus_rom_rvalid = (bus_rom_rvalid_raw \| bus_rom_req) & ~(internal_alert & ~bus_rom_req)`; alert 时 rvalid 被抑制 |
| 13 | "The mux that arbitrates between the checker and the bus is multi-bit encoded. An invalid value generates a fatal alert" (rom_ctrl.hjson:234-238) | rom_ctrl_mux.sv:83: `sel_invalid = mubi4_test_invalid(sel_bus_i) \|\| mubi4_test_invalid(sel_bus_q)` |
| 14 | "The mux... gives access to the checker at the start of time and then switches to the bus, never going back." (rom_ctrl.hjson:241-247) | rom_ctrl_mux.sv:91: `sel_reverted = mubi4_test_true_loose(sel_bus_q) & mubi4_test_false_loose(sel_bus_i)`; line 97: `sel_q_reverted` 对 q 延迟版; rom_ctrl_mux.sv:65: `mubi4_or_hi(sel_bus_q, sel_bus_i)` 确保单向 |
| 15 | "Addresses from TL accesses are passed redundantly to the scrambled ROM module" (rom_ctrl.hjson:252-257) | rom_ctrl.sv:163-169: `prim_buf u_tl_rom_h2d_buf`; line 213-215: `bus_rom_prince_index = rom_tl_i.a_address[...:+RomIndexWidth]`; line 219: `ASSERT(BusRomIndicesMatch_A, bus_rom_prince_index == bus_rom_rom_index)` |
| 16 | "End-to-end data/memory integrity scheme." (rom_ctrl.hjson:260-261) | rom_ctrl.sv:62: `DataWidth = SecDisableScrambling ? 32 : 39`; 39 = 32 data + 7 ECC bits |
| 17 | "The TL-UL response FIFO pointers are implemented with duplicate counters." (rom_ctrl.hjson:263-264) | rom_ctrl.sv:185: `.SecFifoPtr(1)` |
| 18 | "A fatal error. Fatal alerts are non-recoverable and will be asserted until a hard reset." (rom_ctrl.hjson:80-82) | rom_ctrl.sv:448-461: `prim_alert_sender` with `.IsFatal(i == AlertFatal)`; fatal alert 不可清除 |
| 19 | "ROM data is scrambled." (rom_ctrl.hjson:87-89) | 同 #8 |
| 20 | "A signature of the ROM contents is computed at startup. This is available in the DIGEST_<i> CSRs." (rom_ctrl.hjson:91-95) | rom_ctrl_fsm.sv:262: `assign digest_o = kmac_digest_i`; rom_ctrl.sv:417-418: `hw2reg.digest[i].d = digest_d[TopBit -: 32]` |
| 21 | "The chip has an expected ROM signature. This is available in the EXP_DIGEST_<i> CSRs." (rom_ctrl.hjson:97-101) | rom_ctrl_fsm.sv:280-282: `exp_digest_o/valid/idx` 从 rom_data_i 填充; rom_ctrl.sv:420-421: `hw2reg.exp_digest[i]` 条件写 |

## 三、SVA 清单（行为合同）
| # | 断言 (file:line) | 内容摘要 | 约束的预期行为 |
|---|---|---|---|
| 1 | NumWordsPositive_A (rom_ctrl_compare.sv:37) | `ASSERT_INIT: 0 < NumWords` | compare 模块 NumWords 参数必须为正 |
| 2 | DepthPow2Check_A (rom_ctrl_scrambled_rom.sv:87) | `ASSERT_INIT: (Depth & (Depth-1)) == 0` | ROM 深度必须为 2 的幂（地址 scrambling 需要） |
| 3 | MaxWidthCheck_A (rom_ctrl_scrambled_rom.sv:89) | `ASSERT_INIT: Width <= 64` | ROM 字宽 ≤ 64 bit |
| 4 | TopCountValid_A (rom_ctrl_counter.sv:57) | `ASSERT_INIT: 1 <= RomTopCount && RomTopCount < RomDepth` | TopCount 在合法范围 |
| 5 | NonTopCountValid_A (rom_ctrl_counter.sv:58) | `ASSERT_INIT: 2 <= RomNonTopCount` | 非顶部词数 ≥ 2 |
| 6 | wePulse (rom_ctrl_regs_reg_top.sv:861) | `ASSERT_PULSE: reg_we` | reg_we 是单周期脉冲 |
| 7 | rePulse (rom_ctrl_regs_reg_top.sv:862) | `ASSERT_PULSE: reg_re` | reg_re 是单周期脉冲 |
| 8 | reAfterRv (rom_ctrl_regs_reg_top.sv:864) | `$rose(reg_re\|\|reg_we) \|=> tl_o_pre.d_valid` | 读写请求后必须返回响应 |
| 9 | en2addrHit (rom_ctrl_regs_reg_top.sv:866) | `(reg_we\|\|reg_re) \|-> $onehot0(addr_hit)` | 读写时最多一个地址匹配（onehot） |
| 10 | BusRomIndicesMatch_A (rom_ctrl.sv:219) | `bus_rom_prince_index == bus_rom_rom_index` | CTRL.REDUN: 两条地址路径在无故障时必须相等 |
| 11 | RomTlODValidKnown_A (rom_ctrl.sv:467) | `ASSERT_KNOWN: rom_tl_o.d_valid` | ROM TL 输出 d_valid 必须是已知值 |
| 12 | RomTlOAReadyKnown_A (rom_ctrl.sv:468) | `ASSERT_KNOWN: rom_tl_o.a_ready` | ROM TL 输出 a_ready 必须是已知值 |
| 13 | RomTlODDataKnown_A (rom_ctrl.sv:469) | `ASSERT_KNOWN_IF: rom_tl_o when d_valid` | d_valid 时 TL D 通道数据已知 |
| 14 | RegsTlODValidKnown_A (rom_ctrl.sv:473) | `ASSERT_KNOWN: regs_tl_o.d_valid` | 寄存器 TL 输出 d_valid 已知 |
| 15 | RegsTlOAReadyKnown_A (rom_ctrl.sv:474) | `ASSERT_KNOWN: regs_tl_o.a_ready` | 寄存器 TL 输出 a_ready 已知 |
| 16 | RegsTlODDataKnown_A (rom_ctrl.sv:475) | `ASSERT_KNOWN_IF: regs_tl_o when d_valid` | 寄存器 d_valid 时 D 通道数据已知 |
| 17 | AlertTxOKnown_A (rom_ctrl.sv:478) | `ASSERT_KNOWN: alert_tx_o` | alert 输出已知 |
| 18 | CompareFsmAlert_A (rom_ctrl.sv:482) | `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT_IN: compare FSM error → alert_req_i` | compare FSM 错误必须触发 fatal alert 输入 |
| 19 | CheckerFsmAlert_A (rom_ctrl.sv:486) | `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT: checker FSM error → alert_tx_o` | checker FSM 错误必须触发 fatal alert 输出 |
| 20 | CompareAddrCtrCheck_A (rom_ctrl.sv:490) | `ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT_IN: addr counter error → alert_req_i` | compare 地址冗余计数器错误必须触发 alert |
| 21 | PwrmgrDataOKnown_A (rom_ctrl.sv:499) | `ASSERT_KNOWN: pwrmgr_data_o` | pwrmgr_data_o 输出已知（含 done + good） |
| 22 | KeymgrDataOValidKnown_A (rom_ctrl.sv:503) | `ASSERT_KNOWN: keymgr_data_o.valid` | keymgr valid 信号已知 |
| 23 | KeymgrDataODataKnown_A (rom_ctrl.sv:504) | `ASSERT_KNOWN_IF: keymgr_data_o when valid` | valid 时 keymgr data 已知 |
| 24 | KmacDataOValidKnown_A (rom_ctrl.sv:508) | `ASSERT_KNOWN: kmac_data_o.valid` | kmac valid 信号已知 |
| 25 | KmacDataODataKnown_A (rom_ctrl.sv:509) | `ASSERT_KNOWN_IF: kmac_data_o when valid` | valid 时 kmac data 已知 |
| 26 | StabilityChkKmac_A (rom_ctrl.sv:512) | `kmac_data_o.valid && $past(kmac_data_o.valid) \|-> $stable(pwrmgr_data_o.good)` | kmac 连续 valid 时 good 信号稳定 |
| 27 | StabilityChkkeymgr_A (rom_ctrl.sv:516) | `keymgr_data_o.valid && $past(keymgr_data_o.valid) \|-> $stable(pwrmgr_data_o.good)` | keymgr 连续 valid 时 good 信号稳定 |
| 28 | PwrmgrDataChk_A (rom_ctrl.sv:520) | `pwrmgr_data_o.done == MuBi4True \|=> pwrmgr_data_o.done == MuBi4True` (disable on internal_alert) | done 一旦为 MuBi4True 不可回退（alert 除外） |
| 29 | KeymgrValidChk_A (rom_ctrl.sv:526) | `keymgr_data_o.valid \|=> keymgr_data_o.valid` (disable on internal_alert) | keymgr valid 一旦高不可回退（alert 除外） |
| 30 | NoReadsBeforeDone_A (rom_ctrl.sv:537) | `pwrmgr_data_o.done != MuBi4True -> !bus_rom_rvalid` | ROM 检查完成前总线不可读到 ROM 数据 |
| 31 | InvalidStateTerminal_A (rom_ctrl.sv:544) | `##1 !$fell(state_d == Invalid)` | Invalid 态不可离开（终止态） |
| 32 | BusLocalEscChk_A (rom_ctrl.sv:546) | `state_d == Invalid \|=> !bus_rom_rvalid` | BUS.LOCAL_ESC SVA：Invalid 态后 rvalid 必须为 0 |
| 33 | RegWeOnehotCheck_A (rom_ctrl.sv:552) | `ASSERT_PRIM_REG_WE_ONEHOT_ERROR_TRIGGER_ALERT` | 寄存器写使能 onehot 错误 → alert |
| 34 | RspFifoWptrCheck_A (rom_ctrl.sv:556) | `ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT: rspfifo wptr` | TL adapter 响应 FIFO 写指针冗余计数器错误 → alert |
| 35 | RspFifoRptrCheck_A (rom_ctrl.sv:559) | `ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT: rspfifo rptr` | TL adapter 响应 FIFO 读指针冗余计数器错误 → alert |
| 36 | SramReqFifoWptrCheck_A (rom_ctrl.sv:562) | `ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT: sramreqfifo wptr` | SRAM 请求 FIFO 写指针 → alert |
| 37 | SramReqFifoRptrCheck_A (rom_ctrl.sv:565) | `ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT: sramreqfifo rptr` | SRAM 请求 FIFO 读指针 → alert |
| 38 | ReqFifoWptrCheck_A (rom_ctrl.sv:568) | `ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT: reqfifo wptr` | 请求 FIFO 写指针 → alert |
| 39 | ReqFifoRptrCheck_A (rom_ctrl.sv:571) | `ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT: reqfifo rptr` | 请求 FIFO 读指针 → alert |
| 40 | SecCmCFILinear_A (rom_ctrl_fsm.sv:248) | `ASSERT_FPV_LINEAR_FSM: state_q` | checker FSM 必须是线性（无环）状态机 |
| 41 | RelAddrWide_A (rom_ctrl_fsm.sv:276) | `exp_digest_vld_o \|-> ~\|rel_addr_wide[AW-1:TAW]` | 读取顶部区域时相对地址高位为 0 |
| 42 | LastImpliesValid_A (rom_ctrl_fsm.sv:322) | `kmac_rom_last_o \|-> kmac_rom_vld_o` (disable on Invalid) | last 标志只在 valid 时为高 |
| 43 | CounterLntImpliesKmacRomVldO_A (rom_ctrl_fsm.sv:353) | `counter_lnt -> kmac_rom_vld_o` | counter_lnt（最后非顶部词）蕴含 kmac valid |
| 44 | reqParity (rom_ctrl_regs_reg_top.sv:870) | **被注释掉** (`//ASSUME(reqParity, ...)`) | 原约束 TL a_user.chk_en；已降级为注释，不再强制 |

## 四、树内参考
| # | 参考物 (绝对路径) | 类型 | 可对比什么 |
|---|---|---|---|
| 1 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/util/scramble_image.py | 参考实现（Python） | ROM scrambling 的地址置换 + PRINCE keystream + ECC 编码的完整实现；对比 RTL 中 `rom_ctrl_scrambled_rom` 的 PRINCE 参数 (NumRoundsHalf=3, HalfwayDataReg=1, HalfwayKeyReg=1) 和 `prim_subst_perm` 的 NumRounds=2 是否与脚本一致 |
| 2 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/doc/theory_of_operation.md | 行为规范文档 | cSHAKE256 计算、KMAC 接口时序、keymgr 集成、故障注入加固措辞；对照 FSM 状态转换和 alert 逻辑 |
| 3 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/doc/registers.md | 寄存器规范 | FATAL_ALERT_CAUSE 各位语义、DIGEST/EXP_DIGEST 的 swaccess=ro 约束；对照 reg_top 代码 |
| 4 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/doc/interfaces.md | 接口规范 | pwrmgr_data/keymgr_data/kmac_data 信号语义和时序；对照 RTL 端口连接 |
| 5 | rom_ctrl_fsm vs rom_ctrl_compare | 兄弟模块（同文件 FSM） | 两个 FSM 均用 `PRIM_FLOP_SPARSE_FSM` + `default: fsm_alert=1`; 对比 sparse 编码方案、default 态处理、alert 汇聚方式是否一致 |
| 6 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl_pkg.sv | FSM 枚举定义 | fsm_state_e 的 10-bit 稀疏编码值 + Hamming distance；对照 `PRIM_FLOP_SPARSE_FSM` 使用和实际 case 分支覆盖 |
| 7 | rom_ctrl_scrambled_rom vs prim_ram_1p_scr (注释引用) | 同构参考 | scrambled_rom 注释声称遵循 prim_ram_1p_scr 结构 (NumPrinceRoundsHalf=3, NumDiffRounds=2, NumAddrScrRounds=2)；可对照参数和 round 数 |

## 五、特殊结构提示
- **SEC_CM 多锚点**: COMPARE.CTR.CONSISTENCY 在 rom_ctrl_compare.sv 有 2 个锚点 (line 112 + 118, 分别对应 wait_addr_alert 和 done_addr_alert)；MUX.CONSISTENCY 在 rom_ctrl_mux.sv 有 2 个锚点 (line 89 + 95, sel_reverted + sel_q_reverted)；BUS.INTEGRITY 在 rom_ctrl.sv 有 2 个锚点 (line 184 + 331, ROM adapter + reg interface)
- **被注释 ASSUME**: rom_ctrl_regs_reg_top.sv:870 的 `reqParity` 假设被注释掉，不再是强制约束
- **条件实例化**: `SecDisableScrambling` 参数控制 gen_rom_scramble_enabled/disabled 和 gen_fsm_scramble_enabled/disabled 两条完整分支；disabled 分支跳过全部检查、rom_select_bus 绑死 MuBi4True、checker_alert=0
- **BUS.LOCAL_ESC 非标准实现**: rom_ctrl.sv:260-261 的 rvalid 抑制逻辑 `(bus_rom_rvalid_raw | bus_rom_req) & ~(internal_alert & ~bus_rom_req)` 比典型"alert 时 rvalid=0"多了 `bus_rom_req` 条件——允许已有请求在途时传递响应
- **FSM 线性约束**: rom_ctrl_fsm 的状态机被 SVA `SecCmCFILinear_A` 断言为线性（无环），对照 hjson 声明 CHECKER.CTRL_FLOW.CONSISTENCY
- **kmac_digest 两份 share 异或**: rom_ctrl.sv:127 `kmac_digest = kmac_data_i.digest_share0 ^ kmac_data_i.digest_share1`; 这是 KMAC 的 side-channel countermeasure，两份 share 必须异或还原真值
- **mux 单向性**: rom_ctrl_mux.sv:65 用 `mubi4_or_hi(sel_bus_q, sel_bus_i)` 确保选择信号只从 False→True 单向演进
- **fsm_state_e 编码**: rom_ctrl_pkg.sv:49-57 中 Done 态的低 4 位 = MuBi4True，其他态 = MuBi4False；这样 `in_state_done` 直接取低 4 位无需额外比较逻辑
- **alert 粘性**: rom_ctrl_mux.sv:103-108 `alert_q <= alert_q | alert_d` 使 mux alert 一旦置位不可清除；rom_ctrl.sv:441-442 alert_test 写触发 fatal alert 也是粘性的
- **冗余计数器 SVA 覆盖**: rom_ctrl.sv:556-573 对 u_tl_adapter_rom 内 6 个 FIFO 指针各有 ASSERT_PRIM_COUNT_ERROR_TRIGGER_ALERT，加上 rom_ctrl_compare.sv:129 的 addr 计数器，共 7 个冗余计数器被 SVA 约束
