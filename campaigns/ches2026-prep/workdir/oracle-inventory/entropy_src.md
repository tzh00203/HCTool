# entropy_src 盲预言机目录

## 元信息
- 树: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
- 扫描范围: hw/ip/entropy_src/{rtl,data,doc}
- SEC_CM 声明数: 12 / SVA 数: 45 / testplan 条目数: 12 (sec_cm) + 14 (func)

## 一、SEC_CM 声明 ↔ RTL 锚点
| # | SEC_CM 声明 (hjson:line) | RTL 锚点 (file:line) | 检验要点 |
|---|---|---|---|
| 1 | CONFIG.REGWEN (entropy_src.hjson:240) | entropy_src.sv:120 | REGWEN 仅在 MODULE_ENABLE=MuBi4False 且 SW_REGUPD=1 时为1；ME_REGWEN rw0c 一旦清0不可恢复 |
| 2 | CONFIG.MUBI (entropy_src.hjson:242) | entropy_src_core.sv:569, 703, 724, 743, 762, 1482, 1501, 1520, 2404 | 每个 mubi4_t 寄存器字段均有 mubi4_test_invalid 检查，pfa 信号驱动 RECOV_ALERT_STS 对应位；检查 pfe/pfa 赋值是否成对 |
| 3 | CONFIG.REDUN (entropy_src.hjson:244) | entropy_src_core.sv:2179 | alert_threshold_inv 必须 = ~alert_threshold；es_thresh_cfg_alert = (~alert_threshold_inv != alert_threshold)，不匹配时置 RECOV_ALERT_STS.ES_THRESH_CFG_ALERT |
| 4 | INTERSIG.MUBI (entropy_src.hjson:246) | entropy_src.sv:28, 30 | otp_en_entropy_src_fw_read/over 为 mubi8_t 类型，经 prim_mubi8_sync 同步后 mubi8_test_true_strict 控制 fw_read/fw_over 使能 |
| 5 | MAIN_SM.FSM.SPARSE (entropy_src.hjson:248) | entropy_src_core.sv:2846 | main_sm 用 `PRIM_FLOP_SPARSE_FSM，9-bit 稀疏编码，min Hamming 3；local_escalate_i 强制跳 Error 态 |
| 6 | ACK_SM.FSM.SPARSE (entropy_src.hjson:250) | entropy_src_core.sv:2991 | ack_sm 用 `PRIM_FLOP_SPARSE_FSM，6-bit 稀疏编码，min Hamming 3；local_escalate_i 强制跳 Error 态 |
| 7 | RNG.BKGN_CHK (entropy_src.hjson:252) | entropy_src_core.sv:1628, 1691, 1752, 1864, 1927 | repcnt/repcnts/adaptp/bucket/markov 五种健康测试均在 RNG 数据有效时持续运行；检查每个 HT 的 fail_pulse 生成逻辑 |
| 8 | FIFO.CTR.REDUN (entropy_src.hjson:254) | entropy_src_core.sv:1054, 2517, 2569, 2936 | esrng/distr/observe/esfinal 四个 FIFO 的 Secure=1，使用 prim_fifo_sync + 冗余指针；检查 err_o 连接 sfifo_*_int_err |
| 9 | CTR.REDUN (entropy_src.hjson:256) | entropy_src_core.sv:1564, 1671, 1732, 1801, 1843, 1906, 1975, 2016, 2080, 2122, 2145, 2238, 2253, 2268, 2282, 2297, 2313, 2327, 2342, 2356 | 窗口计数器 + 所有 HT 内部计数器 + 所有 cntr_reg（fail counters）均用 prim_count；检查 err_o 汇入 es_cntr_err |
| 10 | CTR.LOCAL_ESC (entropy_src.hjson:258) | entropy_src_core.sv:2845 | fatal_loc_events = es_cntr_err_sum \|\| es_sfifo_int_err \|\| es_main_sm_err_sum \|\| es_ack_sm_err_sum \|\| sha3_state_error_sum；连接至 main_sm.local_escalate_i |
| 11 | ESFINAL_RDATA.BUS.CONSISTENCY (entropy_src.hjson:260) | entropy_src_core.sv:3011 | es_rdata_capt_q 捕获上一次 esfinal pop 数据的 [63:0]，连续两次相同则 es_bus_cmp_alert=1，置 RECOV_ALERT_STS.ES_BUS_CMP_ALERT |
| 12 | TILE_LINK.BUS.INTEGRITY (entropy_src.hjson:262) | entropy_src.sv:121 | entropy_src_reg_top 的 intg_err_o 连接 intg_err_alert[1]（fatal alert）；reg_top 内含 TL-UL end-to-end integrity |

## 二、行为性描述句（hjson 原文 → 检验点）
| # | hjson 原文 (file:line) | 检验点 |
|---|---|---|
| 1 | "Registers are protected from writes." (entropy_src.hjson:241) | ME_REGWEN rw0c: 写0后不可回1 (entropy_src_core.sv:557)；REGWEN 由 es_hw_regwen 硬件驱动，当 MODULE_ENABLE!=MuBi4False 或 SW_REGUPD==0 时 REGWEN=0 |
| 2 | "Registers have multi-bit encoded fields." (entropy_src.hjson:243) | 检查全部 10 个 MuBi4 字段 + 1 个 MuBi8 OTP 输入：每个均有 mubi4_test_invalid → pfa → recov_alert_sts 位 |
| 3 | "Threshold register has an inverted copy to compare against." (entropy_src.hjson:245) | ALERT_THRESHOLD[15:0] vs ALERT_THRESHOLD_INV[31:16]；RTL 用 (~alert_threshold_inv != alert_threshold) 检测不匹配 (entropy_src_core.sv:2182) |
| 4 | "OTP signal used to enable software access to registers." (entropy_src.hjson:247) | otp_en_entropy_src_fw_read → en_entropy_src_fw_read → efuse_es_sw_reg_en 控制 ENTROPY_DATA 可读性 (entropy_src_core.sv:3042)；otp_en_entropy_src_fw_over → en_entropy_src_fw_over → efuse_es_sw_ov_en 控制 FW_OV 模式 |
| 5 | "The ENTROPY_SRC main state machine uses a sparse state encoding." (entropy_src.hjson:249) | main_sm_pkg 20 状态、9-bit、min Hamming 3 (entropy_src_main_sm_pkg.sv:10-52)；PRIM_FLOP_SPARSE_FSM 在 entropy_src_main_sm.sv:41 |
| 6 | "The ENTROPY_SRC ack state machine uses a sparse state encoding." (entropy_src.hjson:251) | ack_sm_pkg 3 状态、6-bit、min Hamming 3 (entropy_src_ack_sm_pkg.sv:9-33)；PRIM_FLOP_SPARSE_FSM 在 entropy_src_ack_sm.sv:25 |
| 7 | "Random number generator is protected with continuous background health checks." (entropy_src.hjson:253) | repcnt/repcnts/adaptp/bucket/markov 五种 HT 永远 active (entropy_src_core.sv:1113-1117)；fail 脉冲经 alert 计数器汇总，达阈值触发 main_sm → AlertState |
| 8 | "The FIFO pointers of several FIFOs are implemented with duplicate counters." (entropy_src.hjson:255) | 四个 FIFO 均用 Secure=1 的 prim_fifo_sync (entropy_src_core.sv:1055-1074, 2517, 2569, 2937)；冗余指针 err 汇入 sfifo_*_int_err |
| 9 | "Counter hardening for all health test counters." (entropy_src.hjson:257) | 每个 HT 内部计数器均用 prim_count (entropy_src_adaptp_ht.sv:53, entropy_src_bucket_ht.sv:52, entropy_src_markov_ht.sv:78, entropy_src_repcnt_ht.sv:75, entropy_src_repcnts_ht.sv:67)；err 汇入 count_err_o |
| 10 | "Redundant counter failures will cause a local escalation to the main state machine." (entropy_src.hjson:259) | fatal_loc_events 连接 main_sm.local_escalate_i (entropy_src_core.sv:2867)；main_sm 收到后跳 Error 态 (entropy_src_main_sm.sv:277) |
| 11 | "Comparison on successive bus values for the post-conditioned entropy seed bus." (entropy_src.hjson:261) | es_rdata_capt_q 存上次值，es_bus_cmp_alert = vld && vld_q && (capt_q == rdata[63:0]) (entropy_src_core.sv:3024-3025) |
| 12 | "Tilelink end-to-end bus integrity scheme." (entropy_src.hjson:263) | intg_err_alert[1] 连 fatal alert (entropy_src.sv:130)；reg_top 生成 intg_err_o |
| 13 | "When false, it becomes read-only." (ME_REGWEN desc, entropy_src.hjson:289) | ME_REGWEN swaccess=rw0c：一旦 SW 写 0，硬件无法回 1；MODULE_ENABLE 受 ME_REGWEN 门控 |
| 14 | "Setting this field to kMultiBitBool4True will enable the ENTROPY_SRC module." (entropy_src.hjson:364) | mubi4_test_true_strict 检测；非法值触发 es_enable_pfa → recov_alert |
| 15 | "When this bit true and the MODULE_ENABLE field is false, the REGWEN write enable bit read as true" (SW_REGUPD desc, entropy_src.hjson:304) | es_hw_regwen = sw_regupd.q && mubi4_test_false_loose(module_en) && !es_delayed_enable (entropy_src_core.sv:557-559) |
| 16 | "ALERT_THRESHOLD_INV: This should be set to the value above, but inverted." (entropy_src.hjson:1176) | resval ALERT_THRESHOLD=0x0002, ALERT_THRESHOLD_INV=0xfffd；RTL 检查 (~INV != THRESH) |
| 17 | "Reading this register while the observe FIFO is empty results in a fatal error" (FW_OV_RD_DATA desc, entropy_src.hjson:1408) | sfifo_observe_err[1] (read-while-empty) 连 ERR_CODE.SFIFO_OBSERVE_ERR |
| 18 | "If the value of this register reaches the value configured in the ALERT_THRESHOLD register, a recoverable alert is raised and the ENTROPY_SRC block stops operating." (ALERT_SUMMARY_FAIL_COUNTS desc, entropy_src.hjson:1188) | any_fail_count >= alert_threshold → alert_threshold_fail → main_sm 转 AlertState → recov_alert |

## 三、SVA 清单（行为合同）
| # | 断言 (file:line) | 内容摘要 | 约束的预期行为 |
|---|---|---|---|
| 1 | RngFipsOutputHighInFipsMode_A (entropy_src_core.sv:3107) | rng_fips_o 仅在 CONF.RNG_FIPS 为 MuBi4True 时输出高 | FIPS 模式标志与 RNG FIPS 输出一致 |
| 2 | RngBackpressureNotAllowed_A (entropy_src_core.sv:1098) | esrng FIFO push 时必须 not_full | RNG 输入不可背压，丢样本即致命 |
| 3 | ValidRngBitsPushedIntoEsrngFifo_A (entropy_src_core.sv:3149) | RNG 有效位数 ≈ esrng push 位数（允许每次 re-enable 丢 RngBusWidth 位） | RNG 数据无损进入 esrng FIFO |
| 4 | EsrngFifoPushedIntoEsbitOrPosthtFifos_A (entropy_src_core.sv:3180) | esrng push 位 = esbit push×4 + postht_from_esrng push 位 | esrng 到 esbit/postht 数据完整性 |
| 5 | EsbitFifoPushedIntoPosthtFifo_A (entropy_src_core.sv:3198) | esbit push 位 = postht_from_esbit push 位 | 单 bit 模式数据完整性 |
| 6 | PosthtFifoPushedFromEsbitOrEsrngFifos_A (entropy_src_core.sv:3207) | postht 总 push = from_esbit + from_esrng | postht 数据来源完整性 |
| 7 | PosthtFifoPushedIntoDistrFifo_A (entropy_src_core.sv:3228) | 非 bypass 模式：postht pop 位 = distr push 位 | HT 后数据进入 distr FIFO |
| 8 | DistrFifoPushedIntoPreconFifo_A (entropy_src_core.sv:3248) | 非 bypass 模式：distr pop 位 = precon push 位 | distr 到 precon 数据完整性 |
| 9 | EsfinalFifoPushed_A (entropy_src_core.sv:3321) | 非 bypass 模式：esfinal push 均来自已通过 startup 检查的数据 | 无未通过 startup 的数据进入 esfinal |
| 10 | NoPushAfterFailedHealthTest_A (entropy_src_core.sv:3350) | HT 失败后不可 push 到 esfinal | 失败数据被丢弃 |
| 11 | PreconPostStartupDiffNonNegative_A (entropy_src_core.sv:3389) | precon 实际 push ≥ 预期 push | 条件器输入无短缺 |
| 12 | PreconPostStartupDiffSmall_A (entropy_src_core.sv:3394) | precon 实际 push - 预期 push < 4×window | 条件器输入差异上界 |
| 13 | HealthTestWindowStableWhenEnabled_A (entropy_src_core.sv:3400) | es_enable 为真时 health_test_window 不变 | HT 窗口大小在运行中不可变 |
| 14 | EsfinalFifoPushedPostStartup_A (entropy_src_core.sv:3404) | esfinal 实际 push = 预期 push | startup 后 esfinal 完整性 |
| 15 | PreconFifoPushedPostStartup_A (entropy_src_core.sv:3414) | precon 实际 push ≈ 预期 push（允许上溢 4×window） | precon 累积一致性 |
| 16 | FifosEmptyWhenShaProcess_A (entropy_src_core.sv:3483) | 非 FW_OV 模式下 sha3_process 触发时 postht/distr/precon FIFO 必须空 | SHA3 吸收前无残留数据 |
| 17 | TlDValidKnownO_A (entropy_src.sv:243) | tl_o.d_valid 已知值 | TL 输出有效性 |
| 18 | TlAReadyKnownO_A (entropy_src.sv:244) | tl_o.a_ready 已知值 | TL 输出就绪 |
| 19 | EsHwIfEsAckKnownO_A (entropy_src.sv:247) | es_ack 已知值 | HW 接口 ack 信号完整性 |
| 20 | EsHwIfEsBitsKnownO_A (entropy_src.sv:248) | es_ack 时 es_bits 已知值 | HW 接口数据有效性 |
| 21 | EsHwIfEsFipsKnownO_A (entropy_src.sv:250) | es_ack 时 es_fips 已知值 | HW 接口 FIPS 标志有效性 |
| 22 | EsRngEnableKnownO_A (entropy_src.sv:254) | rng_enable 已知值 | RNG 使能信号完整性 |
| 23 | EsXhtEntropyBitKnownO_A (entropy_src.sv:257) | XHT valid 时 entropy_bit 已知值 | 外部 HT 数据有效性 |
| 24 | EsXhtEntropyBitValidKnownO_A (entropy_src.sv:259) | entropy_bit_valid 已知值 | 外部 HT valid 信号完整性 |
| 25 | EsXhtClearKnownO_A (entropy_src.sv:260) | XHT clear 已知值 | 外部 HT clear 信号完整性 |
| 26 | EsXhtActiveKnownO_A (entropy_src.sv:261) | XHT active 已知值 | 外部 HT active 信号完整性 |
| 27 | EsXhtThreshHiKnownO_A (entropy_src.sv:262) | XHT thresh_hi 已知值 | 外部 HT 阈值完整性 |
| 28 | EsXhtThreshLoKnownO_A (entropy_src.sv:263) | XHT thresh_lo 已知值 | 外部 HT 阈值完整性 |
| 29 | EsXhtWindowKnownO_A (entropy_src.sv:264) | XHT window_wrap_pulse 已知值 | 外部 HT 窗口信号完整性 |
| 30 | AlertTxKnownO_A (entropy_src.sv:267) | alert_tx_o 已知值 | Alert 输出完整性 |
| 31 | IntrEsEntropyValidKnownO_A (entropy_src.sv:270) | intr_es_entropy_valid_o 已知值 | 中断输出完整性 |
| 32 | IntrEsHealthTestFailedKnownO_A (entropy_src.sv:271) | intr_es_health_test_failed_o 已知值 | 中断输出完整性 |
| 33 | IntrEsFifoErrKnownO_A (entropy_src.sv:272) | intr_es_fatal_err_o 已知值 | 中断输出完整性 |
| 34 | CntAlertCheck0_A (entropy_src.sv:275) | window_cntr count error → fatal alert | 窗口计数器错误触发致命告警 |
| 35 | CntAlertCheck1_A×4 (entropy_src.sv:280) | adaptp HT count error → fatal alert | 自适应比例计数器错误触发致命告警 |
| 36 | CntAlertCheck_A×16 (entropy_src.sv:286) | bucket HT 16个 bin count error → fatal alert | 桶计数器错误触发致命告警 |
| 37 | CntAlertCheck_A×4 (entropy_src.sv:292) | markov HT pair count error → fatal alert | Markov 计数器错误触发致命告警 |
| 38 | CntAlertCheck_A×4 (entropy_src.sv:298) | repcnt HT rep count error → fatal alert | 重复计数器错误触发致命告警 |
| 39 | CntAlertCheck7_A (entropy_src.sv:303) | repcnts HT count error → fatal alert | 重复符号计数器错误触发致命告警 |
| 40 | CtrlMainFsmCheck_A (entropy_src.sv:307) | main_sm FSM error → fatal alert | 主 FSM 错误触发致命告警 |
| 41 | CtrlAckFsmCheck_A (entropy_src.sv:311) | ack_sm FSM error → fatal alert | ACK FSM 错误触发致命告警 |
| 42 | SHA3FsmCheck_A (entropy_src.sv:315) | SHA3 FSM error → fatal alert | SHA3 FSM 错误触发致命告警 |
| 43 | KeccakRoundFsmCheck_A (entropy_src.sv:318) | Keccak round FSM error → fatal alert | Keccak FSM 错误触发致命告警 |
| 44 | SHA3padFsmCheck_A (entropy_src.sv:321) | SHA3 pad FSM error → fatal alert | SHA3 pad FSM 错误触发致命告警 |
| 45 | RegWeOnehotCheck_A (entropy_src.sv:436) | reg_we onehot error → fatal alert | 寄存器写使能独热码错误触发致命告警 |

## 四、树内参考
| # | 参考物 (绝对路径) | 类型 | 可对比什么 |
|---|---|---|---|
| 1 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_adaptp_ht.sv | 兄弟模块 | 与 markov_ht 同构：均有 gen_cntrs 循环 + prim_count + prim_max_tree(u_max/u_min) + prim_sum_tree + rng_bit_en/threshold_scope 分支；adaptp 用 entropy_bit_i[sh] 作 step，markov 用 samples_no_match_pulse 作 incr |
| 2 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_markov_ht.sv | 兄弟模块 | 与 adaptp_ht 对比：markov 额外有 toggle_q/prev_sample_q 采样对逻辑；**注意 markov_ht test_fail_hi/lo_pulse_o 固定 1'b0（行 158-159）**——与 adaptp 的 active_i && window_wrap_pulse_i && (cnt > thresh) 逻辑不同，这可能是刻意的（markov 只报告 watermark 不生成 fail pulse）也可能候选漏洞 |
| 3 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_repcnt_ht.sv | 兄弟模块 | 连续 HT：单 bit 重复检测；与 repcnts_ht 对比（repcnts 检测符号级重复）；repcnt 有 per-line rep_cntr + prim_max_tree 取 max，repcnts 只有一个 rep_cntr |
| 4 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_repcnts_ht.sv | 兄弟模块 | 符号级重复计数；与 repcnt_ht 对比：repcnts 无 per-line 循环，单计数器 |
| 5 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_bucket_ht.sv | 兄弟模块 | 16-bin 直方图；用 gen_symbol_match 循环 + prim_count + prim_max_tree 取 max；fail 逻辑 = active && wrap && (\|bin_cnt_exceeds_thresh) |
| 6 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_main_sm_pkg.sv | 规范注释 | 稀疏 FSM 编码：20 状态、9-bit、seed 2359261201、min Hamming 3；可用于验证 RTL 状态编码是否与包一致 |
| 7 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_ack_sm_pkg.sv | 规范注释 | 稀疏 FSM 编码：3 状态、6-bit、seed 1236774883、min Hamming 3；可用于验证 RTL 状态编码一致性 |
| 8 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/data/entropy_src_sec_cm_testplan.hjson | testplan | 12 条 sec_cm 验证点，每条声明测试名 + 描述 + stage；用于检验哪些 SEC_CM 有对应验证覆盖 |
| 9 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/doc/theory_of_operation.md | 规范注释 | NIST SP 800-90B 健康测试理论；startup 需连续两个窗口通过；窗口大小最小 512 建议；bypass 模式仅支持 384 |

## 五、特殊结构提示

### 5.1 Markov HT fail pulse 硬布零
- entropy_src_markov_ht.sv:158-159: `test_fail_hi_pulse_o = 1'b0; test_fail_lo_pulse_o = 1'b0;`
- 与 adaptp_ht（行128-129）的 `active_i && window_wrap_pulse_i && (cnt > thresh)` 模式不一致
- hjson MARKOV_HI/LO_THRESHOLDS 寄存器存在且可写（entropy_src.hjson:714-782），RECOV_ALERT_STS 有 MARKOV 对应位
- **检验**：检查 markov 的 fail_pulse 是否被 core 使用，以及 alert_fail_counts.markov_hi/lo_fail_count 是否有实际递增来源

### 5.2 阈值单更新（one-way）机制
- 所有 HT 阈值寄存器均用 entropy_src_watermark_reg 实现"只能收紧不能放松"
- 高阈值：写入值 < 当前值才更新；低阈值：写入值 > 当前值才更新
- entropy_src_core.sv:1460-1470: extht_lo_bypass 的 watermark_reg 也用 HighWatermark(1) 参数（逻辑反转为低阈值）
- **检验**：确认 one-way 更新逻辑对 bypass 和 fips 阈值均生效

### 5.3 ALERT_THRESHOLD 冗余校验
- ALERT_THRESHOLD[15:0] 和 ALERT_THRESHOLD_INV[31:16] 互为反码
- entropy_src_core.sv:2182: `es_thresh_cfg_alert = (~alert_threshold_inv != alert_threshold)`
- alert_threshold_fail 使用两种判定路径（行 2184-2186）：(any_fail_count >= ~INV && ~INV!=0) || (any_fail_count >= THRESH && THRESH!=0)
- **检验**：确认两条路径的等价性——若 INV == ~THRESH，两条路径等价；若不等，es_thresh_cfg_alert 触发 recov_alert

### 5.4 es_enable_fo 扇出检查
- EsEnableCopies = 20，es_enable_fo[0..19] 分别用于门控不同功能
- entropy_src_core.sv:607-609: 每个副本独立 mubi4_test_true_strict
- **检验**：确认所有 es_enable_fo[i] 引用的索引范围 [0,19] 无越界

### 5.5 Main SM 状态转换完整性
- entropy_src_main_sm.sv: 20 状态 + Error + default
- 关键路径：Idle→BootHTRunning/StartupHTStart/FWInsertStart; AlertState→AlertHang; Error 不可退出
- local_escalate_i 优先级高于所有状态转换（行 277-279）
- **检验**：确认 enable_i==0 在所有非-Sha3Processing 状态均能转回 Idle

### 5.6 FW_OV 模式安全性
- fw_ov_mode 需要 otp_en_entropy_src_fw_over == MuBi8True
- fw_ov_entropy_insert 需要 fw_ov_mode && fw_ov_entropy_insert_pfe
- 禁用 fw_ov_sha3_start 时若 bypass packer FIFO 非空 → es_fw_ov_disable_alert → RECOV_ALERT_STS.ES_FW_OV_DISABLE_ALERT
- fw_ov_corrupted 机制标记后续两个 esfinal 输出为损坏 (entropy_src_core.sv:2909-2913)

### 5.7 观测 FIFO 读空致命错误
- entropy_src.hjson:1408: 读空 observe FIFO → FIFO_READ_ERR + SFIFO_OBSERVE_ERR → fatal alert
- sfifo_observe_err[1] = (sfifo_observe_pop && !sfifo_observe_not_empty)
- **检验**：确认 observe FIFO pop 信号在空时不会误触（是否有空 FIFO 保护逻辑）

### 5.8 SHA3/Keccak 子模块 FSM 断言
- entropy_src.sv:315-328: SHA3 FSM + Keccak round FSM + SHA3 pad FSM + sentmsg_count + round_count 均有 ASSERT_PRIM_*_ERROR_TRIGGER_ALERT 连接到 fatal alert (alert_tx_o[1])
- 这些子模块不在 entropy_src/rtl/ 下（可能在 prim/ 下），但断言在顶层 entropy_src.sv 中
