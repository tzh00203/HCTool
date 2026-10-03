# Ascon IP — 6-lens 盲猎候选清单

## 覆盖摘要

- **扫描文件**: ascon.sv, ascon_core.sv, ascon_pkg.sv, ascon_reg_pkg.sv, ascon_reg_top.sv, prim_ascon_duplex.sv, prim_ascon_pkg.sv, prim_ascon_round.sv, prim_ascon_sbox.sv, ascon.hjson
- **每 lens 产出**: L1=5, L2=9, L3=3, L4=5, L5=5, L6=5 条候选
- **未覆盖区域**: full AEAD 端到端功能验证（需 DPI testbench 对比 vendored ascon-c）；时序/门级仿真未覆盖；prim_ascon_round_tb / prim_ascon_duplex_tb 中的 Verilator C++ 驱动未审计

---

## L1 SEC_CM-vs-RTL

### CAND-ASCON-01
- 疑点: hjson 无 sec_cm 字段——ascon IP 全部安全对策未声明
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/data/ascon.hjson（整个文件无 sec_cm 段）
- lens: L1
- 预言机依据: 同级 IP（aes/hmac/kmac）均有 sec_cm 声明；RTL 中存在 sparse FSM（prim_ascon_duplex.sv:603）、prim_count（:172）、shadowed regs（ascon_reg_top.sv:1128-1592）、TL-UL integrity（:52-91）、prim_reg_we_check（:60-68）——实现存在但声明缺失，违反 SEC_CM 约定
- 建议验证型: grep hjson "sec_cm" + 逐条核对 RTL 锚点

### CAND-ASCON-02
- 疑点: KEY.SEC_WIPE 清除值为全零常量（非 PRD），与 hjson 声称 "cleared with pseudo-random data" 矛盾
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv:163 `assign hw2reg.key_share0[i].d = '0;` 及 :172 `assign hw2reg.key_share1[i].d = '0;`
- lens: L1
- 预言机依据: hjson:133/158 声明 "Upon reset, these registers are cleared with pseudo-random data"；SEC_WIPE 语义要求 prd_clearing_*（全 0 = 洞，OT-002/006 模式）；EDN 断开（ascon.sv:117 `edn_req = 1'b0`）使 PRD 不可用
- 建议验证型: 组合 micro-tb：写 key 后触发 wipe，检查 hw2reg.d 是否为 PRD 而非 0

### CAND-ASCON-03
- 疑点: NONCE.SEC_WIPE 清除值为全零常量（非 PRD），与 hjson 声称 "cleared with pseudo-random data" 矛盾
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv:213 `assign hw2reg.nonce_share0[i].d = '0;` 及 :222 `assign hw2reg.nonce_share1[i].d = '0;`
- lens: L1
- 预言机依据: hjson:184/209 同 CAND-ASCON-02；EDN 断开使 PRD 不可达
- 建议验证型: 同 CAND-ASCON-02

### CAND-ASCON-04
- 疑点: EDN 完全断开——ascon 永不请求熵，PRD/随机掩码不可用
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon.sv:117 `assign edn_req = 1'b0;` 及 :114-116 unused_edn_data/unused_edn_ack
- lens: L1
- 预言机依据: hjson 声明 EDN inter_signal_list（:106-111）；ascon_core.sv:331 `hw2reg.status.wait_edn.d = 1'b0` 恒零——EDN 等待状态硬编码为无等待；SEC_WIPE 需要 PRD 但 EDN 不可达 → SEC_WIPE 不可实现
- 建议验证型: micro-tb：确认 edn_req 恒 0，edn_data 未进入任何数据通路

### CAND-ASCON-05
- 疑点: lc_escalate_en_i 被 unused——生命周期升级不触发 fatal alert
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv:146 `assign unused_lc_escalate_en_i = lc_escalate_en_i;`
- lens: L1
- 预言机依据: hjson:45-53 fatal alert 描述第 v) 条 "escalations triggered by the life cycle controller"；ascon.sv:122 `alert[1] = ascon_fatal_alert | intg_err_alert | shadowed_storage_err` 无 lc_escalate 贡献——hjson 承诺的升级路径完全缺失
- 建议验证型: 组合 micro-tb：拉高 lc_escalate_en_i，观察 alert[1] 是否变化（预期：不变=洞）

---

## L2 hjson-spec-vs-RTL

### CAND-ASCON-06
- 疑点: WIPE 触发被完全丢弃——hjson 声称 "Performs a secure wipe of sensitive data" 但 RTL 无任何清除逻辑
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv:305-309 `assign hw2reg.trigger.wipe.d = 1'b0; assign hw2reg.trigger.wipe.de = 1'b1; logic unused_wipe; assign unused_wipe = wipe;`
- lens: L2
- 预言机依据: hjson:590 TRIGGER.WIPE 描述 "Performs a secure wipe of sensitive data"；ascon_core.sv:305 TODO "Add wipe/reset"；wipe 信号赋给 unused_wipe 然后丢弃——SW 写 TRIGGER.WIPE=1 无任何效果
- 建议验证型: micro-tb：写 TRIGGER.WIPE=1，检查 key/nonce/state 寄存器是否变化（预期：不变=洞）

### CAND-ASCON-07
- 疑点: manual_start_trigger 被 unused——手动触发模式未实现
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv:311-313 `logic unused_manual_start_trigger; assign unused_manual_start_trigger = manual_start_trigger;`
- lens: L2
- 预言机依据: hjson:583-584 TRIGGER.START 描述 "If CTRL_AUX_SHADOWED.manual_start_trigger = 1: Keep Ascon unit paused (0) or trigger... (1)"；ascon_core.sv:311 TODO "Add manual mode for SCA"
- 建议验证型: micro-tb：设 manual_start_trigger=1，写 TRIGGER.START=1，观察 duplex 是否响应

### CAND-ASCON-08
- 疑点: force_data_overwrite 被 unused——输出覆写控制未实现
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv:315-317 `logic unused_force_data_overwrite; assign unused_force_data_overwrite = force_data_overwrite;`
- lens: L2
- 预言机依据: hjson:301-303 MSG_OUT 描述 "If CTRL_AUX_SHADOWED.force_data_overwrite = 0, the Ascon unit is stalled; stalled when the previous output data has not yet been read"；ascon_core.sv:315 TODO "Add output overwrite"
- 建议验证型: micro-tb：设 force_data_overwrite=0，不读 MSG_OUT，观察 duplex 是否停顿（预期：不停顿，因为控制未生效）

### CAND-ASCON-09
- 疑点: STATUS.STALL 恒零——不反映真实停顿状态
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv:329 `assign hw2reg.status.stall.d = 1'b0;`
- lens: L2
- 预言机依据: hjson:609-612 STATUS.STALL 描述 "stalled (1) because there is previous output data that must be read"；ascon_core.sv:328 TODO "STATUS"
- 建议验证型: micro-tb：产生未读输出，检查 STATUS.STALL 是否为 1（预期：0=洞）

### CAND-ASCON-10
- 疑点: STATUS.WAIT_EDN 恒零——不反映 EDN 等待状态
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv:331 `assign hw2reg.status.wait_edn.d = 1'b0;`
- lens: L2
- 预言机依据: hjson:617-618 STATUS.WAIT_EDN 描述 "The Ascon unit is waiting for new entropy"；与 EDN 断开（CAND-ASCON-04）因果链一致
- 建议验证型: 组合验证（依赖 CAND-ASCON-04 修复）

### CAND-ASCON-11
- 疑点: sideload_key 和 keymgr_key_i 被 unused——密钥 sideload 接口完全未连接
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv:133-136 `assign unused_sideload_key = sideload_key; assign unused_keymgr_key_i = keymgr_key_i;`
- lens: L2
- 预言机依据: hjson:421-422 CTRL_SHADOWED.SIDELOAD_KEY 描述 "Controls whether the Ascon unit uses the key provided by the key manager via key sideload interface (1)"；ascon_core.sv:133 TODO "Add sideload interface"
- 建议验证型: micro-tb：设 sideload_key=1，提供 keymgr_key_i，检查 duplex 是否使用 sideload key（预期：仍使用 SW key=洞）

### CAND-ASCON-12
- 疑点: masked_ad_input 和 masked_msg_input 被 unused——掩码输入控制未生效
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv:140-143 `assign unused_masked_ad_input = masked_ad_input; assign unused_masked_msg_input = masked_msg_input;`
- lens: L2
- 预言机依据: hjson:429-433 MASKED_AD_INPUT 描述 "If set to 0, the write operation tracking of Share 1 is disabled"；ascon_core.sv:138 TODO "Add logic to provide inputs unmasked"
- 建议验证型: micro-tb：设 masked_ad_input=0，不写 share1，检查 data_in_valid 是否仍需要两个 share（预期：仍需要=控制未生效）

### CAND-ASCON-13
- 疑点: ERROR 寄存器无法通过 WIPE 清除——hjson 声称 "To clear the error, a wipe must be triggered" 但 WIPE 不可用
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv:305-309（WIPE 被丢弃）+ ascon.hjson:725 ERROR 描述
- lens: L2
- 预言机依据: hjson:725 ERROR 描述 "To clear the error, a wipe must be triggered"；CAND-ASCON-06 证明 WIPE 无功能 → ERROR 寄存器一旦置位永远无法清除（除非 reset）
- 建议验证型: 组合验证（依赖 CAND-ASCON-06）

### CAND-ASCON-14
- 疑点: ascon_operation 在 duplex FSM 中完全未使用——XOF/HASH 模式无差异化处理
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_duplex.sv:23（输入端口声明）但 FSM（:323-601）中无任何引用
- lens: L2
- 预言机依据: hjson:383-385 声明 "XOF...This mode is currently not supported and treated as an invalid input, that is mapped to ASCON_ENC"；prim_ascon_pkg.sv:23-27 duplex_op_e 定义了 ASCON_HASH=3'b100 但 duplex 完全忽略——行为是 "operation 字段被丢弃" 而非 "mapped to ENC"
- 建议验证型: micro-tb：设 operation=ASCON_HASH，提供输入，检查输出是否等于 operation=ASCON_ENC 的结果

---

## L3 树内参考对比

### CAND-ASCON-15
- 疑点: ascon_core.sv 和 prim_ascon_duplex.sv 无任何 SVA 断言——安全合同缺乏形式化约束
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv（全文无 SVA）+ /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_duplex.sv（全文无 SVA）
- lens: L3
- 预言机依据: 同级 IP（aes_cipher_core.sv、kmac_core.sv）有大量 SVA 断言约束数据通路完整性和 FSM 不变量；ascon_reg_top.sv 仅有 4 条 TL-UL 适配器断言（:2642-2647），核心模块 0 条——对安全 IP 异常
- 建议验证型: FPV：补充 SVA 断言覆盖关键不变量（idle → no state change after done; fatal error → FSM in Error; key/nonce loaded before start）

### CAND-ASCON-16
- 疑点: reqParity ASSUME 被注释掉——FPV 约束降级
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_reg_top.sv:2651 `//ASSUME(reqParity, tl_reg_h2d.a_valid |-> tl_reg_h2d.a_user.chk_en == tlul_pkg::CheckDis)`
- lens: L3
- 预言机依据: 同级 IP 的 reg_top 通常保留此 ASSUME；注释掉意味着 FPV 不再约束 TL-UL 请求包的奇偶校验字段，可能引入虚假的 intg_err 触发路径
- 建议验证型: FPV：取消注释后确认无新反例

### CAND-ASCON-17
- 疑点: 密码功能正确性必须通过 DPI 对比 C 参考实现验证，不可仅凭代码审查
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_duplex.sv（完整 AEAD 数据通路）
- lens: L3
- 预言机依据: OT-004 教训："crypto functional correctness must be tool-verified, never eyeballed"；树内存在 vendored C 参考（ascon-c ascon128/ + ascon128a/）和 DPI 桥接（ascon_model_dpi.c）及 pre_dv testbench（prim_ascon_duplex_tb/, prim_ascon_round_tb/）；IV、rcon、shifts、S-box 已通过 Python 脚本逐位验证正确，但完整 AEAD 端到端功能仍需 DPI 验证
- 建议验证型: DPI 差分 tb：用 prim_ascon_duplex_tb 驱动，对比 RTL 输出 vs ascon_model_dpi 输出，覆盖 Ascon-128/128a × Enc/Dec × 全块/部分块/空 AD × 全块/部分块/空 MSG

---

## L4 结构 lint

### CAND-ASCON-18
- 疑点: nonce_error 不阻塞 start_ok——操作可在无有效 nonce 时启动，可能导致 nonce 重用（AEAD 安全性灾难）
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv:478 `assign start_ok = start & ~key_error;`（仅检查 key_error，不含 nonce_error）
- lens: L4
- 预言机依据: ascon_core.sv:470-471 定义 nonce_error = lack_nonce_inputs；hjson:179-180 声明 "Ascon requires the nonce to be unique for each message. However there are no hardware checks to enforce this."——hjson 明确说不强制，但未声明 nonce_error 不阻塞 start；nonce 重用 + 同 key → 完整性破坏（Ascon 安全性保证失效）
- 建议验证型: micro-tb：不写 nonce，触发 START，确认 duplex 启动并使用全零 nonce

### CAND-ASCON-19
- 疑点: valid_bytes > 15 时 bin2thermo 返回全 1（无范围检查）——SW 写入超范围值导致错误 padding
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_pkg.sv:160 `default : valid_bytes_mask = {128{1'b1}};` 及 prim_ascon_duplex.sv:97 TODO "Add check what to do, if data_in_valid_bytes_i is greater than blocksize"
- lens: L4
- 预言机依据: Ascon-128 rate=64bit(8bytes)，Ascon-128a rate=128bit(16bytes)；valid_bytes 为 5-bit（0-31），但合法范围仅 0-16；complete_block 检查仅覆盖 =8(128) 或 =16(128a)，不检查 >blocksize 情况；bin2thermo default 返回全 1 使所有字节标记为"有效"，padding 被完全跳过
- 建议验证型: micro-tb：设 valid_bytes=17，检查 padding 是否正确（预期：padding 被跳过=错误）

### CAND-ASCON-20
- 疑点: data_type_start/data_type_last 12-bit 值直接比较 enum 常量——非有效 MuBi4 编码可能误匹配
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv:501-504 `data_type_start == AD_IN` 等比较
- lens: L4
- 预言机依据: ascon_pkg.sv:9-14 定义 data_type_in_e 使用 3×MuBi4=12bit 编码（MSG_IN/AD_IN/TAG_IN/NONE_IN）；SW 写入 BLOCK_CTRL_SHADOWED.data_type_start/last 为 12-bit 值，但无 MuBi4 有效性检查；若 SW 写入非标准编码（如 {MuBi4True, MuBi4True, MuBi4False}），比较可能误匹配或完全不匹配，导致 undefined 行为
- 建议验证型: micro-tb：写入非标准 data_type 值，观察 duplex 行为

### CAND-ASCON-21
- 疑点: data_out_ready_i 在 duplex 中被 unused——输出反压逻辑缺失
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_duplex.sv:60-61 `logic unused_data_out_ready_i; assign unused_data_out_ready_i = data_out_ready_i;`
- lens: L4
- 预言机依据: prim_ascon_duplex.sv:13 TODO "Add backpressure logic"；data_out_ready_i 来自 ascon_core.sv:656 msg_out_ready——当输出寄存器未读时 msg_out_ready=0，但 duplex 内部不检查此信号，可能在接收方未就绪时覆写输出
- 建议验证型: 时序 tb：连续两次 duplex 操作不读中间输出，检查第二次输出是否覆写第一次

### CAND-ASCON-22
- 疑点: TRIGGER.START 硬编码 d=0/de=1——START 触发无反馈，SW 无法读到自身写入的触发值
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv:301-303 `assign hw2reg.trigger.start.d = 1'b0; assign hw2reg.trigger.start.de = 1'b1;`
- lens: L4
- 预言机依据: ascon_core.sv:301 TODO "Trigger feedback"；SW 写 TRIGGER.START=1 后立即回读将得到 0 而非 1——违反 "each bit is individually cleared to zero when executing the corresponding trigger" 的 hjson 描述（:571-572）；同类 IP（AES）的 trigger 寄存器通常提供 hwext 反馈
- 建议验证型: micro-tb：写 TRIGGER.START=1 后立即读回，检查是否为 0（预期：0=反馈缺失）

---

## L5 常量折叠

### CAND-ASCON-23
- 疑点: IV_128 = 0x80400c0600000000，IV_128A = 0x80800c0800000000——已通过 Python 脚本对比 C 参考验证正确
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_pkg.sv:36-37
- lens: L5
- 预言机依据: C 参考构建公式：ASCON_128_IV = (k*8<<56)|(r*8<<48)|(pa<<40)|(pb<<32) = (128<<56)|(64<<48)|(12<<40)|(6<<32) = 0x80400c0600000000；ASCON_128A_IV = (128<<56)|(128<<48)|(12<<40)|(8<<32) = 0x80800c0800000000；Python 脚本 bit-exact 比对通过
- 建议验证型: 已脚本验证 ✓

### CAND-ASCON-24
- 疑点: Round constants (f0,e1,d2,c3,b4,a5,96,87,78,69,5a,4b) 及 P6/P8 偏移——已通过 Python 脚本对比 C 参考验证正确
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_pkg.sv:42-61
- lens: L5
- 预言机依据: C 参考 permutations.h P12/P8/P6 序列与 RTL get_ascon_rcon() + perm_offset_e (P12=0, P8=4, P6=6) 完全匹配；Python 脚本逐值比对通过
- 建议验证型: 已脚本验证 ✓

### CAND-ASCON-25
- 疑点: Linear layer 移移量 (19/28, 61/39, 1/6, 10/17, 7/41)——已通过 Python 脚本验证正确
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_round.sv:60-64
- lens: L5
- 预言机依据: C 参考 round.h 使用相同 ROR 移位量；Python 脚本确认 RTL {x[18:0],x[63:19]} 等价于 ROR(x,19) 等
- 建议验证型: 已脚本验证 ✓

### CAND-ASCON-26
- 疑点: S-box 代数实现——已通过 Python 脚本穷举 32 种输入对比 C 参考验证正确
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_sbox.sv:12-33
- lens: L5
- 预言机依据: Python 脚本实现 RTL 三层分解（affine1→chi→affine2）和 C 参考的同一公式，32 种输入全部 bit-exact 匹配
- 建议验证型: 已脚本验证 ✓

### CAND-ASCON-27
- 疑点: Sparse FSM 编码 min Hamming distance=3, 18 编码无重复——已通过 Python 脚本验证
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_pkg.sv:96-139
- lens: L5
- 预言机依据: 编码生成注释声明 -d 3 -m 18 -n 10 -s 3538518573；Python 脚本穷举所有 C(18,2)=153 对，确认 min_hd=3，无重复编码
- 建议验证型: 已脚本验证 ✓

---

## L6 SCA 结构

### CAND-ASCON-28
- 疑点: data_out_o 直接输出无盲化——操作数依赖的功耗泄漏
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_duplex.sv:162 `assign data_out_o = data_out;` + :161 TODO "add blinding"
- lens: L6
- 预言机依据: prim_ascon_duplex.sv:11-12 TODO "Add countermeasures: ... blinding for output signals"；data_out = (data_in_i ^ {ascon_state_q[0], ascon_state_q[1]}) & valid_bytes_bit_mask——明文/密文直接从 state XOR 得出，无随机掩码；doc/theory_of_operation.md 声明 "unhardened 320-bit 1 round/cycle"
- 建议验证型: 时序 tb：对比有/无 blinding 的功耗轨迹差分（DPA 测试向量）

### CAND-ASCON-29
- 疑点: tag_out_o 直接输出无盲化——tag 计算结果泄漏
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_duplex.sv:163 `assign tag_out_o = ({ascon_state_q[3], ascon_state_q[4]} ^ key_i);`
- lens: L6
- 预言机依据: tag = state_word3:4 ^ key——key 参与 XOR 但无掩码保护，侧信道可恢复 key；同 CAND-ASCON-28 的 TODO 声明
- 建议验证型: 时序 tb：DPA 攻击模拟，检查 tag 输出对 key 的相关性

### CAND-ASCON-30
- 疑点: sel_round_input 默认 BLINDING(=0) 但从不使用真实随机值——状态输入无随机化
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_duplex.sv:350 `sel_round_input = BLINDING;` 及 :229-232 `BLINDING: state_to_round = '0;`
- lens: L6
- 预言机依据: prim_ascon_duplex.sv:11 TODO "Add countermeasures: ... random values for state_to_round input"；BLINDING 路径将 state_to_round 设为全零而非 PRD——实际效果是"零盲化"=无盲化；EDN 断开（CAND-ASCON-04）使 PRD 不可达
- 建议验证型: 时序 tb：检查 BLINDING 状态下 state_to_round 是否为非零随机值（预期：全零=洞）

### CAND-ASCON-31
- 疑点: S-box 无掩码保护——unprotected 实现
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_sbox.sv:7-33（纯组合逻辑，无 mask/share）
- lens: L6
- 预言机依据: prim_ascon_duplex.sv:11 TODO 声明需添加 "mubi for control signals, random values for state_to_round input, blinding for output signals"；doc/theory_of_operation.md 声明 "unhardened"；同级 IP（AES）使用 masked S-box
- 建议验证型: 时序 tb：SCA 差分测试（对比 AES masked S-box 方法论）

### CAND-ASCON-32
- 疑点: 无 PRNG/LFSR 用于状态/输出掩码——整个数据通路无随机性源
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_duplex.sv（全文无 PRNG/LFSR 实例化）+ /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon.sv:117 edn_req=0
- lens: L6
- 预言机依据: EDN 断开（CAND-ASCON-04）+ 无内部 PRNG = 整个 Ascon IP 无任何随机性源；所有 SCA 对策（SEC_WIPE 用 PRD、blinding、masked S-box、state randomization）均依赖随机性 → 全部不可实现
- 建议验证型: 组合验证（CAND-ASCON-04 + L6 各条目）

---

## 附：Python 常量验证脚本摘要

以下验证均通过独立 Python 脚本执行（非心算）：

| 验证项 | 方法 | 结果 |
|--------|------|------|
| IV_128 | C 参考公式构建 vs RTL localparam | ✅ bit-exact 匹配 |
| IV_128A | C 参考公式构建 vs RTL localparam | ✅ bit-exact 匹配 |
| Round constants ×12 | 逐值比对 C 参考 permutations.h | ✅ 全部匹配 |
| P6/P8 offset | RTL perm_offset_e vs C P6/P8 起始 rcon | ✅ P8 从 round4 起，P6 从 round6 起 |
| Linear layer shifts ×5 | RTL 移位量 vs C ROR 宏参数 | ✅ (19,28)(61,39)(1,6)(10,17)(7,41) |
| S-box ×32 inputs | RTL 三层分解 vs C 参考公式穷举 | ✅ 全部 bit-exact 匹配 |
| Sparse FSM HD | C(18,2)=153 对 Hamming 距离 | ✅ min_hd=3，无重复编码 |
