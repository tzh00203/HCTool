# entropy_src 候选漏洞清单

## 覆盖摘要
- 扫描文件：entropy_src_core.sv, entropy_src.sv, entropy_src_markov_ht.sv, entropy_src_adaptp_ht.sv,
  entropy_src_bucket_ht.sv, entropy_src_repcnt_ht.sv, entropy_src_repcnts_ht.sv,
  entropy_src_main_sm.sv, entropy_src_ack_sm.sv, entropy_src_main_sm_pkg.sv, entropy_src_ack_sm_pkg.sv,
  entropy_src_pkg.sv, entropy_src_watermark_reg.sv, entropy_src_cntr_reg.sv,
  entropy_src_field_en.sv, entropy_src_enable_delay.sv,
  entropy_src_reg_top.sv (spot-checked), entropy_src.hjson (full)
- L1 SEC_CM-vs-RTL: 2 条（CAND-1, CAND-2）
- L2 hjson-spec-vs-RTL: 3 条（CAND-3, CAND-4, CAND-5）
- L3 树内参考对比: 1 条（CAND-6）
- L4 结构 lint: 2 条（CAND-7, CAND-8）
- L5 常量折叠: 0 条（entropy_src 无混淆常量）
- L6 SCA 结构: 1 条（CAND-9）
- 未覆盖区域：entropy_src_reg_top.sv（仅 spot-checked we/re/d 逻辑）、prim 子模块（不在 entropy_src/rtl/ 下）、
  DV 环境、doc/theory_of_operation.md（仅作为预言机参考使用）

---

### CAND-entropy_src-1
- 疑点: markov_ht fail_pulse 硬布零，hjson 声明的 MARKOV 健康测试永不触发 fail
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_markov_ht.sv:158-159
  ```systemverilog
  assign test_fail_hi_pulse_o = 1'b0;
  assign test_fail_lo_pulse_o = 1'b0;
  ```
- lens: L1 SEC_CM-vs-RTL + L3 树内参考
- 预言机依据:
  1. SEC_CM 声明 RNG.BKGN_CHK（hjson:252）声称五种健康测试"continuous background health checks"，
     markov 是五种之一，但 fail_pulse=0 意味着 markov 永不报告失败
  2. hjson MARKOV_HI/LO_THRESHOLDS 寄存器存在且可写（hjson:714-782），
     RECOV_ALERT_STS 有 MARKOV 对应位，ALERT_FAIL_COUNTS 有 MARKOV_HI/LO_FAIL_COUNT（hjson:1246-1255），
     但 RTL 中 markov_hi_fail_pulse / markov_lo_fail_pulse 恒零，
     any_fail_pulse（core:2162）中 markov 分量永远为 0
  3. adaptp_ht 兄弟模块行 128-129 用 `active_i && window_wrap_pulse_i && (cnt > thresh)` 正常产生 fail pulse，
     bucket_ht 行 85 同理，repcnt_ht 行 92/126 同理——markov 唯一硬布零
  4. core:1982/2023 的 markov_hi/lo_total_fails cntr_reg 接收 markov_hi/lo_fail_pulse 作 event_i，
     但 event 永零 → total_fails 永零 → SW 读到的 MARKOV 总失败数永远为零
- 建议验证型: 组合 micro-tb：对 markov_ht 注入已知 Markov 失败模式（相邻采样对不匹配计数 > 阈值），
  观测 test_fail_hi/lo_pulse_o 是否在 window_wrap_pulse_i 时置 1

---

### CAND-entropy_src-2
- 疑点: SHA3 子模块 lc_escalate_en_i 硬布 Off，生命周期升级不触发 SHA3 致命错误
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv:2770
  ```systemverilog
  .lc_escalate_en_i (lc_ctrl_pkg::Off),
  ```
- lens: L1 SEC_CM-vs-RTL + L2 hjson-spec-vs-RTL
- 预言机依据:
  1. CTR.LOCAL_ESC SEC_CM（hjson:258）声称"Redundant counter failures will cause a local escalation
     to the main state machine"，但 SHA3 FSM/Keccak FSM 的错误虽通过 fatal_loc_events 传播到 main_sm，
     lc_escalate 信号未接入——若外部生命周期要求立即停机，SHA3 子模块不会响应
  2. 对比 kmac 中 sha3 实例连接 lc_escalate_en_i 到真实 lc 信号，
     entropy_src 的 sha3 将其硬布 Off
  3. entropy_src.sv:315-328 的 ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT 确实将 SHA3 FSM 错误连到 fatal alert，
     但这些仅覆盖 FSM 稀疏编码错误，不覆盖 lc_escalate 触发的主动停机
- 建议验证型: 时序 tb：在 SHA3 吸收过程中注入 lc_escalate_en=On，观测 SHA3 是否停止并触发 fatal alert

---

### CAND-entropy_src-3
- 疑点: es_rng_src_valid 被 entropy_data_reg_enable 门控——当 ENTROPY_DATA_REG_ENABLE=MuBi4False(全零)
  时 RNG 数据不进入 esrng FIFO，整个熵管道停摆
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv:812-814
  ```systemverilog
  // Enhanced validation with additional configuration checks
  assign es_rng_src_valid = entropy_src_rng_i.rng_valid &
                         (reg2hw.conf.entropy_data_reg_enable.q != '0);
  ```
- lens: L2 hjson-spec-vs-RTL + L4 结构 lint
- 预言机依据:
  1. hjson 对 ENTROPY_DATA_REG_ENABLE 的描述（hjson:~370）仅控制"Is the ENTROPY_DATA register
     readable"，不影响 RNG 数据接收或健康测试运行
  2. 原始 OpenTitan 此行应为 `assign es_rng_src_valid = entropy_src_rng_i.rng_valid;`，
     当前代码用 `entropy_data_reg_enable.q != '0` 额外门控——注释 "Enhanced validation"
     表明这是注入的修改
  3. 当 ENTROPY_DATA_REG_ENABLE = 4'b0000（原始全零值，非 MuBi4False=4'b1010），
     `!= '0` 为假 → es_rng_src_valid=0 → sfifo_esrng_push(core:1079)=0 →
     无 RNG 数据进入管道 → 所有健康测试无数据 → 无熵输出
  4. SVA ValidRngBitsPushedIntoEsrngFifo_A（core:3149）约束 esrng push 位数≈RNG 有效位数，
     但若 rng_src_valid 被门控，该断言的 LHS 在 rng_valid=1 时也不 push，
     断言将失败（若启用）
- 建议验证型: micro-tb：设置 ENTROPY_DATA_REG_ENABLE=0 后 enable 模块，观测 esrng FIFO 是否收到 RNG 数据

---

### CAND-entropy_src-4
- 疑点: markov HT 的 fail_count 在 ALERT_FAIL_COUNTS 中有字段但永不递增（因 fail_pulse 恒零）
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv:2320, 2334
  ```systemverilog
  .event_i             (markov_hi_fail_pulse),  // always 1'b0
  ...
  .event_i             (markov_lo_fail_pulse),  // always 1'b0
  ```
- lens: L2 hjson-spec-vs-RTL
- 预言机依据:
  1. hjson:1246-1255 声明 ALERT_FAIL_COUNTS.MARKOV_HI_FAIL_COUNT / MARKOV_LO_FAIL_COUNT 字段，
     描述为"The number of health test windows during which this test failed since the last passing window"
  2. RTL 中 markov_hi/lo_fail_pulse 恒零 → cntr_reg 的 event_i 永零 →
     markov_hi/lo_fail_count 永零 → hw2reg.alert_fail_counts.markov_hi/lo_fail_count.d 永零
  3. hjson:1188 声明 "If the value of this register reaches the value configured in the
     ALERT_THRESHOLD register, a recoverable alert is raised"——
     markov 的贡献永远为零，等于从 alert 计数中排除
- 建议验证型: 同 CAND-entropy_src-1 验证方案

---

### CAND-entropy_src-5
- 疑点: MARKOV_HI/LO_THRESHOLDS 寄存器存在且可写，但写值对健康测试无实际效果（fail 永不触发）
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv:1940-1941
  ```systemverilog
  .thresh_hi_i         (markov_hi_threshold),
  .thresh_lo_i         (markov_lo_threshold),
  ```
  阈值传入了 markov_ht 但 markov_ht 行 158-159 将 fail_pulse 硬布零，阈值比较结果被丢弃
- lens: L2 hjson-spec-vs-RTL
- 预言机依据:
  1. hjson:714-782 MARKOV_HI/LO_THRESHOLDS 寄存器有完整描述，含 FIPS_THRESH/BYPASS_THRESH，
     写入约束 one-way 机制，resval 分 FIPS/BYPASS——表明设计意图是阈值控制 fail 触发
  2. RTL 中 markov_ht 接收 thresh_hi_i/thresh_lo_i 但仅用于 test_cnt_hi_o/lo_o 输出
     （供 watermark_reg 使用），不参与 fail 判定
  3. 对比 adaptp_ht 行 128-129：`test_fail_hi_pulse_o = active_i && window_wrap_pulse_i && (test_cnt_hi_o > thresh_hi_i)`
     ——阈值直接参与 fail 判定
- 建议验证型: 同 CAND-entropy_src-1 验证方案

---

### CAND-entropy_src-6
- 疑点: markov_ht 与 adaptp_ht 的 fail_pulse 模式不一致——兄弟模块同接口不同行为
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_markov_ht.sv:158-159
  vs /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_adaptp_ht.sv:128-129
  ```systemverilog
  // markov_ht:
  assign test_fail_hi_pulse_o = 1'b0;
  assign test_fail_lo_pulse_o = 1'b0;
  // adaptp_ht:
  assign test_fail_hi_pulse_o = active_i && window_wrap_pulse_i && (test_cnt_hi_o > thresh_hi_i);
  assign test_fail_lo_pulse_o = active_i && window_wrap_pulse_i && (test_cnt_lo_o < thresh_lo_i);
  ```
- lens: L3 树内参考
- 预言机依据:
  1. adaptp_ht、bucket_ht、repcnt_ht、repcnts_ht 四个兄弟模块均用 active && (window condition) && (threshold comparison) 模式
  2. markov_ht 是唯一将 fail_pulse 硬布零的——结构性异常
  3. 所有五个 HT 的端口签名一致（test_fail_hi/lo_pulse_o 或 test_fail_pulse_o），
     core 的实例化也一致连接到 any_fail_pulse
  4. 这符合 fixed-value-signal 模式（OT-025, markov GT 实例）
- 建议验证型: 同 CAND-entropy_src-1 验证方案

---

### CAND-entropy_src-7
- 疑点: rng_bit_sel 被 health_test_window[0] 掩码，在单比特模式下可能改变 RNG 位选择行为
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv:2424
  ```systemverilog
  assign rng_bit_sel = reg2hw.conf.rng_bit_sel.q & {1'b1, health_test_window[0]};
  ```
- lens: L4 结构 lint
- 预言机依据:
  1. hjson 对 RNG_BIT_SEL 的描述仅说"Selects which RNG bit to use in single-bit mode"（2-bit 字段），
     无提及掩码或与 health_test_window 的交互
  2. 原始代码应为 `assign rng_bit_sel = reg2hw.conf.rng_bit_sel.q;`
  3. 当 health_test_window[0]=0 时，rng_bit_sel 的低位被强制为 0，
     即 rng_bit_sel 值为 2'b00 或 2'b10 的行为一致（都选 bit[0]），
     但 2'b01 和 2'b11 的行为不一致（01→00 选 bit[0]，11→10 选 bit[2]）
  4. adaptp_ht/repcnt_ht/markov_ht 的 rng_bit_sel_i 均受此影响——
     窗口计数器的低位清零期间，位选择可能意外切换
- 建议验证型: micro-tb：在 rng_bit_en=1 模式下，设置 rng_bit_sel=2'b01，
  观测 health_test_window[0]=0 期间实际选择的 RNG 位是否为 bit[0] 而非 bit[1]

---

### CAND-entropy_src-8
- 疑点: distr FIFO 错误的 write/read/state 类型在 ERR_CODE 中无对应位
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv:947-961
  ```systemverilog
  assign fifo_write_err_sum =
         sfifo_esrng_err[2] ||
         sfifo_observe_err[2] ||
         sfifo_esfinal_err[2] ||    // no sfifo_distr_err[2]
         err_code_test_bit[28];
  assign fifo_read_err_sum =
         sfifo_esrng_err[1] ||
         sfifo_observe_err[1] ||
         sfifo_esfinal_err[1] ||    // no sfifo_distr_err[1]
         err_code_test_bit[29];
  assign fifo_status_err_sum =
         sfifo_esrng_err[0] ||
         sfifo_observe_err[0] ||
         sfifo_esfinal_err[0] ||    // no sfifo_distr_err[0]
         err_code_test_bit[30];
  ```
- lens: L4 结构 lint
- 预言机依据:
  1. sfifo_distr_err 是 3-bit 结构 {write_err, read_err, status_err}（core:2560-2563），
     与 esrng/observe/esfinal 相同
  2. SFIFO_DISTR_ERR 在 ERR_CODE 中存在（hjson:1665），由 sfifo_distr_err_sum 驱动（core:967-968）
  3. 但 fifo_write_err/fifo_read_err/fifo_state_err 类型位不包含 distr FIFO 的分量——
     SW 无法从 ERR_CODE 类型位判断 distr FIFO 错误的具体类型
  4. 致命 alert 仍然触发（sfifo_distr_int_err 汇入 es_sfifo_int_err → fatal_loc_events），
     但诊断信息不完整
- 建议验证型: 脚本检查：grep fifo_write_err_sum/fifo_read_err_sum/fifo_status_err_sum 是否包含 sfifo_distr_err

---

### CAND-entropy_src-9
- 疑点: SHA3 条件器 EnMasking=0 且 rand 输入全零——无 SCA 掩码保护，SHA3 吸收过程可被侧信道观测
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv:80, 2749-2754
  ```systemverilog
  localparam bit Sha3EnMasking = 0;
  ...
  .rand_valid_i    (1'b0),
  .rand_early_i    (1'b0),
  .rand_data_i     ('0),
  .rand_aux_i      ('0),
  ```
- lens: L6 SCA 结构
- 预言机依据:
  1. SHA3 子模块支持 EnMasking=1 的掩码实现（有 sha3_pkg::EnMasking 参数），
     当 EnMasking=1 时使用两个 share 的 DOM-independence 实现
  2. 当前 entropy_src 设置 EnMasking=0，使用单 share 实现，Keccak 置换的中间值直接可见
  3. rand 输入全零——不提供 PRD 给域交叉随机化
  4. 对比 kmac 的 SHA3 实例通常设置 EnMasking=1 并连接 EDN rand 输入
  5. 注：entropy_src 的 SHA3 仅用作确定性条件器（NIST SP 800-90B 许可），
     SCA 风险低于密码直接使用场景，但仍可泄露内部熵状态
- 建议验证型: 时序 tb：对比 EnMasking=0 和 EnMasking=1 两种配置下 SHA3 吸收过程的功耗差分轨迹

---

### CAND-entropy_src-10
- 疑点: alert_threshold_fail 的双路径判定逻辑冗余但存在边界条件差异——当 alert_threshold=0 时
  仅 ~INV 路径生效，当 ~INV=0 时仅 THRESH 路径生效，两者非完全等价
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv:2182-2186
  ```systemverilog
  assign es_thresh_cfg_alert = (~alert_threshold_inv != alert_threshold);
  assign alert_threshold_fail =
         ((any_fail_count >= ~alert_threshold_inv) && (~alert_threshold_inv != '0)) ||
         (any_fail_count >= alert_threshold) && (alert_threshold != '0);
  ```
- lens: L2 hjson-spec-vs-RTL
- 预言机依据:
  1. SEC_CM CONFIG.REDUN（hjson:244）声称"Threshold register has an inverted copy to compare against"
  2. hjson:1175-1177 描述 ALERT_THRESHOLD_INV "should be set to the value above, but inverted"
     （resval: THRESH=0x0002, INV=0xfffd，满足 ~INV == THRESH）
  3. 当 ~INV == THRESH 且均非零时，两条路径等价
  4. 但当 THRESH=0 时，仅 ~INV 路径生效；当 ~INV=0 时仅 THRESH 路径生效——
     若 SW 误写 THRESH=0（虽然 one-way 机制阻止放松），alert 仅走 ~INV 路径
  5. es_thresh_cfg_alert 检测 ~INV != THRESH 的不匹配，触发 recov_alert——
     但若 SW 在 enable 前写入不一致值，在 es_thresh_cfg_alert 触发前可能已用错误阈值运行一个窗口
- 建议验证型: micro-tb：设置 alert_threshold=0, alert_threshold_inv!=0xFFFF，
  观测 alert_threshold_fail 是否仅走 ~INV 路径及 es_thresh_cfg_alert 是否及时触发

---

### CAND-entropy_src-11
- 疑点: markov HT 的 watermark_reg 接收 test_cnt 输出但不反映 fail 信息——
    watermark 只跟踪计数值，不跟踪阈值违反，与 hjson 对 RECOV_ALERT_STS 的 Markov 位描述不一致
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv:1954-1961
  ```systemverilog
  entropy_src_watermark_reg #(
    .RegWidth(HalfRegWidth),
    .HighWatermark(1)
  ) u_entropy_src_watermark_reg_markov_hi_fips (
    ...
    .value_i             (markov_hi_event_cnt),  // cnt from markov_ht, no fail info
    .value_o             (markov_hi_event_hwm_fips)
  );
  ```
- lens: L3 树内参考
- 预言机依据:
  1. adaptp_ht 的 watermark_reg 同样接收 test_cnt，但 adaptp 的 fail_pulse 真正工作——
     watermark 跟踪的 cnt 在 fail 时确实反映阈值违反
  2. markov_ht 的 cnt 也真实反映了 pair counter 值，但 fail 永不触发 →
     SW 无法从 watermark 判断是否曾经超过阈值（只能看值本身是否大于阈值）
  3. 这与 CAND-1/4/5/6 是同一根因的不同面——markov fail 机制的全面失效
- 建议验证型: 同 CAND-entropy_src-1 验证方案

---

### CAND-entropy_src-12
- 疑点: es_rng_src_valid 被 entropy_data_reg_enable 门控违反 SVA RngBackpressureNotAllowed_A 的前提——
    该断言假设 esrng FIFO 在 enable 时总接收 RNG 数据，但门控后可能不接收
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv:1098
  ```systemverilog
  `ASSERT(RngBackpressureNotAllowed_A, sfifo_esrng_push |-> sfifo_esrng_not_full)
  ```
  配合 core:1079:
  ```systemverilog
  assign sfifo_esrng_push = es_enable_fo[5] && es_delayed_enable && es_rng_src_valid &&
                            rng_enable_q;
  ```
- lens: L4 结构 lint
- 预言机依据:
  1. SVA RngBackpressureNotAllowed_A 约束"push 时必须 not_full"，
     前提是 RNG 数据在 enable 时必须被接收
  2. 但 es_rng_src_valid 被 entropy_data_reg_enable 门控后，push 可能在 enable 且 rng_valid=1 时不触发——
     这不违反该断言本身（断言仅约束 push→not_full），但违反设计意图：
     注释（core:1077-1078）明确说"the input coming from the noise source / RNG
     needs to be accepted without dropping samples"
- 建议验证型: 同 CAND-entropy_src-3 验证方案
