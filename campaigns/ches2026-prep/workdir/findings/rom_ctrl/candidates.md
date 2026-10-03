# rom_ctrl — 6-Lens Blind Hunt Candidates

## 覆盖摘要

- **扫描文件**: rom_ctrl.sv, rom_ctrl_fsm.sv, rom_ctrl_compare.sv, rom_ctrl_mux.sv, rom_ctrl_scrambled_rom.sv, rom_ctrl_counter.sv, rom_ctrl_pkg.sv, rom_ctrl_regs_reg_top.sv, rom_ctrl_rom_reg_top.sv
- **L1 SEC_CM-vs-RTL**: 2 条候选
- **L2 hjson-spec-vs-RTL**: 3 条候选
- **L3 树内参考对比**: 2 条候选
- **L4 结构lint**: 3 条候选
- **L5 常量折叠**: 1 条候选（已脚本验证通过，记录为无洞）
- **L6 SCA结构**: 1 条候选
- **总计**: 12 条候选
- **未覆盖区域**: rom_ctrl_reg_pkg.sv（自动生成，仅类型定义）、doc/ 下的行为规范文档仅作预言机引用未全文审计、scramble_image.py 的 PRINCE round 常量对比未做完整脚本化（见 CAND-rom_ctrl-12）

---

### CAND-rom_ctrl-01
- 疑点: BUS.LOCAL_ESC rvalid 抑制逻辑在 `internal_alert & bus_rom_req` 时泄漏响应——hjson 声称"rvalid can only be high if no internal consistency error has been spotted"，但 RTL 允许已有请求在途时即使 alert 仍传递 rvalid=1
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl.sv:260-261
  ```systemverilog
  assign bus_rom_rvalid = (bus_rom_rvalid_raw | bus_rom_req) &
                          ~(internal_alert & ~bus_rom_req);
  ```
- lens: L1 SEC_CM-vs-RTL
- 预言机依据: (1) hjson rom_ctrl.hjson:224-230 声明 BUS.LOCAL_ESC "bus_rom_rvalid signal... can only be high if no internal consistency error has been spotted"——但真值表验证：当 `internal_alert=1, bus_rom_req=1` 时 `bus_rom_rvalid=1`，直接违反 hjson 声明；(2) SVA BusLocalEscChk_A (rom_ctrl.sv:546) 只检查 `state_d==Invalid |=> !bus_rom_rvalid`（下一周期），不覆盖同周期 overlap；(3) vuln-patterns/rtl/fsm-error-handling GT 实例 OT-019 明确标注 "rom_ctrl: 内部 alert 时 rvalid 仍可置位" 为已知 GT
- 建议验证型: 组合 micro-tb：驱动 `internal_alert=1, bus_rom_req=1, rvalid_raw=0`，观测 `bus_rom_rvalid`；vuln=1 / twin（改为 `~internal_alert` 门控）=0

### CAND-rom_ctrl-02
- 疑点: SecDisableScrambling=1 时全部安全对策被消除：checker FSM 不实例化、rom_select_bus 绑死 MuBi4True、checker_alert=0、kmac 全断、但无任何 fatal alert 或指示通知系统安全已全废
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl.sv:376-405
  ```systemverilog
  assign pwrmgr_data_o = PWRMGR_DATA_DEFAULT; // done=MuBi4True, good=MuBi4True
  assign keymgr_data_o = '{data: {128{2'b10}}, valid: 1'b1};
  assign rom_select_bus = MuBi4True;
  assign checker_alert = 1'b0;
  ```
- lens: L1 SEC_CM-vs-RTL
- 预言机依据: (1) hjson SecDisableScrambling 参数描述（rom_ctrl.hjson:58-68）称 "This isn't intended for real chips"，但 RTL 在 disabled 分支无任何 alert/rflag 通知 SOC 安全检查被跳过；(2) PWRMGR_DATA_DEFAULT 设 done=MuBi4True + good=MuBi4True——pwrmgr 以为 ROM 验证通过，实际跳过验证；(3) SEC_CM CHECKER.CTR.CONSISTENCY / CHECKER.FSM.LOCAL_ESC / MEM.SCRAMBLE / MEM.DIGEST / FSM.SPARSE 等在 disabled 分支全部无实现（17 条 SEC_CM 仅 BUS.INTEGRITY 和 TLUL_FIFO.CTR.REDUN 仍有效）
- 建议验证型: 组合 tb：设 SecDisableScrambling=1，检查 pwrmgr_data_o.done==MuBi4True 且 checker_alert==0——安全检查完全绕过但 pwrmgr 认为通过

### CAND-rom_ctrl-03
- 疑点: hjson 声称 fatal alert "non-recoverable and will be asserted until a hard reset"（rom_ctrl.hjson:80-82），但 SVA PwrmgrDataChk_A 和 KeymgrValidChk_A 在 `internal_alert` 时禁用断言——done/valid 回退被允许
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl.sv:520-527
  ```systemverilog
  `ASSERT(PwrmgrDataChk_A,
          pwrmgr_data_o.done == prim_mubi_pkg::MuBi4True |=>
          pwrmgr_data_o.done == prim_mubi_pkg::MuBi4True,
          clk_i, !rst_ni || internal_alert)
  `ASSERT(KeymgrValidChk_A, keymgr_data_o.valid |=> keymgr_data_o.valid,
          clk_i, !rst_ni || internal_alert)
  ```
- lens: L2 hjson-spec-vs-RTL
- 预言机依据: (1) hjson:80-82 声明 "Fatal alerts are non-recoverable and will be asserted until a hard reset"——但 SVA 在 internal_alert 时主动禁用"done 不可回退"和"valid 不可回退"的约束，允许 alert 后 done 降回 MuBi4False；(2) 这意味着 ROM 检查完成后，如果出现 internal_alert（如 FSM 被 glitch 到 Invalid），pwrmgr_data_o.done 会从 MuBi4True 降为 MuBi4False，pwrmgr 可能重启检查流程——与 "non-recoverable" 语义矛盾
- 建议验证型: 时序 tb：正常 boot 完成后注入 FSM glitch 使 state=Invalid，观测 pwrmgr_data_o.done 是否降回 MuBi4False

### CAND-rom_ctrl-04
- 疑点: reqParity ASSUME 被注释掉（rom_ctrl_regs_reg_top.sv:870），TL a_user.chk_en 约束降级——FPV/验证环境可能缺少此约束
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl_regs_reg_top.sv:870
  ```systemverilog
  //`ASSUME(reqParity, tl_reg_h2d.a_valid |-> tl_reg_h2d.a_user.chk_en == tlul_pkg::CheckDis)
  ```
- lens: L2 hjson-spec-vs-RTL
- 预言机依据: (1) 预言机目录 #44 显式标注"被注释掉"、"约束降级"；(2) 该 ASSUME 约束寄存器 TL 通道的 integrity check enable——去掉后 FPV 可构造不满足 TL 协议的激励，使 BUS.INTEGRITY SEC_CM 验证出现假 pass；(3) 注释说 "formulated as an assumption such that the FPV testbenches do disprove this property by mistake"——说明是有意降级，但这削弱了 BUS.INTEGRITY 的形式化保证
- 建议验证型: FPV 审计：恢复 ASSUME 后重跑 BUS.INTEGRITY 相关 FPV，确认无新反例

### CAND-rom_ctrl-05
- 疑点: hjson 声称 mux "gives access to the checker at the start of time and then switches to the bus, never going back"——但 rom_ctrl_mux.sv:118 的 `bus_rvalid_o` 使用 `mubi4_test_true_strict`（精确匹配 MuBi4True），而非 `mubi4_test_true_loose`（宽松匹配），sel_bus_i 的非标 MuBi4 值可能导致 bus_rvalid_o=0 即使选择信号已指向 bus
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl_mux.sv:114-118
  ```systemverilog
  assign bus_gnt_o    = mubi4_test_true_strict(sel_bus_i);
  assign bus_rvalid_o = mubi4_test_true_strict(sel_bus_q) & rom_rvalid_i;
  ```
- lens: L2 hjson-spec-vs-RTL
- 预言机依据: (1) hjson:241-247 声明 mux 单向切换；(2) bus_gnt_o 和 bus_rvalid_o 均用 `strict` 测试——而 MUX.MUBI 的 sel_invalid 检查使用 `mubi4_test_invalid`（检测非 True/False 值）；若 sel_bus_q 处于"loose true but not strict true"的中间态（如 4'b1011），bus_rvalid_o=0 但 sel_invalid=0——MUX.MUBI 不报错，bus 请求被授予(gnt=0)但响应不返回；(3) 与 MUX.CONSISTENCY 检测逻辑（用 loose test）形成 strict/loose 语义不一致
- 建议验证型: 组合 micro-tb：设 sel_bus_q 为 loose-true 非 strict-true 值（如 4'b1011），检查 bus_rvalid_o vs rom_rvalid_i

### CAND-rom_ctrl-06
- 疑点: rom_ctrl_fsm.sv 将 rom_data_i 声明为 `logic [31:0]`（32位），但 checker_rom_rdata 为 DataWidth 宽（39位含 ECC），连接时截断高7位 `checker_rom_rdata[31:0]`——exp_digest 只取低32位，ECC位被丢弃
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl.sv:371
  ```systemverilog
  .rom_data_i           (checker_rom_rdata[31:0]),
  ```
- lens: L3 树内参考对比
- 预言机依据: (1) rom_ctrl_fsm.sv:91 声明 `input logic [31:0] rom_data_i`——固定32位，与 DataWidth 参数无关；(2) rom_ctrl.sv:62 的 `DataWidth = SecDisableScrambling ? 32 : 39`——scrambling 使能时 DataWidth=39，ECC bit 7:32 被截断；(3) 此截断为设计意图（ECC 由 tl_adapter 检查，exp_digest 仅存数据位），但若 ROM 物理存储的 ECC 位被 fault 注入修改，ECC 检查和 exp_digest 读取走不同路径——CTRL.REDUN 声明只约束地址冗余，未约束数据路径冗余；(4) scrambled_rom 的 clr_rdata_o 是解扰后含 ECC 的 39 位，KMAC 收到的 kmac_rom_data 也是 zero-extended 的 checker_rom_rdata（39位），但 FSM 的 exp_digest 只看到低32位
- 建议验证型: 时序 tb：fault 注入 ROM 中某字的 ECC 位，验证 ECC 检查路径和 exp_digest 读取路径是否一致检测

### CAND-rom_ctrl-07
- 疑点: rom_ctrl_mux 的 alert_o 不是粘性的——尽管 mux 内部 alert_q 是粘性的（line 107: `alert_q <= alert_q | alert_d`），但 rom_ctrl.sv:445 的 `alerts[AlertFatal] = bus_integrity_error | checker_alert | mux_alert` 中 mux_alert 直接连接 mux.alert_o，而 prim_alert_sender 对 fatal alert 本身就是粘性的——双重粘性是否导致 alert 清除时序问题
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl_mux.sv:103-111
  ```systemverilog
  always_ff @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      alert_q <= 0;
    end else begin
      alert_q <= alert_q | alert_d;
    end
  end
  assign alert_o = alert_q;
  ```
- lens: L3 树内参考对比
- 预言机依据: (1) rom_ctrl_mux.sv:46 注释 "This isn't latched in this module because it feeds into a fatal alert at top-level, whose sender will latch it anyway"——但实际代码 line 103-108 又做了 latch（alert_q 粘性），与注释矛盾；(2) 对比 rom_ctrl_fsm.sv 的 alert_o = fsm_alert | checker_alert | unexpected_counter_change（组合逻辑，无 latch）——两模块的 alert 输出模式不一致；(3) 双重 latch 本身不产生功能错误（fatal alert 不可清除），但注释与实现不一致可能掩盖注入
- 建议验证型: 代码审计：确认注释与实现的一致性；若注释是原始设计意图（不 latch），则 line 103-108 的 latch 是注入候选

### CAND-rom_ctrl-08
- 疑点: rom_data_i 宽度硬编码为 32 位（rom_ctrl_fsm.sv:91），无法适应 DataWidth 参数变化——若未来 ROM 需要更宽数据（如 64 位），FSM 无法正确读取全部数据位
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl_fsm.sv:91
  ```systemverilog
  input logic [31:0]                 rom_data_i,
  ```
- lens: L4 结构lint
- 预言机依据: (1) rom_ctrl.sv:62 的 DataWidth 是参数化的（32 或 39），但 rom_ctrl_fsm#(RomDepth,7) 的 rom* 端口全部硬编码 32 位——参数化不一致；(2) rom_ctrl.sv:371 的连接 `checker_rom_rdata[31:0]` 显式截断，编译不报错但语义损失；(3) 属于结构级宽度不匹配，非安全漏洞但增加未来注入面
- 建议验证型: lint 级检查：对比 rom_ctrl_fsm 端口宽度与 rom_ctrl 中 DataWidth 参数

### CAND-rom_ctrl-09
- 疑点: rom_ctrl_mux.sv 的 rom_prince_addr_o 在 chk 路径下未连接——checker 侧不提供 prince 地址，rom_prince_addr_o 在 checker 模式下取 chk_addr_i（与 rom_rom_addr_o 相同），但 scrambled_rom 的两个地址端口（rom_addr_i, prince_addr_i）被设计为冗余且应独立传输以检测 fault
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl_mux.sv:122-124
  ```systemverilog
  assign rom_req_o         = mubi4_test_true_strict(sel_bus_i) ? bus_req_i         : chk_req_i;
  assign rom_rom_addr_o    = mubi4_test_true_strict(sel_bus_i) ? bus_rom_addr_i    : chk_addr_i;
  assign rom_prince_addr_o = mubi4_test_true_strict(sel_bus_i) ? bus_prince_addr_i : chk_addr_i;
  ```
- lens: L4 结构lint
- 预言机依据: (1) rom_ctrl_scrambled_rom.sv:17-22 注释 "These are expected to be connected to signals that are logically the same. The first is used as an input to the physical ROM index. The second is used when calculating the address-tweakable keystream. The trick is that you can mitigate fauhct-injection attacks that corrupt the address by splitting it somewhere upstream."——但在 checker 模式下两者相同（均来自 chk_addr_i），无冗余；(2) CTRL.REDUN SEC_CM (rom_ctrl.hjson:251) 声明 "Addresses from TL accesses are passed redundantly"——但这只覆盖 bus 侧，checker 侧地址无冗余保护；(3) checker 在 boot 阶段独占 ROM 读取——此期间地址 fault 注入无冗余检测
- 建议验证型: 时序 tb：在 checker 读取 ROM 期间注入地址 fault，观测 scrambled_rom 输出是否错误且未被检测

### CAND-rom_ctrl-10
- 疑点: rom_ctrl_fsm 的 `CHECKER.FSM.LOCAL_ESC` 实现 `if (alert_o) state_d = Invalid` 存在组合环路风险——alert_o 依赖 fsm_alert（依赖 state_d），state_d 又依赖 alert_o
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl_fsm.sv:242-244,351
  ```systemverilog
  // line 242-244 (in always_comb):
  if (alert_o) begin
    state_d = Invalid;
  end
  // line 351:
  assign alert_o = fsm_alert | checker_alert | unexpected_counter_change;
  // where fsm_alert = 1'b1 only in default branch of state_q case
  ```
- lens: L4 结构lint
- 预言机依据: (1) alert_o = fsm_alert | checker_alert | unexpected_counter_change；(2) fsm_alert 在 `default: fsm_alert = 1'b1` 分支置位，但该分支也设 `state_d = Invalid`；之后 line 242 `if (alert_o)` 再次设 `state_d = Invalid`——冗余但不矛盾；(3) unexpected_counter_change = mubi4_test_true_loose(in_state_done) & !counter_done——依赖 state_q（非 state_d），无环路；(4) checker_alert 来自子模块输出，不依赖 state_d；(5) 结论：无组合环路，但代码结构易误读，属于 lint 级可改进项
- 建议验证型: lint 级——非漏洞，记录供 correlator 降级

### CAND-rom_ctrl-11
- 疑点: FSM sparse 编码中 in_state_done 提取逻辑 `mubi4_t'(state_q_bits[3:0])` 依赖 FSM 枚举的低4位恰好等于 MuBi4True/MuBi4False——若 PRIM_FLOP_SPARSE_FSM 的实现改变了位映射（如加扰），此提取会静默错误
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl_fsm.sv:258-259
  ```systemverilog
  mubi4_t in_state_done;
  assign in_state_done = mubi4_t'(state_q_bits[3:0]);
  ```
- lens: L5 常量折叠
- 预言机依据: (1) Python 脚本验证（/tmp/rom_ctrl_fsm_check.py）：7 个 FSM 态的低4位——Done=0b1010=MuBi4True，其他6态=0b0101=MuBi4False——逻辑正确；(2) rom_ctrl_pkg.sv:49-57 的枚举定义保证此映射；(3) 但 PRIM_FLOP_SPARSE_FSM 可能对 state_q 做加扰存储（sparse encoding），此时 state_q_bits != 原始枚举值——需确认 PRIM_FLOP_SPARSE_FSM 的 q 输出是解码后还是原始编码；(4) 若为解码后（标准实现），则正确；若为加扰存储，则 in_state_done 静默错误且 INTERSIG.MUBI SEC_CM 失效
- 建议验证型: 脚本验证：读 PRIM_FLOP_SPARSE_FSM 实现，确认 q 输出为解码后枚举值

### CAND-rom_ctrl-12
- 疑点: scrambled_rom 的 PRINCE 参数（NumRoundsHalf=3, HalfwayDataReg=1, HalfwayKeyReg=1）和 prim_subst_perm 的 NumRounds=2 应与 scramble_image.py 的参考实现一致——需脚本化比对，禁心算
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl_scrambled_rom.sv:94-113
  ```systemverilog
  prim_subst_perm #(.DataWidth(Aw), .NumRounds(2), .Decrypt(0)) u_sp_addr (...);
  prim_prince #(.DataWidth(64), .KeyWidth(128), .NumRoundsHalf(3),
                .HalfwayDataReg(1'b1), .HalfwayKeyReg(1'b1)) u_prince (...);
  ```
- lens: L6 SCA结构
- 预言机依据: (1) rom_ctrl_scrambled_rom.sv:13 注释 "NumPrinceRoundsHalf = 3, NumDiffRounds = 2, NumAddrScrRounds = 2"；(2) 树内参考 #1 scramble_image.py 实现完整 scrambling（PRINCE + subst_perm + ECC）；(3) 注释声称 "follows the structure of prim_ram_1p_scr.sv"；(4) PRINCE 的 NumRoundsHalf=3 对应约 7 个有效 round——PRINCE 是 10-round cipher，NumRoundsHalf=3 表示 3 个正向 + round5 + 3 个逆向 = 7 effective rounds——这是标准 OT 选择；(5) 常量值与注释和参考实现描述一致，但需脚本化 bit-exact 比对 scramble_image.py 中的 PRINCE round 常量和 prim_subst_perm 的置换表
- 建议验证型: Python 脚本：从 scramble_image.py 提取 PRINCE/perm 参数，与 RTL localparam 比对

---

## 附：常量折叠脚本验证结果

### FSM 编码验证 (L5)
- 脚本: /tmp/rom_ctrl_fsm_check.py
- 结果: 7 态 Hamming distance min=3, max=8，符合 >=3 声明
- in_state_done 提取: 仅 Done 态低4位 = MuBi4True，其他 = MuBi4False — **正确**
- compare FSM 3 态 Hamming distance: 3, 3, 4 — **正确**，符合 >=3 声明

### rvalid 真值表验证 (L1)
- 脚本: /tmp/rom_ctrl_rvalid_check.py
- 结果: 当 `internal_alert=1, bus_rom_req=1` 时 `bus_rom_rvalid=1` — **违反 hjson 声明**
