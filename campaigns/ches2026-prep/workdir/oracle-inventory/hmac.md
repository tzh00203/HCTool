# hmac 盲预言机目录

## 元信息
- 树: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
- 扫描范围: hw/ip/hmac/{rtl,data,doc} + hw/ip/prim/rtl/prim_sha2*.sv（SHA-2 引擎原语）
- SEC_CM 声明数: 1 / SVA 数: 16 / testplan 条目数: 14

## 一、SEC_CM 声明 ↔ RTL 锚点
| # | SEC_CM 声明 (hjson:line) | RTL 锚点 (file:line) | 检验要点 |
|---|---|---|---|
| 1 | BUS.INTEGRITY (hmac.hjson:167) | hmac.sv:777 // SEC_CM: BUS.INTEGRITY | intg_err_o 输出接 alert[0]，prim_alert_sender IsFatal=1；reg_top 中 reg_error = addrmiss \| wr_err \| intg_err 驱动 alerts[0] |

## 二、行为性描述句（hjson 原文 → 检验点）
| # | hjson 原文 (file:line) | 检验点 |
|---|---|---|
| 1 | "Wipe of internal state and secret key with constant value provided by software." (hmac.hjson:163, feature HMAC.SECURE_WIPE) | WIPE_SECRET 写入后：secret_key=={32{wipe_v}}（hmac.sv:216-217）、SHA-2 内部 w_q/hash_q/digest_q 全部被 {N{wipe_v}} 覆写（prim_sha2.sv:93-94,124-125,147-148 多模; 201,227,245 SHA256模）、digest CSR 亦须被覆写（hmac.sv:267-283 分 digest_size_started_q 三路）|
| 2 | "The clear secret operation overwrites the internal variables with the provided 32-bit value." (hmac.hjson:427, WIPE_SECRET 寄存器描述) | 同上；且对于 SHA-2 384/512 的 64-bit 字，32-bit wipe_v 被复制拼接为 64-bit {wipe_v,wipe_v}（hmac.sv:217 secret_key_d={32{wipe_v}} 即 1024-bit 全覆写）|
| 3 | "It is recommended to use a value extracted from an entropy source." (hmac.hjson:429) | 非硬性约束，但 WIPE_SECRET 的 wipe_v 来自 SW 写入，不是硬件 PRD；若 wipe_v 为常数则 wipe 无安全意义 |
| 4 | "If the engine computes the hash, it discards any attempts to update the secret keys and report an error." (hmac.hjson:450, KEY multireg 描述) | cfg_block==1 时 key 写入被挡（hmac.sv:218 !cfg_block 门控）；同时 update_seckey_inprocess 触发 err_code=SwUpdateSecretKeyInProcess（hmac.sv:826-836,867-869）|
| 5 | "The registers are allowed to be updated only when the engine is in Idle state." (hmac.hjson:449, KEY 寄存器) | hmac.sv:218: `!cfg_block` 门控 key 更新；cfg_block 在 hash_start_or_continue 时置 1（hmac.sv:369），在 reg_hash_done\|\|reg_hash_stop 时清 0（hmac.sv:371）|
| 6 | "The digest gets cleared when CFG.sha_en transitions from 1 to 0." (hmac.hjson:476, DIGEST 描述) | 在 prim_sha2.sv 中 sha_en_i==0 触发 digest_d 从 digest_we_i/digest_i 加载（prim_sha2.sv:161-163）；hmac.sv 中 digest 传递路径需确认 sha_en→0 时确实清除 |
| 7 | "When STATUS.hmac_idle is 1, these registers may be written to by software." (hmac.hjson:476, DIGEST 可写条件) | digest_sw_we 在 hmac.sv:254,263 由 reg2hw.digest[i].qe 驱动，无 idle 门控——需检查是否有隐式保护（digest_we_i 进入 prim_sha2 后仅在 !sha_en_i 时生效：prim_sha2.sv:161-163）|
| 8 | "With this value, when HMAC/SHA-2 is triggered to start … it will be blocked from starting and an error is signalled to the SW." (hmac.hjson:274, SHA2_None digest_size) | hmac.sv:360-362: hash_start/hash_continue/hash_process 均 &~invalid_config；invalid_config 含 (digest_size==SHA2_None)（hmac.sv:818）；invalid_config_atstart 驱动 err_valid（hmac.sv:844）|
| 9 | "If only unkeyed SHA-2 is configured (hmac_en == 0), starting is not blocked" (hmac.hjson:332, Key_None for SHA-only) | invalid_config = (key_length==Key_None) && hmac_en（hmac.sv:819），所以 hmac_en==0 时 Key_None 不触发 invalid_config |
| 10 | "key_length = 1024-bit for digest_size = SHA2_256 (max 512-bit is supported for SHA-2 256)" → blocked (hmac.hjson:293, key_length 描述) | hmac.sv:820: (key_length==Key_1024) && (digest_size==SHA2_256) && hmac_en 触发 invalid_config |
| 11 | "This fatal alert is triggered when a fatal TL-UL bus integrity fault is detected." (hmac.hjson:73, fatal_fault alert) | hmac.sv:777-778: alerts[0] 接 reg_top intg_err_o；hmac.sv:787-788: AlertIsFatal={1'b1}，prim_alert_sender 永不解除断言 |

## 三、SVA 清单（行为合同）
| # | 断言 (file:line) | 内容摘要 | 约束的预期行为 |
|---|---|---|---|
| 1 | hmac_core.sv:498: `ASSERT(ValidSelRdata_A, …) | hmac_en→sel_rdata in {SelIPad,SelOPad,SelFifo} | HMAC 模式下数据选择合法 |
| 2 | hmac_core.sv:499: `ASSERT(ValidDigestSize_A, …) | hmac_en && sel_msglen==SelOPadMsg → digest_size_i in {SHA2_256,SHA2_384,SHA2_512} | 外层轮消息长度计算时摘要大小必须合法 |
| 3 | hmac.sv:918: assert property wmask_bytealign_p | msg_fifo_req & msg_fifo_we → wmask 字节对齐 | TL-UL 写掩码字节对齐 |
| 4 | hmac.sv:938: `ASSERT(ValidWriteAssert, …) | msg_fifo_req → !in_process | hash_process 后不再写消息 |
| 5 | hmac.sv:943: `ASSERT(ValidHashProcessAssert, …) | (hash_process\|\|reg_hash_stop) → initiated | process/stop 必须在 start/continue 之后 |
| 6 | hmac.sv:946: `ASSERT(ValidHmacEnConditionAssert, …) | hmac_en 变化 → !in_process && !initiated | hmac_en 只能在空闲时修改 |
| 7 | hmac.sv:951: `ASSERT(WipeSecretKeyAssert, …) | wipe_secret → next cycle secret_key=={32{past(wipe_v)}} | WIPE_SECRET 寄存器写入后密钥被覆写 |
| 8 | hmac.sv:955: `ASSERT_KNOWN(IntrHmacDoneOKnown, …) | intr_hmac_done_o 值已知 | 中断输出非 X |
| 9 | hmac.sv:956: `ASSERT_KNOWN(IntrFifoEmptyOKnown, …) | intr_fifo_empty_o 值已知 | 中断输出非 X |
| 10 | hmac.sv:957: `ASSERT_KNOWN(TlODValidKnown, …) | tl_o.d_valid 值已知 | TL 响应有效信号非 X |
| 11 | hmac.sv:958: `ASSERT_KNOWN(TlOAReadyKnown, …) | tl_o.a_ready 值已知 | TL 就绪信号非 X |
| 12 | hmac.sv:959: `ASSERT_KNOWN(AlertKnownO_A, …) | alert_tx_o 值已知 | 告警输出非 X |
| 13 | hmac.sv:965: `ASSERT_PRIM_REG_WE_ONEHOT_ERROR_TRIGGER_ALERT(RegWeOnehotCheck_A, …) | reg_we onehot 错误触发 alert[0] | 寄存器写使能 one-hot 检查 |
| 14 | hmac_reg_top.sv:2645: `ASSERT_PULSE(wePulse, …) | reg_we 为单周期脉冲 | 写使能脉冲检查 |
| 15 | hmac_reg_top.sv:2646: `ASSERT_PULSE(rePulse, …) | reg_re 为单周期脉冲 | 读使能脉冲检查 |
| 16 | hmac_reg_top.sv:2648: `ASSERT(reAfterRv, …) | reg_re/reg_we 上升沿后下一周期 d_valid | 寄存器读写时序 |
| 17 | hmac_reg_top.sv:2650: `ASSERT(en2addrHit, …) | reg_we\|\|reg_re → $onehot0(addr_hit) | 地址译码 one-hot |
| 18 | prim_sha2.sv:183: `ASSERT(WipeHashAssert, …) 多模 | wipe_secret_i → hash_q=={N{past(wipe_v_i)}} | SHA-2 多模哈希寄存器被擦除 |
| 19 | prim_sha2.sv:185: `ASSERT(WipeMsgSchArrAssert, …) 多模 | wipe_secret_i → w_q=={N{past(wipe_v_i)}} | SHA-2 多模消息调度数组被擦除 |
| 20 | prim_sha2.sv:187: `ASSERT(WipeDigestAssert, …) 多模 | wipe_secret_i → digest_q=={N{past(wipe_v_i)}} | SHA-2 多模摘要寄存器被擦除 |
| 21 | prim_sha2.sv:278: `ASSERT(WipeHashAssert, …) SHA256模 | 同 #18，SHA-256 专用 | SHA-2 256 哈希寄存器被擦除 |
| 22 | prim_sha2.sv:280: `ASSERT(WipeMsgSchArrAssert, …) SHA256模 | 同 #19，SHA-256 专用 | SHA-2 256 消息调度数组被擦除 |
| 23 | prim_sha2.sv:282: `ASSERT(WipeDigestAssert, …) SHA256模 | 同 #20，SHA-256 专用 | SHA-2 256 摘要寄存器被擦除 |
| 24 | prim_sha2.sv:523: `ASSERT(ValidDigestModeFlag_A, …) | run_hash → digest_mode_flag_q in {SHA2_256,SHA2_384,SHA2_512} | 哈希运行时摘要模式合法 |
| 25 | prim_sha2_pad.sv:384: `ASSERT(ValidDigestModeFlag_A, …) | sel_data in {Pad80,LenHi,LenLo} \|\| inc_txcount → digest_mode_flag_q 合法 | 填充操作时摘要模式合法 |

注：hmac_reg_top.sv:2654 有注释掉的 `ASSUME(reqParity, …)`，被降级/禁用。

## 四、树内参考
| # | 参考物 (绝对路径) | 类型 | 可对比什么 |
|---|---|---|---|
| 1 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_sha2.sv | 参考实现（SHA-2 压缩/调度/摘要核心） | HMAC 实例化 prim_sha2_32 → prim_sha2；wipe 逻辑、round 计数、compress 函数正确性 |
| 2 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_sha2_32.sv | 参考实现（32-bit 输入包装器） | 32→64 位字拼接、多模/单模分支、word_part_count 状态机 |
| 3 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_sha2_pad.sv | 参考实现（SHA-2 填充） | 512/1024 位块填充、长度域附加、FIFO 状态机 |
| 4 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_sha2_pkg.sv | 参考实现（常量/类型/函数包） | InitHash、CubicRootPrime 常量值、compress_multi_256/compress_512/calc_w_256/calc_w_512 函数、err_code_e 枚举 |
| 5 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/doc/theory_of_operation.md | 规范文档 | NIST FIPS 180-4 SHA-2 规范引用、HMAC 双轮流程（inner pad → msg → outer pad + inner digest）、消息长度计算 |
| 6 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/doc/programmers_guide.md | 规范文档 | SW 操作序列（CFG→KEY→hash_start→MSG_FIFO→hash_process→DIGEST）、上下文保存/恢复流程 |

## 五、特殊结构提示

### 5.1 wipe_secret_we 门控极性反转（关键风险点）
- **位置**: hmac_reg_top.sv:2128
- **代码**: `assign wipe_secret_we = (addr_hit[8] && reg_we && reg_error);`
- **对比**: 所有其他寄存器使用 `!reg_error`（如 key_0_we 在 2131 行: `addr_hit[9] && reg_we && !reg_error`）
- **后果**: 正常 SW 写入 WIPE_SECRET（reg_error=0）→ wipe_secret_we=0 → 擦除无效；仅在 TL-UL 错误（reg_error=1）时才触发擦除
- **预言机依据**: hjson HMAC.SECURE_WIPE（hmac.hjson:162-163）+ hjson WIPE_SECRET 描述（hmac.hjson:421-439）+ SVA WipeSecretKeyAssert（hmac.sv:951）均要求正常写入时擦除生效

### 5.2 err_code priority case 重复项（结构风险点）
- **位置**: hmac.sv:850-858
- **代码**: `priority case (1'b1)` 中 `hash_start_sha_disabled` 出现两次（行 851 和行 856），第二个为死代码
- **后果**: 由于使用 `priority case`，重复项本身不改变功能，但 `invalid_config_atstart` 虽然contributing to err_valid（hmac.sv:844），却在 err_code case 中无对应分支——当 invalid_config_atstart==1 且其他条件为 0 时，err_code 保持 NoError 而非专用错误码
- **预言机依据**: hjson 描述 "it will be blocked from starting and an error is signalled to the SW"（hmac.hjson:274,331），err_valid 被触发但 err_code 无对应枚举值

### 5.3 unique case 覆盖性
- hmac_core.sv:137: `unique case (key_length_i)` 有 default 空分支（行 184-186），Key_None 不显式列出——若 key_length_i==Key_None 进入 default，i_pad/o_pad 全零，但 HMAC 模式下应已被 invalid_config 挡住
- hmac_core.sv:329: FSM `unique case (st_q)` 有 default: st_d=StIdle（行 451-453），覆盖非法状态
- hmac_core.sv:239: `unique case (digest_size_i)` 有 default 空分支（行 243），txcnt_eq_blksz 保持 0

### 5.4 密钥/摘要位宽与参数化
- secret_key: 1024-bit（hmac.sv:41），hjson NumKeyWords=32（hmac.hjson:100）
- digest: sha_word64_t [7:0] = 512-bit（hmac.sv:115），hjson NumDigestWords=16（hjson:89）
- SHA2_256 只用 digest[7:0][31:0]（256-bit），SHA2_384 截断 digest[7:4] 的部分位
- 若擦除后 digest CSR 不完整覆写（digest_size_started_q==SHA2_None 分支，hmac.sv:279-283），检查所有 16 个 CSR 是否都被覆写

### 5.5 FIFO 写使能与 msg_allowed 门控
- MSG_FIFO 写入需 msg_allowed==1（hmac.sv:628），msg_allowed 在 hash_start_or_continue 后置 1（hmac.sv:418），在 packer_flush_done 后清 0（hmac.sv:420）
- FIFO 硬件侧写入（hmac_fifo_wsel==1）不受 msg_allowed 门控，直接由 hmac_core 的 StPushToMsgFifo 状态驱动

### 5.6 done_state 冷却计数器
- hmac.sv:180-189: DoneAwaitHashComplete 状态需 cool_down_ct_q 从 0 计到 127 才触发 hash_done_event
- 若 hash_running 在冷却期间重新拉高，计数器不重置（cool_down_ct_d 仅 cool_down_ct_q+1），可能导致延迟触发或时序窗口

### 5.7 注释降级 SVA
- hmac_reg_top.sv:2654: `//`ASSUME(reqParity, …)` — 已注释掉，TL-UL 请求奇偶校验假设被禁用
- hmac.sv:941: `//`ASSERT(ValidHashStartAssert, …)` — 已注释掉，hash_start 重复触发检查被禁用
