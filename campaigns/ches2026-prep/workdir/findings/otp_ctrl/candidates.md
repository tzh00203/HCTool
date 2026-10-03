# otp_ctrl 候选漏洞清单

## 覆盖摘要

- 扫描范围：`hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/` 全部 16 个 SV 文件（10040 行）+ `hw/ip/otp_ctrl/rtl/otp_ctrl_pkg.sv`（203 行）+ `hw/top_earlgrey/ip_autogen/otp_ctrl/data/otp_ctrl.hjson`（2953 行）
- 预言机弹药：`oracle-inventory/otp_ctrl.md`（121 条预言机：42 SEC_CM + 16 行为描述 + 51 SVA + 8 参考 + 4 特殊结构提示）
- 各 lens 产出：L1=3 条, L2=3 条, L3=2 条, L4=4 条, L5=3 条, L6=1 条, 总计 17 条候选（2 major + 15 minor/验证通过）
- 未覆盖区域：otp_ctrl_reg_pkg.sv（40815 行，纯寄存器定义，人工跳过）、otp_ctrl_core_reg_top.sv 的全部 we 表达式（仅抽样检查前 2162 行，未逐条审计所有 50+ 个寄存器写使能极性）

---

### CAND-otp_ctrl-001
- 疑点: 3 个 SVA 断言被注释降级——对应 SEC_CM 声明存在但运行时合同未激活
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl.sv:1493-1498`
- 代码摘录:
  ```sv
  // `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT(TlLcGateFsm_A,
  //     u_tlul_lc_gate.u_state_regs, alert_tx_o[2])
  // `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT(PrimFsmCheck_A,
  //     u_otp.gen_generic.u_impl_generic.u_state_regs, alert_tx_o[3])
  // `ASSERT_PRIM_REG_WE_ONEHOT_ERROR_TRIGGER_ALERT(PrimRegWeOnehotCheck_A,
  //     u_otp.gen_generic.u_impl_generic.u_reg_top, alert_tx_o[3])
  ```
- lens: L1 (SEC_CM-vs-RTL)
- 预言机依据: SEC_CM 条目 #44 `TEST_TL_LC_GATE.FSM.SPARSE`（sec_cm_testplan:268）声明 TL-UL LC 门控 FSM sparse 编码对策；SVA 清单 #46-48 标记"[注释/降级]"；otp_ctrl.sv:1485 有 `IMPORTANT TODO` 注释确认该检查未完成
- 建议验证型: 组合 micro-tb——向 `u_tlul_lc_gate` 注入 sparse FSM 非法态，观测 alert_tx_o[2] 是否触发；若不触发则确认 sec-cm-mismatch

### CAND-otp_ctrl-002
- 疑点: `fatal_prim_otp_alert` 直连 alert 发送器但未纳入 fatal 错误锁存逻辑——OTP 宏致命错误触发 alert 但不推动 FSM 进入 ErrorSt（不触发本地 escalation）
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl.sv:768`（赋值）+ `otp_ctrl.sv:568-574`（alerts 数组）+ `otp_ctrl.sv:413-462`（锁存逻辑缺失）
- 代码摘录:
  ```sv
  // line 768
  assign fatal_prim_otp_alert = otp_macro_i.fatal_alert;
  // line 568-574
  assign alerts = {
    recov_prim_otp_alert,
    fatal_prim_otp_alert,   // <-- 直连，未经锁存
    fatal_bus_integ_error_q,
    fatal_check_error_q,
    fatal_macro_error_q
  };
  // line 416-418: 锁存逻辑仅覆盖 macro/check/bus_integ 三类
  fatal_macro_error_d = fatal_macro_error_q;
  fatal_check_error_d = fatal_check_error_q;
  fatal_bus_integ_error_d = fatal_bus_integ_error_q | (|intg_error);
  // fatal_prim_otp_alert 不在以上任何表达式中
  ```
- lens: L1 (SEC_CM-vs-RTL) + L2 (hjson-spec-vs-RTL)
- 预言机依据: (1) hjson 行为描述 #8: "This alert triggers if hardware detects an uncorrectable error during an OTP transaction"——隐含错误不可恢复，应锁存；(2) hjson 行为描述 #9: "This alert triggers if any of the background checks fails"——fatal_check_error 应覆盖所有致命条件；(3) otp_ctrl.sv:1485 `IMPORTANT TODO: Add checks that the incoming fatal conditions from prim_otp trigger alerts.`——开发者自己标注未完成；(4) SVA 清单 #46-48（注释掉的断言）本应检查 prim_otp 内部 FSM 错误→alert 路径
- 建议验证型: 组合 micro-tb——使 `otp_macro_i.fatal_alert=1` 持续 1 周期后拉低，观测：(a) alert 是否持续触发（若不持续=未锁存=洞）；(b) 各子 FSM 是否进入 ErrorSt（若不进入=无 escalation=洞）

### CAND-otp_ctrl-003
- 疑点: `intg_error[2]`（`otp_macro_i.fatal_lc_fsm_err`）被锁存进 `fatal_bus_integ_error_q`，但信号源是 LC FSM 错误而非总线完整性错误——错误分类语义错配，可能掩盖真实 bus integrity error 或误导 SW 诊断
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl.sv:107`（赋值）+ `otp_ctrl.sv:418`（锁存）
- 代码摘录:
  ```sv
  logic [2:0] intg_error;
  assign intg_error[2] = otp_macro_i.fatal_lc_fsm_err; // LC FSM error
  // ...
  fatal_bus_integ_error_d = fatal_bus_integ_error_q | (|intg_error);
  // intg_error[2] 算作 "bus_integ_error"，但实际是 LC FSM error
  ```
- lens: L3 (树内参考对比)
- 预言机依据: SEC_CM 条目 #1 `BUS.INTEGRITY` 定义为 "End-to-end bus integrity scheme"；intg_error[0] 和 [1] 确实来自 TL-UL 总线完整性检查，但 intg_error[2] 语义不同；hjson 状态寄存器 `status.bus_integ_error` 位名暗示纯总线错误
- 建议验证型: 脚本——向 `otp_macro_i.fatal_lc_fsm_err` 注入 1，读取 `status.bus_integ_error` CSR，确认 SW 看到的错误类型与实际不符

### CAND-otp_ctrl-004
- 疑点: VendorTest 分区的 `MacroEccUncorrError` 不触发 `fatal_macro_error`——hjson 错误描述声称不可恢复但该分区降级为可恢复
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl.sv:428-432`
- 代码摘录:
  ```sv
  fatal_macro_error_d |= part_error[k] == MacroError;
  // While uncorrectable ECC errors are always reported, they do not trigger a fatal alert
  // event in some partitions like the VENDOR_TEST partition.
  if (PartInfo[k].integrity) begin
    fatal_macro_error_d |= part_error[k] == MacroEccUncorrError;
  end
  // VendorTest 分区 integrity=1'b0，所以 MacroEccUncorrError 不触发 fatal
  ```
- lens: L2 (hjson-spec-vs-RTL)
- 预言机依据: (1) hjson 行为描述 #4: "An uncorrectable ECC error...This error should never occur during normal operation and is not recoverable."——无分区例外声明；(2) 但 hjson features 部分（:1992-1998）明确说 "In this partition, ECC uncorrectable errors will not lead to fatal errors and alerts. Instead the error will be reported as correctable ECC error."——有文档化例外；(3) otp_ctrl_part_pkg.sv:126 VendorTest 的 `integrity: 1'b0` 与代码逻辑一致
- 建议验证型: 组合 micro-tb——向 VendorTest 分区注入 ECC uncorr error，观测 fatal_macro_error alert 是否触发（预期不触发）；验证是否可恢复（SW 清除 status 后是否恢复操作）

### CAND-otp_ctrl-005
- 疑点: scramble FSM ErrorSt 不清除敏感内部状态（key_state_q, data_state_q, digest_state_q）——错误态后密钥/数据残留直至 reset
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_scrmbl.sv:420-423`（ErrorSt 处理）+ `otp_ctrl_scrmbl.sv:480-504`（寄存器更新）
- 代码摘录:
  ```sv
  ErrorSt: begin
    fsm_err_o = 1'b1;
    // 注意：没有 key_state_en=0/data_state_en=0/digest_state_en=0
    // 也没有强制写零清除——寄存器保持错误前的值
  end
  // ...
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      key_state_q    <= '0;  // 仅 reset 清除
      data_state_q   <= '0;
      digest_state_q <= '0;
    end else begin
      if (key_state_en)  key_state_q  <= key_state_d;   // ErrorSt 不使能
      if (data_state_en) data_state_q <= data_state_d;  // ErrorSt 不使能
      // 结果：旧值保持
    end
  end
  ```
- lens: L3 (树内参考对比) + L2 (hjson-spec-vs-RTL)
- 预言机依据: (1) SEC_CM 声明 #2 `SECRET.MEM.SCRAMBLE`："Secret partitions are scrambled with a full-round PRESENT cipher"——密钥应在错误后不可访问；(2) SEC_CM 声明 #8 `SCRMBL.FSM.SPARSE` + #23 `SCRMBL.FSM.LOCAL_ESC`——错误态应完全锁定；(3) 对比其他 IP（aes_core ErrorSt 清除 key/state，kmac ErrorSt 清除 state）——scrmbl 未做等价处理
- 建议验证型: 时序 tb——使 scrmbl FSM 进入 ErrorSt 后，通过 DPI 探测 key_state_q/data_state_q 是否仍保持错误前的密钥值

### CAND-otp_ctrl-006
- 疑点: `OTP_LC_DATA_DEFAULT.state` 使用按位 OR 运算 `LcStTestUnlocked0 | (LcStRma & {8{(&1'b1)}})`——**脚本验证结果：当前值等价于 LcStTestUnlocked0（PASS）**，但 OR 模式是"意外正确"：仅因 8-bit mask 限制了 OR 到 LcStTestUnlocked0 已有的低 8 位；若 mask 扩展到全宽，结果会变成 LcStRma（完全不同的非法状态）。这种混淆模式阻碍代码审查，且与 OT-017 GT 同构。
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/otp_ctrl/rtl/otp_ctrl_pkg.sv:66-67`
- 代码摘录:
  ```sv
  state: lc_ctrl_state_pkg::LcStTestUnlocked0 |
         (lc_ctrl_state_pkg::LcStRma & {8{(&1'b1)}}),
  ```
- lens: L5 (常量折叠)
- 预言机依据: (1) 模式 `obfuscated-constant-mismatch`——GT OT-017 正是同一类型的 OTP LC 默认状态 OR 篡改；(2) **Python 脚本验证**：`LcStTestUnlocked0 | (LcStRma & {8{1'b1}})` 的 320-bit 结果与 `LcStTestUnlocked0` bit-exact 相等——OR 未改变任何位；(3) 原因：LcStTestUnlocked0 和 LcStRma 的低 8 位相同（0xEE），OR 无效；(4) 但此表达式是"意外正确"——若 mask 改为 `{320{1'b1}}`，结果会变成 LcStRma，违反注释 "put the life cycle into TEST_UNLOCKED0 by default"；(5) 混淆模式阻碍人工审查，易被注入者利用
- 建议验证型: 已由脚本验证通过（verify_otp_constants.py）；保留为 [minor]——混淆模式可疑但当前值正确

### CAND-otp_ctrl-007
- 疑点: `FLASH_OTP_KEY_RSP_DEFAULT` 使用多层混淆表达式——必须脚本验证解码后值是否与预期匹配
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/otp_ctrl/rtl/otp_ctrl_pkg.sv:157-163`
- 代码摘录:
  ```sv
  parameter flash_otp_key_rsp_t FLASH_OTP_KEY_RSP_DEFAULT = '{
      data_ack: (~(|4'h0)) || (&(~4'hF)),
      addr_ack: ((1'b1 << 1) >> 1) !== 1'b0,
      key: {FlashKeyWidth{1'b0}} ^ {FlashKeyWidth{1'b0}},
      rand_key: '0,
      seed_valid: (|(~0)) && (!(&0))
  };
  ```
- lens: L5 (常量折叠)
- 预言机依据: (1) 模式 `obfuscated-constant-mismatch`——OT-018 GT 是 flash key 默认值混淆篡改；(2) 逐表达式分析：`(~(|4'h0))` = `(~0)` = 1, `(&(~4'hF))` = `(&0)` = 0, 所以 `data_ack = 1 || 0 = 1`；(3) `((1'b1 << 1) >> 1)` = `(2 >> 1)` = 1, `!== 1'b0` = true = 1, 所以 `addr_ack = 1`；(4) `(|(~0))` 在 SV 中 `~0` 是全1，所以 `|` 全1 = 1, `(!(&0))` = `(!0)` = 1, 所以 `seed_valid = 1`；(5) 但以上是心算——OT-017/018 教训要求必须脚本验证，特别是位宽和运算符优先级可能影响结果
- 建议验证型: 已由脚本验证通过（verify_otp_constants.py）——data_ack=1, addr_ack=1, seed_valid=1；保留为 [minor]——混淆模式可疑但当前值正确

### CAND-otp_ctrl-008
- 疑点: `OTP_LC_DATA_DEFAULT.valid` 和 `.error` 使用混淆表达式——**脚本验证通过：valid=1, error=0**
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/otp_ctrl/rtl/otp_ctrl_pkg.sv:64-65`
- 代码摘录:
  ```sv
  valid: (1'b1 && 1'b1) || (1'b0 && 1'b0),  // 预期 1
  error: (2'b01 != 2'b01),                    // 预期 0
  ```
- lens: L5 (常量折叠)
- 预言机依据: 模式 `obfuscated-constant-mismatch`；表达式简单但遵循"一切混淆常量必须脚本验证"规则
- 建议验证型: 已由脚本验证通过（verify_otp_constants.py）——valid=1, error=0

### CAND-otp_ctrl-009
- 疑点: `ScrmblBlockWidth = (64 >> 1) << 1` 混淆——结果应为 64，但若注入者将 64 改为奇数（如 63），结果会静默变为 62，改变 OTP 分区块宽度
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/otp_ctrl/rtl/otp_ctrl_pkg.sv:26`
- 代码摘录:
  ```sv
  parameter int ScrmblBlockWidth = (64 >> 1) << 1;
  ```
- lens: L5 (常量折叠)
- 预言机依据: (1) 模式 `obfuscated-constant-mismatch`；(2) 当前值 64 是偶数，`(64>>1)<<1 = 64` 正确；(3) 但混淆模式隐藏了"保证偶数"的意图，若上游修改了基础值而不更新此处，结果会静默改变；(4) 多个 SVA 断言（OffsetMustBeBlockAligned_A, SizeMustBeBlockAligned_A）依赖此值正确性
- 建议验证型: 已由脚本验证通过（verify_otp_constants.py）——(64 >> 1) << 1 = 64；保留为 [minor]——混淆模式可疑但当前值正确

### CAND-otp_ctrl-010
- 疑点: part_buf FSM 进入 ErrorSt 通过 ecc_err 路径时未设置 `fsm_err_o`——仅设置 `error_d = CheckFailError`；而 cnt_err/escalate 路径同时设置 `fsm_err_o = 1'b1` 和 `error_d = FsmStateError`。稀疏 FSM 错误触发断言 `CtrlPartBufFsmCheck_A` 仅检查 `fsm_err_o`，故 ECC 错误不触发该断言
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_part_buf.sv:600-614`
- 代码摘录:
  ```sv
  // SEC_CM: PART.FSM.LOCAL_ESC
  if (ecc_err) begin
    state_d = ErrorSt;
    if (state_q != ErrorSt) begin
      error_d = CheckFailError;
    end
    // 注意：fsm_err_o 未设置！
  end
  // SEC_CM: PART.FSM.LOCAL_ESC, PART.FSM.GLOBAL_ESC
  if (lc_ctrl_pkg::lc_tx_test_true_loose(escalate_en_i) || cnt_err) begin
    state_d = ErrorSt;
    fsm_err_o = 1'b1;  // <-- 这里设置了
    if (state_q != ErrorSt) begin
      error_d = FsmStateError;
    end
  end
  ```
- lens: L3 (树内参考对比)
- 预言机依据: (1) SEC_CM #22 `PART.FSM.LOCAL_ESC` 声明 "partition FSMs are moved into an invalid state upon local escalation"——ECC 错误是 local escalation 的一种，但 fsm_err_o 未设置意味着 sparse FSM 断言不覆盖此路径；(2) 顶层 `fatal_check_error_d |= part_error[k] inside {CheckFailError, FsmStateError}` 仍会捕获（通过 error_o），但 FSM 错误断言漏检；(3) 对比 unbuf 分区同样模式——一致但不代表正确
- 建议验证型: 组合 micro-tb——向 buf 分区注入 ECC error，观测 CtrlPartBufFsmCheck_A 断言是否触发（预期不触发，因为 fsm_err_o=0）

### CAND-otp_ctrl-011
- 疑点: KDI 模块的 nonce 输出使用 `entropy_cnt[0]` 作为 2-bit 索引选择 nonce_out_q 的 64-bit block——若 NumNonceChunks > 2，`entropy_cnt[0]` 只能索引 0/1，高索引 block 永远不被写入
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_kdi.sv:267`
- 代码摘录:
  ```sv
  if (nonce_reg_en) begin
    nonce_out_d[entropy_cnt[$clog2(NumNonceChunks)-1:0]] = edn_data_i;
  end
  ```
- lens: L4 (结构 lint)
- 预言机依据: (1) `entropy_cnt` 宽度 CntWidth=2（line 213），可表示 0-3；(2) `NumNonceChunks` 取决于最大 nonce 宽度：SramNonceWidth=128, ScrmblBlockWidth=64, 所以 SramNonceSel=128/64=2, OtbnNonceSel=64/64=1, FlashNonceSel=128/64=2；(3) `NumNonceChunks = max(OtbnNonceSel, FlashNonceSel, SramNonceSel) = 2`；(4) 所以 `$clog2(2)-1:0 = 0:0`，即只用 `entropy_cnt[0]`，可索引 0/1——刚好覆盖 2 个 chunk；(5) 此为正确设计，nonce_out_d[0] 和 [1] 都会被写入；(6) **撤回**——经验证此非漏洞，但索引切片模式需人工确认
- 建议验证型: 脚本——计算 NumNonceChunks 并确认 $clog2(NumNonceChunks) <= CntWidth

### CAND-otp_ctrl-012
- 疑点: PRESENT 加密/解密使用迭代式单物理轮实现（NumPhysRounds=1）+ 循环计数器——每轮的 key schedule 和 p-layer 计算是数据依赖的，但 PRESENT 是固定轮数固定操作的分组密码，不存在操作数依赖的可变时序路径。SCA 风险来自轮计数器本身的泄露，但已被 prim_count 冗余计数器保护
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_scrmbl.sv:446-472`
- 代码摘录:
  ```sv
  prim_present #(
    .KeyWidth(128),
    .NumRounds(NumPresentRounds),
    .NumPhysRounds(1)
  ) u_prim_present_enc (
    .data_i ( data_state_q ),
    .key_i  ( key_state_q  ),
    .idx_i  ( idx_state_q  ),
    .data_o ( enc_data_out ),
    ...
  );
  ```
- lens: L6 (SCA 结构)
- 预言机依据: (1) SEC_CM #2 `SECRET.MEM.SCRAMBLE` 声明使用 PRESENT 加密；(2) prim_present 是固定时序分组密码实现——每轮执行相同的 S-box 替换和 P-layer 置换，无操作数条件分支；(3) 迭代式实现（NumPhysRounds=1）意味着每时钟周期执行 1 轮，总延迟 31 周期——时序侧信道可观测轮数但不可观测数据值；(4) 无动态 mask——PRESENT 实现本身不使用 PRNG mask（不同于 AES 的 DOM masking），但 OTP scramble 的安全模型不要求 DPA 保护（仅要求逻辑正确性）
- 建议验证型: 时序 tb——对比两个不同密钥的加密时序波形，确认无数据依赖时序差异

### CAND-otp_ctrl-013
- 疑点: OTP 宏命令 sparse 编码（otp_ctrl_macro_pkg.sv:57-64）的 Hamming distance=4 是声明值——如果注入者修改了命令码，可能导致 OTP 宏行为异常（例如将 Write 码改为 Read 码的邻值）
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_macro_pkg.sv:57-64`
- 代码摘录:
  ```sv
  typedef enum logic [6:0] {
    Read    = 7'b1000101,
    Write   = 7'b0110111,
    ReadRaw = 7'b1111001,
    WriteRaw= 7'b1100010,
    Init    = 7'b0101100
  } cmd_e;
  ```
- lens: L5 (常量折叠) + L1 (SEC_CM-vs-RTL)
- 预言机依据: (1) 预言机目录特殊结构提示 #7："5 个命令码 Hamming distance = 4，这是 FSM sparse encoding 的另一种形式"；(2) SEC_CM #4-9 声明 DAI/KDI/LCI/PART/SCRMBL/TIMER FSM sparse 编码——OTP 宏命令码是类似的 sparse 编码保护；(3) 必须用脚本验证 10 对命令码间 Hamming distance 均 >= 4
- 建议验证型: 已由脚本验证通过——10 对命令码 Hamming distance 均=4，min=4 >= 4 PASS；保留为 [minor]——编码正确但属于必须验证的混淆常量类

### CAND-otp_ctrl-014
- 疑点: DAI 命令解码 `unique case (dai_cmd_i)` 的 default 分支为空 `default: ;`——5 个无效编码 (000,011,101,110,111) 被静默忽略，不触发错误，FSM 留在 IdleSt 如同无事发生
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_dai.sv:309`
- 代码摘录:
  ```sv
  unique case (dai_cmd_i)
    DaiRead:  begin state_d = ReadSt; ... end
    DaiWrite: begin ... end
    DaiDigest: begin ... end
    default: ; // Ignore invalid commands
  endcase
  ```
- lens: L4 (结构 lint)
- 预言机依据: (1) `dai_cmd_e` 是 3-bit 枚举（DaiRead=001, DaiWrite=010, DaiDigest=100），5/8 编码未定义；(2) DAI 是 SW 访问 OTP 的主要接口——无效命令被吞没意味着故障注入可抑制 digest/read/write 操作而不触发任何错误；(3) 对比 DAI FSM 的 `unique case (state_q)` 的 default 分支跳 ErrorSt 并设 fsm_err_o=1（line 681-684）——命令解码的 default 应遵循同一安全模式
- 建议验证型: 组合 micro-tb——向 DAI 发送无效命令编码（如 3'b000），观测 FSM 是否留在 IdleSt 且无错误指示

### CAND-otp_ctrl-015
- 疑点: scramble 命令解码 `unique case (cmd_i)` 的 default 分支为空 `default: ;`——2 个无效编码 (110,111) 被静默忽略
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_scrmbl.sv:369`
- 代码摘录:
  ```sv
  unique case (cmd_i)
    Decrypt: begin ... end
    Encrypt: begin ... end
    LoadShadow: begin ... end
    Digest: begin ... end
    DigestInit: begin ... end
    DigestFinalize: begin ... end
    default: ; // ignore
  endcase
  ```
- lens: L4 (结构 lint)
- 预言机依据: (1) `otp_scrmbl_cmd_e` 是 3-bit 枚举，6/8 编码已定义，2 个 (110,111) 未定义；(2) scramble 数据通路用于密钥分区加解密和 digest 计算——无效命令被吞没意味着故障注入可抑制加解密/digest 操作；(3) scrmbl FSM 的 `unique case (state_q)` 的 default 分支正确跳 ErrorSt 并设 fsm_err_o=1（line 427-430）——命令解码的 default 不一致
- 建议验证型: 组合 micro-tb——向 scrmbl 发送无效命令编码（如 3'b110），观测 FSM 是否留在 IdleSt 且无错误指示

### CAND-otp_ctrl-016
- 疑点: KDI ErrorSt 不锁定/清零密钥输出——部分计算的密钥可能残留在 prim_sec_anchor_flop 中并被 flash/SRAM/OTBN 消费
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_kdi.sv:548-550`
- 代码摘录:
  ```sv
  ErrorSt: begin
    fsm_err_o = 1'b1;
    // 无 key_out_d 清零/锁定逻辑
    // 无 nonce_out_d 清零/锁定逻辑
  end
  ```
- lens: L4 (结构 lint) + L2 (hjson-spec-vs-RTL)
- 预言机依据: (1) 对比 otp_ctrl_part_buf.sv:578 ErrorSt 设置 `dout_locked_d = MuBi8True` 锁定输出——KDI 无等效锁定；(2) `prim_sec_anchor_flop` 仅在 reset 时初始化为 `RndCnstScrmblKeyInit.key`，ErrorSt 不触发重初始化；(3) 若 KDI 在 DigWaitSt 只完成一半密钥计算时被推入 ErrorSt，`key_out_q` 持有部分密钥且 `seed_valid_q` 未更新——消费者可能使用不完整密钥
- 建议验证型: 时序 tb——使 KDI 在 DigWaitSt 中途触发 escalation 进入 ErrorSt，观测 flash_otp_key_o/sram_otp_key_o 是否仍持有部分密钥值

### CAND-otp_ctrl-017
- 疑点: LCI ErrorSt 不设置 fsm_err_o——与 DAI/scrmbl/part_buf 的 ErrorSt 行为不一致
- 位置: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_lci.sv:211-214`
- 代码摘录:
  ```sv
  ErrorSt: begin
    if (error_q == NoError) begin
      error_d = FsmStateError;
    end
    // fsm_err_o 未设置！默认 1'b0
  end
  ```
- lens: L4 (结构 lint)
- 预言机依据: (1) 对比 otp_ctrl_scrmbl.sv:422 ErrorSt 设 `fsm_err_o = 1'b1`；(2) 对比 otp_ctrl_dai.sv:674 ErrorSt 设 `fsm_err_o = 1'b1`（通过 fsm_err_d 默认赋值）；(3) LCI 的 `fsm_err_o` 仅在 default 分支（line 221）和 escalation override（line 230）时设 1；(4) 若 LCI 通过正常 OTP 编程错误（WriteWaitSt line 198）进入 ErrorSt，fsm_err_o=0 → part_fsm_err[LciIdx]=0 → 顶层 |part_fsm_err 不反映此错误；错误仍通过 part_error[LciIdx] 传播，但 fsm_err_o 不一致意味着 CtrlLciFsmCheck_A 断言不覆盖此路径
- 建议验证型: 组合 micro-tb——使 LCI 通过 OTP 编程错误进入 ErrorSt，观测 CtrlLciFsmCheck_A 断言是否触发（预期不触发）
