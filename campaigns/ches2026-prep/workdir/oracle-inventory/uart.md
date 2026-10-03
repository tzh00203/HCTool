# uart 盲预言机目录

## 元信息
- 树: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
- 扫描范围: hw/ip/uart/{rtl,data,doc}
- SEC_CM 声明数: 1 / SVA 数: 21 / testplan 条目数: 21

## 一、SEC_CM 声明 ↔ RTL 锚点
| # | SEC_CM 声明 (hjson:line) | RTL 锚点 (file:line) | 检验要点 |
|---|---|---|---|
| 1 | BUS.INTEGRITY (uart.hjson:163) | uart.sv:68 `// SEC_CM: BUS.INTEGRITY` | intg_err_o 连到 alerts[0]；uart_reg_top.sv:87 拼接 err_q\|intg_err\|reg_we_err；err_q 一旦置1不清（line 77-83）；alert_sender IsFatal=1'b1（uart.sv:104） |

## 二、行为性描述句（hjson 原文 → 检验点）
| # | hjson 原文 (file:line) | 检验点 |
|---|---|---|
| 1 | "This fatal alert is triggered when a fatal TL-UL bus integrity fault is detected." (uart.hjson:89-92) | alert_list 名为 fatal_fault；alerts[0] 来自 intg_err_o；err_q 是锁存不清的寄存器——一旦 bus integrity 出错，alert 永久拉高，只有 reset 才能恢复。验证 uart_reg_top.sv:80-83 的 `if (intg_err \|\| reg_we_err) err_q <= 1'b1` 无 else 清零分支 |
| 2 | "Self-clearing status trigger for the DMA. Set when RX or TX FIFOs are past their configured watermarks matching watermark interrupt behaviour." (uart.hjson:134-138) | **关键预言机**：hjson 声明 lsio_trigger 在 RX/TX FIFO 超过 watermark 时置位，但 RTL 实现（uart_core.sv:356-363）在复位后无条件赋 `lsio_trigger_o <= 1'b1`，完全忽略 FIFO watermark 条件。检验：lsio_trigger_o 应为 `event_rx_watermark \| event_tx_watermark` 的函数，而非常量 1 |
| 3 | "RX fifo reset. Write 1 to the register resets RX_FIFO. Read returns 0" (uart.hjson:332-336) | uart_core.sv:81 `uart_fifo_rxrst = reg2hw.fifo_ctrl.rxrst.q & reg2hw.fifo_ctrl.rxrst.qe`——需 .q=1 且 .qe=1 才生效（WO 语义通过 qe 门控）；prim_fifo_sync clr_i 连此信号 |
| 4 | "TX fifo reset. Write 1 to the register resets TX_FIFO. Read returns 0" (uart.hjson:339-343) | uart_core.sv:82 `uart_fifo_txrst = reg2hw.fifo_ctrl.txrst.q & reg2hw.fifo_ctrl.txrst.qe`——同上 WO+qe 门控 |
| 5 | "If the FIFO depth is greater than or equal to the setting, it raises rx_watermark interrupt." (uart.hjson:346-348) | uart_core.sv:350 `event_rx_watermark = (rx_fifo_depth >= rx_thresh_val)`；rx_thresh_val 按 rxilvl 移值算（line 338-349），需逐枚举值对比 |
| 6 | "If the FIFO depth is less than the setting, it raises tx_watermark interrupt." (uart.hjson:382-384) | uart_core.sv:321 `event_tx_watermark = tx_fifo_depth < tx_watermark_thresh`；tx_watermark_thresh 按 txilvl 积值算（line 313-321），注意饱和逻辑 `if (uart_fifo_txilvl >= (TxFifoDepthW-2))` |
| 7 | "Trigger level for RX break detection. Sets the number of character times the line must be low to detect a break." (uart.hjson:237-240) | uart_core.sv:115-120 的 unique case：rxblvl=0→≥2, 1→≥4, 2→≥8, default(3)→≥16；与 hjson 枚举 break2/break4/break8/break16 一一对应 |
| 8 | "If PARITY_EN is true, this determines the type, 1 for odd parity, 0 for even." (uart.hjson:231-233) | uart_tx.sv:67 parity_enable 时插入 wr_parity；uart_core.sv:209 `wr_parity = (^tx_fifo_data) ^ reg2hw.ctrl.parity_odd.q`——偶校验时 XOR-sum=parity_odd=0，奇校验时 XOR-sum=parity_odd=1。uart_rx.sv:102-103 `rx_parity_err = parity_enable & rx_valid_q & (^{sreg_q[9:1],parity_odd})`——收端同逻辑 |
| 9 | "If this bit is turned on, any outgoing bits to TX are received through RX. Note that the TX line goes 1 if System loopback is enabled." (uart.hjson:213-217) | uart_core.sv:262 `rx_in = sys_loopback ? tx_out : ...`；uart_core.sv:222 `tx_out_q <= 1'b1` when sys_loopback——两者需同时成立 |
| 10 | "If this bit is turned on, incoming bits are forwarded to TX for testing purpose. Note that the internal design sees RX value as 1 always if line loopback is enabled." (uart.hjson:221-225) | uart_core.sv:215 `tx = line_loopback ? rx : tx_out_q`；uart_core.sv:263 `rx_in = ... line_loopback ? 1'b1 : rx_in_mx`——两者需同时成立 |
| 11 | "RX noise filter enable. If the noise filter is enabled, RX line goes through the 3-tap repetition code. It ignores single IP clock period noise." (uart.hjson:205-208) | uart_core.sv:257-260 三输入多数表决 `rx_in_maj`；uart_core.sv:260 `rx_in_mx = rxnf_enable ? rx_in_maj : rx_sync`——nf=1 走多数表决，nf=0 直通 |
| 12 | "raised if the transmit FIFO is past the high-water mark." (uart.hjson:60-63, type=status, default=1) | intr_hw_tx_watermark 使用 IntrT="Status"（uart_core.sv:406），是电平中断，复位后因 TX FIFO 空 depth<thresh 所以默认=1 |
| 13 | "raised if the transmit FIFO is empty." (uart.hjson:83-86, type=status, default=1) | intr_hw_tx_empty 使用 IntrT="Status"（uart_core.sv:419），电平中断，复位后默认=1 |
| 14 | "raised if the receive FIFO has overflowed." (uart.hjson:69-70) | uart_core.sv:401 `event_rx_overflow = rx_fifo_wvalid & ~rx_fifo_wready`——溢出字被丢弃（rx_fifo_wready=0 时 prim_fifo_sync 不接受） |

## 三、SVA 清单（行为合同）
| # | 断言 (file:line) | 内容摘要 | 约束的预期行为 |
|---|---|---|---|
| 1 | TxEnIsOne_A (uart.sv:120) | `cio_tx_en_o === 1'b1` | TX 始终驱动使能，由 line 117 `assign cio_tx_en_o = 1'b1` 兑现 |
| 2 | TxKnown_A (uart.sv:121) | `ASSERT_KNOWN(cio_tx_o, ...)` | TX 输出值在使能后不出现 X |
| 3 | AlertsKnown_A (uart.sv:124) | `ASSERT_KNOWN(alert_tx_o)` | alert 输出不出现 X |
| 4 | TxWatermarkKnown_A (uart.sv:127) | `ASSERT_KNOWN(intr_tx_watermark_o)` | tx_watermark 中断不出现 X |
| 5 | TxEmptyKnown_A (uart.sv:128) | `ASSERT_KNOWN(intr_tx_empty_o)` | tx_empty 中断不出现 X |
| 6 | RxWatermarkKnown_A (uart.sv:129) | `ASSERT_KNOWN(intr_rx_watermark_o)` | rx_watermark 中断不出现 X |
| 7 | TxDoneKnown_A (uart.sv:130) | `ASSERT_KNOWN(intr_tx_done_o)` | tx_done 中断不出现 X |
| 8 | RxOverflowKnown_A (uart.sv:131) | `ASSERT_KNOWN(intr_rx_overflow_o)` | rx_overflow 中断不出现 X |
| 9 | RxFrameErrKnown_A (uart.sv:132) | `ASSERT_KNOWN(intr_rx_frame_err_o)` | rx_frame_err 中断不出现 X |
| 10 | RxBreakErrKnown_A (uart.sv:133) | `ASSERT_KNOWN(intr_rx_break_err_o)` | rx_break_err 中断不出现 X |
| 11 | RxTimeoutKnown_A (uart.sv:134) | `ASSERT_KNOWN(intr_rx_timeout_o)` | rx_timeout 中断不出现 X |
| 12 | RxParityErrKnown_A (uart.sv:135) | `ASSERT_KNOWN(intr_rx_parity_err_o)` | rx_parity_err 中断不出现 X |
| 13 | LsioTriggerKnown_A (uart.sv:136) | `ASSERT_KNOWN(lsio_trigger_o)` | lsio_trigger 输出不出现 X（注意：当前 RTL 赋常量 1，此断言虽通过但失去实际约束力） |
| 14 | RaclErrorKnown_A (uart.sv:137) | `ASSERT_KNOWN(racl_error_o.valid)` | RACL 错误 valid 信号不出现 X |
| 15 | RegWeOnehotCheck_A (uart.sv:140) | `ASSERT_PRIM_REG_WE_ONEHOT_ERROR_TRIGGER_ALERT` | reg_we 为 one-hot，违例触发 alert_tx_o[0]（BUS.INTEGRITY 的 RTL 兑现路径之一） |
| 16 | wePulse (uart_reg_top.sv:1905) | `ASSERT_PULSE(reg_we)` | reg_we 是单周期脉冲 |
| 17 | rePulse (uart_reg_top.sv:1906) | `ASSERT_PULSE(reg_re)` | reg_re 是单周期脉冲 |
| 18 | reAfterRv (uart_reg_top.sv:1908) | `$rose(reg_re\|\|reg_we) \|=> tl_o_pre.d_valid` | 请求后下一周期响应有效 |
| 19 | en2addrHit (uart_reg_top.sv:1910) | `(reg_we\|\|reg_re) \|-> $onehot0(addr_hit)` | 访问时地址命中 one-hot0 |
| 20 | TxFifoDepth_A (uart_core.sv:38) | `TxFifoDepth < 256` | TX FIFO 深度限制（与 FIFO_STATUS.TXLVL 8-bit 宽度一致） |
| 21 | RxFifoDepth_A (uart_core.sv:39) | `RxFifoDepth < 256` | RX FIFO 深度限制（与 FIFO_STATUS.RXLVL 8-bit 宽度一致） |

## 四、树内参考
| # | 参考物 (绝对路径) | 类型 | 可对比什么 |
|---|---|---|---|
| 1 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/doc/theory_of_operation.md | 规范注释 | 帧格式（START+8data+parity?+STOP）、波特率公式、中断语义、break 检测语义——与 RTL 逐条对照 |
| 2 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/doc/registers.md | 规范注释 | 寄存器字段语义与 hjson 一致，可交叉验证 |
| 3 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/dv/sva/uart_bind.sv | 参考实现 | 绑定 tlul_assert（Device 端 TL-UL 协议断言）和 uart_csr_assert_fpv（CSR 一致性断言），为 BUS.INTEGRITY 的额外验证层 |
| 4 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_tx.sv ↔ uart_rx.sv | 兄弟模块 | TX 和 RX 的 baud 分频逻辑同构（都做 16x 分频取进位），可交叉对比 baud_div/tick_baud 行为一致性 |
| 5 | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/prim/rtl/prim_intr_hw.sv | 参考实现 | 9 个中断实例的 IntrT 参数：tx_watermark/tx_empty/rx_watermark 为 "Status"（电平），其余 6 个为默认 "Event"（脉冲）。可验 IntrT 与 hjson type 字段一致 |

## 五、特殊结构提示

### 1. lsio_trigger_o 语义丢失（hjson↔RTL 矛盾）
- hjson (line 134-138) 声明 lsio_trigger 为 "Self-clearing status trigger for the DMA. Set when RX or TX FIFOs are past their configured watermarks"
- RTL (uart_core.sv:356-363) 实现为 `lsio_trigger_o <= 1'b1`（无条件常量赋值），注释说 "Simplified assertion for static data path enablement"
- **可检验预言机**：lsio_trigger_o 应等于 `event_rx_watermark | event_tx_watermark`（或类似 watermark 条件组合），而非硬 1

### 2. Break 检测 FSM 的 default 分支
- uart_core.sv:135-137 有 `default: break_st_q <= BRK_CHK`——2-bit 枚举只有 2 态，default 理论不可达但存在。若注入将 break_st_q 篡改为非法态，default 会回 BRK_CHK（可恢复）。检验该 FSM 无未覆盖态逃逸。

### 3. FIFO reset 的 WO+qe 双门控
- uart_core.sv:81-82：`rxrst = .q & .qe`，WO 寄存器的 .qe 来自 prim_flop 延迟一拍。两次连续写同一值时 qe 只在第一拍有效。验证软件协议：写 1 清 FIFO 后无需回读。

### 4. RX FIFO 入队门控
- uart_core.sv:28'2': `rx_fifo_wvalid = rx_valid & ~event_rx_frame_err & ~event_rx_parity_err`——帧错误和校验错误的字符不进 FIFO。若攻击者注入此门控（去掉 `~event_rx_frame_err`），错误帧会混入 FIFO。

### 5. TX override 与安全
- uart_core.sv:219-220：`ovrd_tx_en` 时 `tx_out_q <= ovrd_tx_val`，允许 SW 直接驱动 TX 线。hjson 标记 `excl:CsrAllTests:CsrExclWrite`（协议违规场景）。若 ovrd 信号在非预期时刻被置位，可破坏 TX 通信。

### 6. NCO 计数器无保护
- uart_core.sv:167-173：nco_sum_q 纯加法溢出取进位做 tick_baud_x16，无范围检查。NCO=0 时 tick_baud_x16 永远为 0（TX/RX 时钟停），但无 alert 或错误指示。

### 7. reg_we_check 中只读寄存器 we=0
- uart_reg_top.sv:1767-17784：`reg_we_check[5]=1'b0`(STATUS), `[6]=1'b0`(RDATA), `[9]=1'b0`(FIFO_STATUS), `[11]=1'b0`(VAL)——这些只读寄存器的 we 被硬0，不参与 one-hot 检查。若 prim_reg_we_check 实现有偏差可能漏检。

### 8. RACL 门控对寄存器写使能的影响
- uart_reg_top.sv:1664-1762：所有 `*_we` 和 `*_re` 信号都由 `racl_addr?_hit_write/read[idx] & reg_we/re & !reg_error` 门控。若 EnableRacl=0，racl_addr_hit 退化为 addr_hit（无权限过滤），安全语义依赖 top-level 正确设置 EnableRacl=1。
