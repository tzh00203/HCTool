# HMAC Blind Hunt — Candidate List

## 覆盖摘要
- 扫描文件: hmac.sv (967行), hmac_core.sv (502行), hmac_reg_top.sv (2657行), prim_sha2.sv (首200行), prim_sha2_pkg.sv (首100行), prim_sha2_pad.sv (首50行)
- hjson: hmac.hjson (features/countermeasures/寄存器描述)
- Lens 产出: L1=2, L2=4, L3=1, L4=3, L5=0, L6=1 → 总 11 候选
- 未覆盖区域: prim_sha2_32.sv 包装器内部（已读 hmac.sv 实例化连线）、prim_sha2_pad.sv 填充 FSM 全文（仅首50行）、prim_sha2 压缩函数算术正确性（需 DPI 差分验证，非盲检范围）

---

### CAND-HMAC-01
- 疑点: wipe_secret_we 门控极性反转——正常 SW 写入 WIPE_SECRET 无法触发擦除
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac_reg_top.sv:2128
- 代码摘录:
  ```systemverilog
  assign wipe_secret_we = (addr_hit[8] && reg_we && reg_error);   // line 2128 — INVERTED
  assign key_0_we       = (addr_hit[9] && reg_we && !reg_error);  // line 2131 — correct
  ```
- lens: L1 SEC_CM-vs-RTL + L2 hjson-spec-vs-RTL + L4 结构lint
- 预言机依据:
  - hjson HMAC.SECURE_WIPE feature (hmac.hjson:163): "Wipe of internal state and secret key with constant value provided by software"
  - hjson WIPE_SECRET 寄存器描述 (hmac.hjson:427): "The clear secret operation overwrites the internal variables with the provided 32-bit value"
  - SVA WipeSecretKeyAssert (hmac.sv:951): `wipe_secret |=> secret_key == {32{$past(wipe_v)}}` — 此断言依赖 wipe_secret 在正常写入时为 1，但极性反转使其在正常写入时为 0，断言前提不触发
  - 同文件一致性: 所有其他寄存器 we 信号（intr_state_we, intr_enable_we, cfg_we, cmd_we, key_0_we..key_31_we, digest_*_we）均使用 `!reg_error`，唯独 wipe_secret_we 使用 `reg_error`
- 建议验证型: 组合micro-tb（向 WIPE_SECRET 写入后检查 secret_key 是否被覆写）+ SVA WipeSecretKeyAssert 反证

### CAND-HMAC-02
- 疑点: err_code priority case 中 hash_start_sha_disabled 重复项 + invalid_config_atstart 无对应 err_code 分支
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac.sv:850-875
- 代码摘录:
  ```systemverilog
  priority case (1'b1)
    hash_start_sha_disabled: begin        // line 851 — FIRST occurrence
      err_code = SwHashStartWhenShaDisabled;
    end
    hash_start_sha_disabled: begin        // line 856 — DUPLICATE (dead code)
      err_code = SwHashStartWhenShaDisabled;
    end
    hash_start_active: ...
    msg_push_not_allowed: ...
    update_seckey_inprocess: ...
    default: err_code = NoError;
  endcase
  ```
  invalid_config_atstart 贡献 err_valid (line 844) 但无 err_code 分支
- lens: L4 结构lint
- 预言机依据:
  - hjson 描述 (hmac.hjson:274): "it will be blocked from starting and an error is signalled to the SW" — invalid_config 触发 err_valid 中断但 err_code 保持 NoError，SW 无法区分无效配置错误与其他零错误状态
  - lc_ctrl LcStProd 重复 case 值 (OT-027) 为同类结构性异常先例
- 建议验证型: 组合micro-tb（配置无效 digest_size 后 hash_start，检查 err_code 寄存器值 ≠ NoError）

### CAND-HMAC-03
- 疑点: SHA2_512 外层 HMAC 轮消息长度计算错误——default 分支返回 SHA2_384 长度
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac_core.sv:229
- 代码摘录:
  ```systemverilog
  // outer pad (sel_msglen == SelOPadMsg)
  unique case (digest_size_i)
    SHA2_256: sha_msg_len = BlockSizeSHA256in64 + 64'd256;    // 512+256=768 ✓
    SHA2_384: sha_msg_len = BlockSizeSHA512in64 + 64'd384;    // 1024+384=1408 ✓
    default:  sha_msg_len = BlockSizeSHA512in64 + 64'd384;    // 1024+384=1408 ✗ should be 1024+512=1536
  endcase
  ```
- lens: L2 hjson-spec-vs-RTL + L3 树内参考对比
- 预言机依据:
  - hmac_core.sv SVA ValidDigestSize_A (line 499-500) 声明 `digest_size_i inside {SHA2_256, SHA2_384, SHA2_512}` 当 hmac_en && sel_msglen==SelOPadMsg，即 SHA2_512 在外层轮可达
  - NIST FIPS 180-4: SHA-512 摘要输出 512 位，外层 HMAC 消息长度 = block_size(1024) + digest_output(512) = 1536 bits，而非 1408 bits
  - 对比 inner pad 分支 (line 217-219): SHA2_256/SHA2_384/SHA2_512 均显式列出，外层分支缺 SHA2_512 显式项
  - OT-007 (hmac opad 384≠512) 为同类密码功能错误先例
- 建议验证型: DPI 差分（对比 OpenSSL HMAC-SHA512 输出）+ 时序 tb（追踪 sha_message_length_o 当 digest_size_i==SHA2_512 外层轮）

### CAND-HMAC-04
- 疑点: WIPE_SECRET 寄存器读取返回 key[0] 数据——密钥材料泄露
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac_reg_top.sv:2418-2420
- 代码摘录:
  ```systemverilog
  addr_hit[8]: begin                          // HMAC_WIPE_SECRET_OFFSET
    reg_rdata_next[31:0] = reg2hw.key[0].q;  // returns KEY[0] instead of wipe_secret value!
  end
  ```
  addr_hit[8] 映射到 WIPE_SECRET (line 1953: `addr_hit[ 8] = (reg_addr == HMAC_WIPE_SECRET_OFFSET)`)
- lens: L4 结构lint
- 预言机依据:
  - hjson WIPE_SECRET 寄存器描述为 swaccess="wo"（只写），但 reg_top rdata 仍返回 key[0] 而非 '0 或安全默认值
  - 任何 SW 读取 WIPE_SECRET 地址（即使是未定义行为的只读访问）将泄露密钥第一个 32-bit 字
  - 同文件对比: key_0 (addr_hit[9]) 返回 key[1].q（偏移错位），key_1 (addr_hit[10]) 返回 '0——整体 rdata 映射异常
- 建议验证型: 组合micro-tb（读取 WIPE_SECRET CSR 地址，检查返回值不等于 key[0]）

### CAND-HMAC-05
- 疑点: SVA ValidHashStartAssert 被注释降级——hash_start 重复触发无保护
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac.sv:941
- 代码摘录:
  ```systemverilog
  // Below condition is covered by the design (2020-02-19)
  //`ASSERT(ValidHashStartAssert, hash_start_or_continue |-> !initiated)
  ```
- lens: L2 hjson-spec-vs-RTL
- 预言机依据:
  - 注释声称"covered by the design"但 design 中 hash_start (hmac.sv:360) = `reg_hash_start & sha_en & ~cfg_block & ~invalid_config`，若第一次 hash 已 cfg_block=1 后 SW 再写 hash_start，hash_start 被挡但 reg_hash_start 仍触发——若 cfg_block 在 hash_done 与第二次 start 间有单周期窗口，可能重入
  - hjson 描述 (hmac.hjson:449): "The registers are allowed to be updated only when the engine is in Idle state" — 重入违反此约束
  - hmac_reg_top.sv:2654 的 reqParity ASSUME 亦被注释降级（两条 SVA 降级）
- 建议验证型: 时序 tb（在 hash_process 后但 hash_done 前的窗口写入 hash_start，检查 FSM 不重入 StIPad）

### CAND-HMAC-06
- 疑点: WIPE_SECRET 的 wipe_v 来自 SW 写入而非 PRD——安全擦除无真随机性保证
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac.sv:210-211
- 代码摘录:
  ```systemverilog
  assign wipe_secret = reg2hw.wipe_secret.qe;
  assign wipe_v      = reg2hw.wipe_secret.q;  // SW-controlled, not PRD
  ```
- lens: L1 SEC_CM-vs-RTL
- 预言机依据:
  - hjson HMAC.SECURE_WIPE feature (hmac.hjson:163): 声称 "Wipe of internal state and secret key with constant value provided by software"
  - hjson WIPE_SECRET 描述 (hmac.hjson:429): "It is recommended to use a value extracted from an entropy source" — 仅为推荐，非硬约束
  - 若 SW 写入 wipe_v=0，所有内部状态（secret_key/hash_q/w_q/digest_q）被覆写为全零——虽"擦除"但值可预测，SCA 攻击者可据此推断旧值是否为零
  - 对比 kmac: kmac_reduced.sv 使用 LFSR PRD mask 进行 SEC_WIPE
- 建议验证型: [minor] 单一依据（hjson 为推荐而非硬约束），标注为 SCA 弱化

### CAND-HMAC-07
- 疑点: SEC_CM 仅声明 BUS.INTEGRITY 一条——缺少 SEC_WIPE/FSM.LOCAL_ESC 等安全关键对策声明
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/data/hmac.hjson (countermeasures 段)
- 代码摘录:
  ```
  countermeasures: [
    { name: "BUS.INTEGRITY",
      desc: "End-to-end bus integrity scheme."
    }
  ]
  ```
- lens: L1 SEC_CM-vs-RTL
- 预言机依据:
  - RTL 实现了 wipe_secret 擦除逻辑（hmac.sv:216-217, prim_sha2.sv:93-94,124-125,147-148）但无 SEC_CM 对应声明
  - SVA WipeSecretKeyAssert (hmac.sv:951) + prim_sha2 WipeHashAssert/WipeMsgSchArrAssert/WipeDigestAssert 均存在但无 SEC_CM 映射
  - sec-cm-mismatch 模式（OT-001,006,012,013,016 命中 5 个 GT）：声明缺失=实现无法通过 sec_cm_testplan 验证
- 建议验证型: 交叉比对 hmac_sec_cm_testplan.hjson 条目

### CAND-HMAC-08
- 疑点: done_state 冷却计数器在 hash_running 重新拉高时不重置——可能提前触发 hash_done_event
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac.sv:180-189
- 代码摘录:
  ```systemverilog
  DoneAwaitHashComplete: begin
    if (!hash_running) begin
      if (cool_down_ct_q < 8'd127) begin
        cool_down_ct_d = cool_down_ct_q + 1'b1;
        hash_done_event = 1'b0;
        done_state_d = DoneAwaitHashComplete;
      end else begin
        hash_done_event = 1'b1;       // fires after 128 cycles of !hash_running
        done_state_d = DoneAwaitCmd;
      end
    end
    // if hash_running is re-asserted, cool_down_ct_q is NOT reset
  end
  ```
- lens: L2 hjson-spec-vs-RTL
- 预言机依据:
  - 若 hash_running 在冷却期间重新拉高（例如 SW 在 stop 后立即 continue），cool_down_ct_q 保留已积累值，下次 !hash_running 时从非零开始——128 周期冷却保证被缩短
  - 对比 aes_ctr_fsm 延迟告警 (OT-019 变体)：计数器不重置导致时序窗口
- 建议验证型: 时序 tb（stop→continue→stop 序列，检查 hash_done_event 不提前触发）

### CAND-HMAC-09
- 疑点: FIFO 硬件侧写入（hmac_fifo_wsel==1）不受 msg_allowed 门控——绕过 SW 写保护
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac.sv:546
- 代码摘录:
  ```systemverilog
  assign fifo_wvalid = (hmac_fifo_wsel && fifo_wready) ? hmac_fifo_wvalid : reg_fifo_wvalid;
  // hmac_fifo_wsel path has NO msg_allowed gate
  assign msg_write = msg_fifo_req & msg_fifo_we & ~hmac_fifo_wsel & msg_allowed;  // SW path gated
  ```
- lens: L2 hjson-spec-vs-RTL
- 预言机依据:
  - 设计意图：msg_allowed 在 hash_start_or_continue 后置 1（hmac.sv:418），在 packer_flush_done 后清 0（hmac.sv:420），防止 SW 在非运行状态写消息
  - FIFO 硬件侧（hmac_core 的 StPushToMsgFifo 状态）直接写 FIFO 无 msg_allowed 检查——若 hmac_core FSM 异常进入 StPushToMsgFifo（例如错误态），可在非运行状态向 FIFO 注入数据
  - hmac_core FSM 有 default: st_d=StIdle (line 451-453) 覆盖非法状态，但 StPushToMsgFifo 的进入条件仅依赖 fifo_wready_i 和 fifo_wdata_sel_o 计数
- 建议验证型: [minor] 单一依据（正常路径 hmac_core FSM 不会在非运行状态进入 StPushToMsgFifo），存疑

### CAND-HMAC-10
- 疑点: SHA2_None 分支下 digest CSR 覆写可能不完整——16 个 CSR 中仅覆盖 i=0..7 的 [i] 和 [i+8]
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac.sv:279-283
- 代码摘录:
  ```systemverilog
  end else begin // for SHA2_None
    // to ensure secret wiping is always passed to digest CSRs
    hw2reg.digest[i].d   = conv_endian32(digest[i][31:0], digest_swap);
    hw2reg.digest[i+8].d = conv_endian32(digest[i][31:0], digest_swap);
  end
  ```
  循环 i=0..7，覆盖 hw2reg.digest[0..7] 和 [8..15]——但 digest[i] 为 sha_word64_t[7:0]，
  SHA2_None 分支仅取 digest[i][31:0]（低 32 位），丢弃 [63:32]（高 32 位）
- lens: L2 hjson-spec-vs-RTL
- 预言机依据:
  - hjson WIPE_SECRET 描述 (hmac.hjson:427): "The clear secret operation overwrites the internal variables with the provided 32-bit value"
  - SVA WipeDigestAssert (prim_sha2.sv:187/282): 检查 digest_q=={N{wipe_v_i}}——覆盖 64-bit 全字
  - 但 CSR 端 SHA2_None 分支仅映射低 32 位，若 wipe 后 digest_q 高 32 位非零但 CSR 不反映——SCA 攻击者可通过侧信道观测残留高 32 位
- 建议验证型: [minor] 功能上 wipe 确实清除了 digest_q 全 64-bit（由 prim_sha2 SVA 保证），CSR 映射截断是显示问题而非清除问题

### CAND-HMAC-11
- 疑点: HMAC-SHA2 密码数据通路无 SCA 掩码——压缩函数输入直接使用 secret_key XOR ipad/opad 常量
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac_core.sv:139-186
- 代码摘录:
  ```systemverilog
  i_pad_256 = {secret_key_i[1023:896], {(BlockSizeSHA256-128){1'b0}}} ^ {(BlockSizeSHA256/8){8'h36}};
  ```
  secret_key_i 直接参与 XOR 运算，无 PRNG mask
- lens: L6 SCA 结构
- 预言机依据:
  - hjson 无 MSG.MASKING 或 KEY.MASKING 声明（countermeasures 仅 BUS.INTEGRITY）
  - 对比 kmac: kmac_reduced.sv 使用 LFSR 动态 msg_mask 对消息通路掩码
  - HMAC 的 secret_key XOR ipad/opad 为固定常量 XOR，功耗/EM 与 key Hamming weight 线性相关——典型 SCA 泄露点
  - 注意：这是设计选择而非 bug（OpenTitan HMAC 未声称 SCA 防护），但作为 SCA 弱化点值得报告
- 建议验证型: 时序 tb（对照移位寄存器差分，测量 key 变化时 i_pad 功耗差异）
