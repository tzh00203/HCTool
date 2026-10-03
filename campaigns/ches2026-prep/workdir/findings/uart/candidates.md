# UART 候选漏洞清单

## 覆盖摘要

- 扫描文件: uart.sv, uart_core.sv, uart_rx.sv, uart_tx.sv, uart_reg_top.sv, uart_reg_pkg.sv, uart.hjson
- L1 SEC_CM-vs-RTL: 0 条（BUS.INTEGRITY 唯一声明，实现一致）
- L2 hjson-spec-vs-RTL: 1 条（lsio_trigger_o hjson↔RTL 矛盾）
- L3 树内参考对比: 1 条（TX/RX baud_div 行为差异 + TX override）
- L4 结构 lint: 2 条（undefined rxilvl=7 + RACL 退化为无权限）
- L5 常量折叠: 1 条（lsio_trigger_o 常量替换动态信号，与 L2 交叉佐证）
- L6 SCA 结构: 0 条（UART 非密码 IP，无 SCA 攻击面）
- 未覆盖区域: uart_reg_top.sv 的 RACL policy 细粒度权限矩阵未逐条验证（需 top-level 配置）；prim_fifo_sync 内部实现未深度走查（vendored 原语，非 IP RTL）

---

### CAND-uart-01
- 疑点: lsio_trigger_o 无条件赋常量 1'b1，hjson 声明应为 FIFO watermark 条件触发
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_core.sv:356-363
- 代码摘录:
  ```systemverilog
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      lsio_trigger_o <= 1'b0;
    end else begin
      // Simplified assertion for static data path enablement
      // TX/RX watermark logic handled within downstream DMA FSM
      lsio_trigger_o <= 1'b1;
    end
  end
  ```
- lens: L2 (hjson-spec-vs-RTL) + L5 (constant-replaces-dynamic) + fixed-value-signal 模式
- 预言机依据:
  1. hjson uart.hjson:134-138 原文："Self-clearing status trigger for the DMA. Set when RX or TX FIFOs are past their configured watermarks matching watermark interrupt behaviour." — 明确声明 lsio_trigger 应在 FIFO 超过 watermark 时置位，而非常量 1
  2. SVA LsioTriggerKnown_A (uart.sv:136) `ASSERT_KNOWN(lsio_trigger_o)` — 常量 1 下此断言虽通过但完全失去约束力，无行为合同价值
  3. RTL 注释 "Simplified assertion for static data path enablement" + "TX/RX watermark logic handled within downstream DMA FSM" — 注释声称逻辑已移至下游，但 hjson 未声明此变更，形成 spec↔code+注释 三方不一致
  4. 正确实现应为 `lsio_trigger_o <= event_rx_watermark | event_tx_watermark;`（或注册版），与 event_rx_watermark (line 350) 和 event_tx_watermark (line 321) 已计算但未使用的事实吻合
- 建议验证型: 组合 micro-tb：驱动 RX FIFO 至超过/低于 watermark，观测 lsio_trigger_o 是否变化；vuln 版始终为 1，twin 版应随 watermark 条件翻转

---

### CAND-uart-02
- 疑点: Break 检测 FSM 无 FSM.LOCAL_ESC 声明，非法态无告警
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_core.sv:123-140
- 代码摘录:
  ```systemverilog
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) break_st_q <= BRK_CHK;
    else begin
      unique case (break_st_q)
        BRK_CHK: begin
          if (event_rx_break_err) break_st_q <= BRK_WAIT;
        end
        BRK_WAIT: begin
          if (rx_in) break_st_q <= BRK_CHK;
        end
        default: begin
          break_st_q <= BRK_CHK;
        end
      endcase
    end
  end
  ```
- lens: L1 (SEC_CM-vs-RTL) + L4 (结构 lint)
- 预言机依据:
  1. hjson countermeasures 仅声明 BUS.INTEGRITY (uart.hjson:162-166)，无任何 FSM.LOCAL_ESC 声明
  2. break_st_e 为 1-bit 枚举仅 2 态，default 分支理论不可达但存在（line 135-137）——若故障注入产生非法态，default 恢复到 BRK_CHK 但无 alert
  3. 同树 aes/kmac 等 IP 的 FSM 均声明 SEC_CM *.FSM.LOCAL_ESC 并用 sparse_fsm_flop 编码，UART 缺失此对策
- 建议验证型: 故障注入 tb：将 break_st_q 强制为非法态（2'b11），观测是否有 alert 输出；预期无 alert（vuln），twin 应有 alert

---

### CAND-uart-03
- 疑点: TX override (ovrd_tx_en) 允许 SW 直接驱动 TX 线，无额外安全门控
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_core.sv:216-226
- 代码摘录:
  ```systemverilog
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      tx_out_q <= 1'b1;
    end else if (ovrd_tx_en) begin
      tx_out_q <= ovrd_tx_val;
    end else if (sys_loopback) begin
      tx_out_q <= 1'b1;
    end else begin
      tx_out_q <= tx_out;
    end
  end
  ```
- lens: L2 (hjson-spec-vs-RTL) + L3 (树内参考)
- 预言机依据:
  1. hjson uart.hjson:434 标记 `excl:CsrAllTests:CsrExclWrite`——承认写入 ovrd.txen 导致协议违规
  2. theory_of_operation.md 未提及 TX override 的安全约束或使用条件
  3. ovrd_tx_en 由 RW 寄存器控制（uart_reg_top.sv:1452），无 lc_ctrl 门控或权限分级——任何可写该寄存器的 SW 均可劫持 TX 线
  4. 若 RACL 未配置写权限限制，非特权 SW 也可设置 ovrd_tx_en
- 建议验证型: micro-tb：在 TX 传输进行中设置 ovrd_tx_en=1, ovrd_tx_val=0，观测 TX 线是否被劫持；验证 RACL 配置下非特权角色写 OVRD 是否被拒

---

### CAND-uart-04
- 疑点: NCO=0 时 TX/RX 时钟停止，无任何错误指示或 alert
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_core.sv:167-175
- 代码摘录:
  ```systemverilog
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      nco_sum_q <= 17'h0;
    end else if (tx_enable || rx_enable) begin
      nco_sum_q <= {1'b0,nco_sum_q[NcoWidth-1:0]} + {1'b0,reg2hw.ctrl.nco.q[NcoWidth-1:0]};
    end
  end
  assign tick_baud_x16 = nco_sum_q[16];
  ```
- lens: L2 (hjson-spec-vs-RTL) + L4 (结构 lint)
- 预言机依据:
  1. NCO=0 时 nco_sum_q 始终为 0，tick_baud_x16 恒 0，TX/RX 完全停转
  2. hjson uart.hjson:260-263 描述 NCO 为 "BAUD clock rate control"，未提及 NCO=0 为非法值或需软件保证
  3. theory_of_operation.md:115-125 的波特率公式在 NCO=0 时给出 f_baud=0，文档未讨论此边界
  4. 无 STATUS 位、无 alert、无 interrupt 指示 NCO=0 异常——软件可能写入 NCO=0（意外或攻击）后，UART 静默失效
- 建议验证型: micro-tb：设置 NCO=0, tx_enable=1, 写 WDATA，观测 TX 线是否保持 idle 且无任何错误指示

---

### CAND-uart-05
- 疑点: rxilvl=7（3-bit 字段的未定义值）使 rx_watermark 中断永不触发
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_core.sv:338-351
- 代码摘录:
  ```systemverilog
  unique case (uart_fifo_rxilvl)
    default: begin
      if (uart_fifo_rxilvl > RxFifoDepthW - 1) begin
        rx_thresh_val = {RxFifoDepthW{1'b1}};
      end else begin
        rx_thresh_val = 1'b1 << uart_fifo_rxilvl;
      end
    end
    RxFifoDepthW-1: rx_thresh_val = RxFifoDepthW'(RxFifoDepth - 2);
  endcase
  event_rx_watermark = (rx_fifo_depth >= rx_thresh_val);
  ```
- lens: L4 (结构 lint) + L2 (hjson-spec-vs-RTL)
- 预言机依据:
  1. hjson uart.hjson:349-378 定义 rxilvl 枚举仅 7 个值（0-6: rxlvl1/rxlvl2/rxlvl4/rxlvl8/rxlvl16/rxlvl32/rxlvl62），3-bit 字段可表达 0-7
  2. rxilvl=7 时 rx_thresh_val = 7'h7F = 127，而 RxFifoDepth=64，FIFO 深度永远无法达到 127，event_rx_watermark 恒为 0
  3. 无 WARL 约束（reggen 未为 rxilvl 生成最大值限制），SW 可写入 7
  4. 此为 width-truncation/未定义枚举值的变体——功能失效但不报错
- 建议验证型: micro-tb：设置 rxilvl=7，填充 RX FIFO 至 64 字节，观测 rx_watermark 中断是否触发；预期不触发（vuln），twin 应将 rxilvl=7 映射为 rxilvl=6 或拒绝写入

---

### CAND-uart-06
- 疑点: EnableRacl=0（默认值）时 RACL 退化为无权限过滤，所有角色可读写所有寄存器
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_reg_top.sv:1622-1626
- 代码摘录:
  ```systemverilog
  end else begin : gen_no_racl
    racl_addr_hit_read  = addr_hit;
    racl_addr_hit_write = addr_hit;
  end
  ```
- lens: L4 (结构 lint) + L2 (hjson-spec-vs-RTL)
- 预言机依据:
  1. uart.sv:13 参数默认 `EnableRacl = 1'b0`——若 top-level 未显式传 1，RACL 完全无效
  2. uart_reg_top.sv:1624-1625：EnableRacl=0 时 racl_addr_hit_read/write = addr_hit，绕过所有权限检查
  3. racl_error_o.valid (line 1631) 在 EnableRacl=0 时为 0（因为 |addr_hit & ... 中 racl_addr_hit_read/write = addr_hit，条件 ~|addr_hit 为 0），即 RACL 错误永不报告
  4. hjson uart.hjson:52 声明 `racl_support: true`——声称支持 RACL 但默认关闭
- 建议验证型: 组合验证：在 EnableRacl=0 的 top-level 配置下，用非特权角色写 CTRL 寄存器，验证写入成功（应为拒绝）；对比 EnableRacl=1 时行为

---

### CAND-uart-07
- 疑点: rx_fifo_wvalid 门控可被注入移除，使帧错误字符混入 RX FIFO
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_core.sv:282
- 代码摘录:
  ```systemverilog
  assign rx_fifo_wvalid = rx_valid & ~event_rx_frame_err & ~event_rx_parity_err;
  ```
- lens: L3 (树内参考) + L4 (结构 lint)
- 预言机依据:
  1. theory_of_operation.md:67-71 描述："After it detects the START bit... If the STOP bit is detected as high and the optional parity bit is correct the data byte is pushed into a... RX FIFO."——明确要求帧错误和校验错误的字符不进 FIFO
  2. 当前实现正确（~event_rx_frame_err & ~event_rx_parity_err 门控），但此门控为单行组合逻辑，无冗余保护——注入移除任一反相器即可让错误字符入 FIFO
  3. 若攻击者将 `~event_rx_frame_err` 替换为 `event_rx_frame_err`（极性反转），帧错误字符反而更容易入 FIFO
- 建议验证型: 组合 micro-tb：注入帧错误（STOP bit=0），观测 rx_fifo_wvalid 是否为 0（正确）；修改 RTL 移除 ~event_rx_frame_err 后重跑，验证错误字符入 FIFO

---

### CAND-uart-08
- 疑点: SEC_CM 仅声明 BUS.INTEGRITY，无 SEC_WIPE / FSM.LOCAL_ESC / TOKEN.DIFF 等——UART 安全面虽窄但缺少对 CTRL/OVRD 等寄存器的写保护声明
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/data/uart.hjson:162-166
- 代码摘录:
  ```
  countermeasures: [
    { name: "BUS.INTEGRITY",
      desc: "End-to-end bus integrity scheme."
    }
  ]
  ```
- lens: L1 (SEC_CM-vs-RTL)
- 预言机依据:
  1. hjson 仅声明 BUS.INTEGRITY 一条 countermeasure——相比同树 IP（aes 声明 10+条，hmac 声明 5+条），UART 安全对策声明极度稀疏
  2. err_q (uart_reg_top.sv:77-83) 一旦置 1 不清（永久锁死 alert），但无 SEC_WIPE 声明保证关键寄存器（CTRL, OVRD, FIFO_CTRL）的清除路径使用 PRD
  3. 12 IP 清单中 UART 标注为 "LSIO 触发语义 vs hjson"——即已知存在 hjson↔RTL 不一致（本候选 CAND-uart-01），但无对应 SEC_CM 声明约束
- 建议验证型: 文档审计：对照同树其他 IP 的 SEC_CM 声明模式，确认 UART 的安全面是否确实仅需 BUS.INTEGRITY；若 CTRL/OVRD 寄存器可被非特权 SW 写入且影响安全，需追加对策声明

---

### CAND-uart-09
- 疑点: TX/RX baud 分频器行为不一致——TX 的 baud_div 在 tx_enable=0 时仍自由运行，RX 的 baud_div 在 rx_enable=0 时归零
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_tx.sv:34-42 vs /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_rx.sv:53-68
- 代码摘录 (TX):
  ```systemverilog
  // uart_tx.sv:34-42 — baud_div 始终由 tick_baud_x16 驱动，不受 tx_enable 影响
  end else if (tick_baud_x16) begin
    {tick_baud_q, baud_div_q} <= {1'b0,baud_div_q} + 5'h1;
  end else begin
    tick_baud_q <= 1'b0;
  end
  ```
- 代码摘录 (RX):
  ```systemverilog
  // uart_rx.sv:53-68 — rx_enable=0 时 baud_div 归零
  if (!rx_enable) begin
    sreg_d = 11'h0; bit_cnt_d = 4'h0;
    baud_div_d = 4'h0; tick_baud_d = 1'b0; idle_d = 1'b1;
  end else begin
    ...
    if (tick_baud_x16) begin
      {tick_baud_d, baud_div_d} = {1'b0,baud_div_q} + 5'h1;
    end
  ```
- lens: L3 (树内参考——兄弟模块 TX↔RX 对比)
- 预言机依据:
  1. uart_tx.sv 与 uart_rx.sv 为兄弟模块（oracle-inventory/uart.md §四参考#4），应同构
  2. TX 在 !tx_enable 时 baud_div 自由运行（可能处于任意中间值 0-15），当 tx_enable 从 0→1 时，第一个 tick_baud 可能提前或延后到来，导致首字符的采样点偏移
  3. RX 在 !rx_enable 时 baud_div 归零，rx_enable 从 0→1 时 baud_div 从 0 开始——干净的起始点
  4. 此不一致虽不直接导致安全漏洞，但在 sys_loopback 模式下（TX→RX 路径）可能造成首字符时序对齐问题
- 建议验证型: 时序 tb：在 sys_loopback 模式下，关闭 TX/RX 后重开，发送首字符，对比 TX 发出时刻与 RX 采样时刻的偏差

---

### CAND-uart-10
- 疑点: reg_we_check 对只读寄存器硬 0，若 prim_reg_we_check 实现有偏差可能漏检 we 违例
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_reg_top.sv:1765-1779
- 代码摘录:
  ```systemverilog
  reg_we_check[5]  = 1'b0;  // STATUS (hwext, RO)
  reg_we_check[6]  = 1'b0;  // RDATA  (hwext, RO)
  reg_we_check[9]  = 1'b0;  // FIFO_STATUS (hwext, RO)
  reg_we_check[11] = 1'b0;  // VAL    (hwext, RO)
  ```
- lens: L4 (结构 lint)
- 预言机依据:
  1. reg_we_check 的 one-hot 检查不包含只读寄存器——若硬件故障或 GLITCH 导致某只读寄存器的 we 意外置 1，one-hot 检查不会触发 reg_we_err
  2. uart_reg_top.sv 中 STATUS/RDATA/FIFO_STATUS/VAL 均为 hwext 类型，其 .we 硬接 1'b0（如 line 1147, 1237, 1419, 1507），正常情况下 we 不可能为 1
  3. 但 prim_reg_we_check 仅检查 `oh_i` (reg_we_check) 的 one-hot 属性，不检查未参与寄存器的 we=0 约束——若 GLITCH 在 reg_we_check 某位产生 spuriously 1，可能漏过
  4. SVA RegWeOnehotCheck_A (uart.sv:140) 仅验证 reg_we 违例触发 alert，不验证只读寄存器 we=0 不变量
- 建议验证型: micro-tb：在 STATUS 地址产生 GLITCH 使 reg_we=1，观测 reg_we_check 是否检测到违例；预期不检测（当前 we_check[5]=0），验证 alert 是否触发
