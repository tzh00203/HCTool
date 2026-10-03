# ascon 盲预言机目录

## 元信息
- 树: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
- 扫描范围: hw/ip/ascon/{rtl,data,doc} + hw/ip/prim/rtl/prim_ascon_* + hw/ip/prim/dv/prim_ascon/
- SEC_CM 声明数: 0 / SVA 数: 3 / testplan 条目数: 0

## 一、SEC_CM 声明 ↔ RTL 锚点

**注意：ascon.hjson 无 `sec_cm:` 字段——此 IP 的 hjson 未声明任何 SEC_CM 条目。**
这与同级 IP（aes/hmac/kmac 等）均有 sec_cm 声明的惯例不一致，本身即预言机：
hjson 未声明但 RTL 中存在安全对策实现（sparse FSM、prim_count、shadowed regs），
反之亦可能有 hjson 未来补声明但 RTL 未实现。

| # | SEC_CM 声明 (hjson:line) | RTL 锚点 (file:line) | 检验要点 |
|---|---|---|---|
| 1 | （hjson 无 sec_cm 字段——隐式缺失声明） | prim_ascon_duplex.sv:603 `PRIM_FLOP_SPARSE_FSM` | sparse FSM 实现存在但未在 hjson 声明；检查 `err_o` 路径：sparse_fsm_error → err_o → duplex_fatal_error → alert_fatal_o |
| 2 | （隐式缺失） | prim_ascon_duplex.sv:172-187 `prim_count` u_round_counter | 计数器防篡改存在但未声明；检查 `round_count_error` → `err_o` 传播链 |
| 3 | （隐式缺失） | ascon_reg_top.sv:1128-1377 `prim_subreg_shadow` (CTRL_SHADOWED, CTRL_AUX_SHADOWED, BLOCK_CTRL_SHADOWED) | 影子寄存器实现存在；检查 `shadowed_storage_err_o` 和 `shadowed_update_err_o` → alert 传播 |
| 4 | （隐式缺失） | ascon_reg_top.sv:52-56 `tlul_cmd_intg_chk` + ascon_reg_top.sv:85-91 `tlul_rsp_intg_gen` | TL-UL 完整性检查存在；检查 `intg_err` → `intg_err_o` → alert_fatal |
| 5 | （隐式缺失） | ascon_reg_top.sv:60-68 `prim_reg_we_check` | 寄存器写使能独热检查存在；检查 `reg_we_err` → `intg_err_o` → alert_fatal |
| 6 | （隐式缺失） | ascon.sv:133-147 `prim_alert_sender` ×2 | 告警发送器实例化；检查 IsFatal 参数：索引 1=fatal, 索引 0=recov |
| 7 | KEY.SEC_WIPE（hjson desc 文本暗示：line 133 "Upon reset, these registers are cleared with pseudo-random data"） | 缺失! ascon_core.sv:163 `assign hw2reg.key_share0[i].d = '0` | key share0 的 hw2reg.d 固定写 0（非 PRD），与 hjson 声称的"pseudo-random data"矛盾；应来自 prd_clearing 或 edn_data |
| 8 | KEY.SEC_WIPE（同上，line 158 "Upon reset, these registers are cleared with pseudo-random data"） | 缺失! ascon_core.sv:172 `assign hw2reg.key_share1[i].d = '0` | key share1 同理，hw2reg.d = 0 非 PRD |
| 9 | NONCE.SEC_WIPE（hjson line 184 "Upon reset, these registers are cleared with pseudo-random data"） | 缺失! ascon_core.sv:213 `assign hw2reg.nonce_share0[i].d = '0` | nonce share0 hw2reg.d = 0 非 PRD |
| 10 | NONCE.SEC_WIPE（同上） | 缺失! ascon_core.sv:222 `assign hw2reg.nonce_share1[i].d = '0` | nonce share1 hw2reg.d = 0 非 PRD |

## 二、行为性描述句（hjson 原文 → 检验点）

| # | hjson 原文 (file:line) | 检验点 |
|---|---|---|
| 1 | "This fatal alert is triggered upon detecting a fatal fault inside the Ascon unit. Examples include i) storage errors in the shadowed Control Register, ii) any internal FSM entering an invalid state, iii) any sparsely encoded signal taking on an invalid value, iv) errors in the internal round counter, v) escalations triggered by the life cycle controller, and vi) fatal integrity failures on the TL-UL bus. The Ascon unit cannot recover from such an error and needs to be reset." (ascon.hjson:45-53) | (i) shadowed_storage_err → alert[1] (ascon.sv:122); (ii) sparse_fsm_error → err_o → duplex_fatal_error → alert_fatal_o → alert[1] (prim_ascon_duplex.sv:594,612, ascon_core.sv:125, ascon.sv:122); (iii) mubi4_test_invalid → mubi_error → err_o (prim_ascon_duplex.sv:606-612); (iv) round_count_error → err_o (prim_ascon_duplex.sv:186,612); (v) **缺失!** lc_escalate_en_i 被 unused 掉（ascon_core.sv:146 `assign unused_lc_escalate_en_i = lc_escalate_en_i`），升级输入未生效；(vi) intg_err → alert[1] (ascon_reg_top.sv:52,81, ascon.sv:122) |
| 2 | "Performs a secure wipe of sensitive data." (ascon.hjson:590, TRIGGER.WIPE 字段描述) | **缺失!** ascon_core.sv:305-309：`wipe` 信号被赋给 `unused_wipe`，`hw2reg.trigger.wipe.d = 1'b0; hw2reg.trigger.wipe.de = 1'b1;`——WIPE 触发被丢弃，无实际清除逻辑 |
| 3 | "Upon reset, these registers are cleared with pseudo-random data." (ascon.hjson:133, KEY_SHARE0) | **矛盾!** ascon_core.sv:163 `hw2reg.key_share0[i].d = '0`——清除值为全零常量，非伪随机数据；ascon.sv:117 `edn_req = 1'b0`（EDN 请求被禁用），edn_data 被 unused |
| 4 | "Upon reset, these registers are cleared with pseudo-random data." (ascon.hjson:158, KEY_SHARE1) | **矛盾!** ascon_core.sv:172 `hw2reg.key_share1[i].d = '0`——同 #3 |
| 5 | "Upon reset, these registers are cleared with pseudo-random data." (ascon.hjson:184, NONCE_SHARE0) | **矛盾!** ascon_core.sv:213 `hw2reg.nonce_share0[i].d = '0`——同 #3 |
| 6 | "Upon reset, these registers are cleared with pseudo-random data." (ascon.hjson:209, NONCE_SHARE1) | **矛盾!** ascon_core.sv:222 `hw2reg.nonce_share1[i].d = '0`——同 #3 |
| 7 | "If CTRL_AUX_SHADOWED.manual_start_trigger = 1: Keep Ascon unit paused (0) or trigger the authenticated encryption/decryption of one data block (1)." (ascon.hjson:583-584, TRIGGER.START) | **缺失!** ascon_core.sv:311-313：`manual_start_trigger` 被赋给 `unused_manual_start_trigger`，手动触发模式未实现 |
| 8 | "If CTRL_AUX_SHADOWED.force_data_overwrite = 0, the Ascon unit is stalled when the previous output data has not yet been read and is about to be overwritten." (ascon.hjson:301-303) | **缺失!** ascon_core.sv:315-317：`force_data_overwrite` 被赋给 `unused_force_data_overwrite`，输出覆写控制未实现 |
| 9 | "The Ascon unit is waiting for new entropy." (ascon.hjson:617-618, STATUS.WAIT_EDN) | **缺失!** ascon_core.sv:331：`hw2reg.status.wait_edn.d = 1'b0` 恒零——EDN 等待状态硬编码为无等待 |
| 10 | "The Ascon unit is not stalled (0) or stalled (1) because there is previous output data that must be read" (ascon.hjson:609-612, STATUS.STALL) | **缺失!** ascon_core.sv:329：`hw2reg.status.stall.d = 1'b0` 恒零——STALL 状态硬编码为无停顿 |
| 11 | "Controls whether the Ascon unit uses the key provided by the key manager via key sideload interface (1)" (ascon.hjson:421-422, CTRL_SHADOWED.SIDELOAD_KEY) | **缺失!** ascon_core.sv:133-136：`sideload_key` 赋给 `unused_sideload_key`，`keymgr_key_i` 赋给 `unused_keymgr_key_i`——sideload 接口未连接 |
| 12 | "If set to 0, the write operation tracking of Share 1 is disabled." (ascon.hjson:429-433, MASKED_AD_INPUT) | **缺失!** ascon_core.sv:140-143：`masked_ad_input` 和 `masked_msg_input` 赋给 unused 变量——掩码输入控制未生效 |
| 13 | "An error due to a misconfiguration has happened. The user should read out the error register for more information" (ascon.hjson:622-624, STATUS.ASCON_ERROR) | ascon_core.sv:526：`ascon_error = key_error | nonce_error | flag_error | order_error`；检查四个错误源的 OR 是否完整 |
| 14 | "To clear the error, a wipe must be triggered." (ascon.hjson:725, ERROR register desc) | **矛盾!** WIPE 触发未实现（见 #2），ERROR 寄存器无法通过 WIPE 清除 |
| 15 | "A recoverable alert is triggered upon detecting an update error in the shadowed Control Register. The Ascon unit can be recovered from such a condition by restarting the Ascon operation." (ascon.hjson:37-40) | ascon.sv:123：`alert[0] = ascon_recov_alert | shadowed_update_err`；ascon_core.sv:294：`alert_recov_o = no_ad_mubi4invalid | no_msg_mubi4invalid`——recoverable alert 两个来源：mubi4 无效 + shadowed update error |
| 16 | "XOF...This mode is currently not supported and treated as an invalid input, that is mapped to ASCON_ENC." (ascon.hjson:383-385) | ascon_core.sv:255 `operation = reg2hw.ctrl_shadowed.operation.q`；传入 prim_ascon_duplex 后由 duplex_op_e 枚举处理——需检查 ASCON_HASH(3'b100) 值在 duplex FSM 中是否被映射到 ENC 行为或进入 Error |

## 三、SVA 清单（行为合同）

| # | 断言 (file:line) | 内容摘要 | 约束的预期行为 |
|---|---|---|---|
| 1 | ascon_reg_top.sv:2642 `ASSERT_PULSE(wePulse, reg_we, ...)` | 寄存器写使能必须是单周期脉冲 | 防止寄存器被持续写入；违反意味着寄存器接口时序异常 |
| 2 | ascon_reg_top.sv:2643 `ASSERT_PULSE(rePulse, reg_re, ...)` | 寄存器读使能必须是单周期脉冲 | 防止寄存器被持续读出；违反意味着读接口时序异常 |
| 3 | ascon_reg_top.sv:2645 `ASSERT(reAfterRv, $rose(reg_re \|\| reg_we) \|=> tl_o_pre.d_valid, ...)` | 读/写请求上升沿下一周期必须返回有效数据 | TL-UL 适配器响应时序合同；违反意味着总线响应丢失 |
| 4 | ascon_reg_top.sv:2647 `ASSERT(en2addrHit, (reg_we \|\| reg_re) \|-> $onehot0(addr_hit), ...)` | 读写使能有效时地址命中必须 one-hot0 | 防止地址解码冲突；违反意味着两个寄存器同时被选中 |
| 5 | ascon_reg_top.sv:2651 `//ASSUME(reqParity, ...)` **被注释** | TL-UL 请求奇偶校验假设 | 原本约束 TL-UL 请求包的奇偶字段；注释掉意味着 FPV 不再约束此条件 |

**注意：ascon RTL（ascon.sv, ascon_core.sv）和 prim_ascon_duplex.sv 中无任何 SVA 断言。**
这对安全 IP 来说异常——AES/KMAC 等同类 IP 的核心模块有大量 SVA。

## 四、树内参考

| # | 参考物 (绝对路径) | 类型（兄弟模块/参考实现/规范注释） | 可对比什么 |
|---|---|---|---|
| 1 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/dv/prim_ascon/ascon_model_dpi/vendor/ascon_ascon-c/ascon128/ | 参考实现（vendored ascon-c C 代码，ascon-128 变体） | RTL 的 ASCON_128 路径输出 vs C 参考的 AEAD 结果；round 常量、IV、S-box、线性层正确性 |
| 2 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/dv/prim_ascon/ascon_model_dpi/vendor/ascon_ascon-c/ascon128a/ | 参考实现（vendored ascon-c C 代码，ascon-128a 变体） | RTL 的 ASCON_128A 路径输出 vs C 参考的 AEAD 结果；特别注意 128a 的 128-bit rate、P8 round 差异 |
| 3 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/dv/prim_ascon/ascon_model_dpi/ascon_model_dpi.c | 参考实现（DPI 桥接 C 模型，190 行） | 通过 Verilator/VCS DPI 调用对比 RTL 与 C 模型 |
| 4 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/pre_dv/prim_ascon/prim_ascon_duplex_tb/ | 参考实现（pre_dv 单元级 testbench） | duplex 模块的端到端功能验证；含 Verilator C++ 驱动 |
| 5 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/pre_dv/prim_ascon/prim_ascon_round_tb/ | 参考实现（pre_dv round 函数 testbench） | round 函数（ARK + S-box + 线性层）端到端正确性；含 Verilator C++ 驱动 |
| 6 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/doc/theory_of_operation.md | 规范注释（设计文档） | FSM 状态流描述 vs RTL 实现；padding 策略（10* / 10+）；domain separation 逻辑；"unhardened 320-bit 1 round/cycle" 声明 |
| 7 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_round.sv | 兄弟模块（round 函数） | round 常量表 prim_ascon_pkg::get_ascon_rcon vs Ascon 规范；线性层移位量 (19/28, 61/39, 1/6, 10/17, 7/41) vs 规范 |
| 8 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_ascon_sbox.sv | 兄弟模块（S-box） | S-box 代数实现 vs 规范的 5-bit permutation；可直接穷举 32 种输入验证 |

## 五、特殊结构提示

### 5.1 TODO 标记清单（未实现功能 = 潜在预言机缺口）

| file:line | TODO 内容 | 安全影响 |
|---|---|---|
| ascon_core.sv:133 | "Add sideload interface" | sideload_key 和 keymgr_key_i 被 unused——密钥 sideload 路径完全未连接 |
| ascon_core.sv:138 | "Add logic to provide inputs unmasked" | masked_ad_input / masked_msg_input 被 unused——掩码控制未生效 |
| ascon_core.sv:145 | "Add escalation Input" | lc_escalate_en_i 被 unused——生命周期升级不触发 fatal alert |
| ascon_core.sv:275 | "This should be added to the register_top/reggen-tool" | mubi4 sanitize 应在 reg_top 而非 ascon_core——当前实现允许无效 mubi4 值短暂存在 |
| ascon_core.sv:301 | "Trigger feedback" | hw2reg.trigger.start 硬编码 d=0/de=1——START 触发无反馈 |
| ascon_core.sv:305 | "Add wipe/reset" | WIPE 触发被丢弃——**关键安全缺口**：敏感数据无法被清除 |
| ascon_core.sv:311 | "Add manual mode for SCA" | manual_start_trigger 被 unused——手动模式未实现 |
| ascon_core.sv:315 | "Add output overwrite" | force_data_overwrite 被 unused——输出覆写控制未实现 |
| ascon_core.sv:328 | "STATUS" | stall/wait_edn 硬编码为 0——状态寄存器不反映真实停顿/等待 |
| ascon.sv:113 | "TODO" (no description) | edn_req = 1'b0, edn_data unused——**EDN 请求被禁用**，熵源未连接 |
| prim_ascon_duplex.sv:11 | "Add countermeasures: mubi for control signals, random values for state_to_round input, blinding for output signals" | SCA 对策未实现——设计文档承认"unhardened" |
| prim_ascon_duplex.sv:13 | "Add backpressure logic" | data_out_ready_i 被 unused——输出反压未实现 |
| prim_ascon_duplex.sv:14 | "Add check for data_in_valid_bytes_i > blocksize" | 无 valid_bytes 范围检查——越界 valid_bytes 可能导致 padding 错误 |
| prim_ascon_duplex.sv:161 | "add blinding" | data_out_o 直接输出无盲化——SCA 泄漏 |

### 5.2 关键数据流与极性

- **alert[1] (fatal)**: `ascon_fatal_alert | intg_err_alert | shadowed_storage_err` (ascon.sv:122)
  - ascon_fatal_alert ← duplex_fatal_error (ascon_core.sv:125)
  - duplex_fatal_error ← err_o ← round_count_error | sparse_fsm_error | mubi_error (prim_ascon_duplex.sv:612)
- **alert[0] (recov)**: `ascon_recov_alert | shadowed_update_err` (ascon.sv:123)
  - ascon_recov_alert ← no_ad_mubi4invalid | no_msg_mubi4invalid (ascon_core.sv:294)
- **start_ok gate**: `start_ok = start & ~key_error` (ascon_core.sv:478)——nonce_error 不阻塞 start，仅设 error 标志

### 5.3 EDN 完全断开

- `edn_req = 1'b0` (ascon.sv:117)——IP 永不请求熵
- `edn_data` 通过 prim_sync_reqack_data 同步但被 `unused_edn_data` 消耗 (ascon.sv:114,116)
- `unused_edn_fips` 消耗 edn_i.edn_fips (ascon.sv:111)
- **后果**：SEC_WIPE 无法使用 PRD；状态初始化无法注入随机掩码

### 5.4 Sparse FSM 编码

- prim_ascon_pkg.sv:96-139 定义 duplex_fsm_state_e，18 状态，10-bit 编码，最小 Hamming 距离 = 3
- `PRIM_FLOP_SPARSE_FSM` 实例化 (prim_ascon_duplex.sv:603)
- 非法编码 → Error 状态 → sparse_fsm_error → err_o → fatal alert
- **检验**：RTL 中 `unique case (fsm_state_q)` 覆盖全部 18 个枚举值 + default → Error；确认无遗漏

### 5.5 prim_count 保护

- u_round_counter: 4-bit 计数器 (prim_ascon_duplex.sv:172-187)
- set_i/incr_en_i 受 FSM 控制；clr_i 恒 0
- err_o(round_count_error) → duplex fatal alert
- **检验**：计数器 set 值来自 perm_offset（P12/P8/P6），检查与 ascon_variant 的对应关系

### 5.6 Shadowed 寄存器结构

- CTRL_SHADOWED: 7 个子字段全 shadowed (ascon_reg_top.sv:1128-1377)
- CTRL_AUX_SHADOWED: 2 个子字段 shadowed，受 CTRL_AUX_REGWEN 门控 (ascon_reg_top.sv:1380-1454)
- BLOCK_CTRL_SHADOWED: 3 个子字段 shadowed (ascon_reg_top.sv:1485-1592)
- 错误汇总：shadowed_storage_err_o = OR(12 storage_err), shadowed_update_err_o = OR(12 update_err) (ascon_reg_top.sv:2600-2627)

### 5.7 bin2thermo / get_padding_mask 函数

- prim_ascon_pkg.sv:141-189：5-bit valid_bytes → 128-bit 掩码
- valid_bytes > 15（即 5'b1xxxx）时 bin2thermo 返回全 1，get_padding_mask 返回全 0
- **风险**：valid_bytes = 0 → bin2thermo 返回全 0（无有效字节）+ get_padding_mask 返回 0x80 在 byte[0]——空块的 padding 逻辑
