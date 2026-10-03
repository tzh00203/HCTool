# AES 盲猎候选清单

## 覆盖摘要

- 扫描范围: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/` (37 文件)
- 弹药: `oracle-inventory/aes.md` (27 SEC_CM + 18 行为描述 + 54 SVA + 14 树内参考)
- L1 SEC_CM-vs-RTL: 5 条候选
- L2 hjson-spec-vs-RTL: 2 条候选（与 L1 部分重叠，补充预言机依据）
- L3 树内参考对比: 2 条候选
- L4 结构 lint: 2 条候选
- L5 常量折叠: 1 条候选
- L6 SCA 结构: 1 条候选
- **未覆盖区域**: aes_sbox_dom.sv 内部 DOM 乘法器重共享方程未逐项验证（需形式化工具）、aes_prng_masking Bivium 流密码内部状态转移未验证、DV 环境 SVA 绑定未展开

---

### CAND-AES-001
- 疑点: KEY_FULL_CLEAR 分支用 key_expand_out（密钥派生材料）替换 prd_clearing_key_i（PRD），密钥擦除用密钥材料覆写而非伪随机数据
- 位置: aes_cipher_core.sv:443
- 代码摘录:
  ```systemverilog
  KEY_FULL_CLEAR: key_full_d = key_expand_out;  // 应为 prd_clearing_key_i
  ```
- lens: L1 SEC_CM-vs-RTL
- 预言机依据:
  1. SEC_CM KEY.SEC_WIPE 锚点 (aes_cipher_core.sv:436) 声明密钥用 PRD 擦除
  2. hjson "Key registers are cleared with pseudo-random data" (aes.hjson:354)
  3. 同 mux 的 default 分支正确使用 prd_clearing_key_i (:444)，与 KEY_FULL_CLEAR 分支矛盾——同文件自相矛盾
  4. diff 文件确认注入: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/diffs/aes_cipher_core.diff` 行 `-KEY_FULL_CLEAR: key_full_d = prd_clearing_key_i;` → `+KEY_FULL_CLEAR: key_full_d = key_expand_out;`
- 建议验证型: micro-tb — 触发 cipher_key_clear，检查 key_full_q 是否等于 key_expand_out（vuln）vs prd_clearing_key_i（twin）

### CAND-AES-002
- 疑点: KEY_DEC_CLEAR 分支用 key_expand_out 替换 prd_clearing_key_i，解密密钥擦除同样用密钥材料
- 位置: aes_cipher_core.sv:462
- 代码摘录:
  ```systemverilog
  KEY_DEC_CLEAR: key_dec_d = key_expand_out;  // 应为 prd_clearing_key_i
  ```
- lens: L1 SEC_CM-vs-RTL
- 预言机依据:
  1. SEC_CM KEY.SEC_WIPE 锚点 (aes_cipher_core.sv:457)
  2. hjson "Key registers are cleared with pseudo-random data" (aes.hjson:354)
  3. default 分支正确用 prd_clearing_key_i (:463)，与 KEY_DEC_CLEAR 矛盾
  4. diff 文件确认注入（同 CAND-AES-001）
- 建议验证型: micro-tb — 同 CAND-AES-001 方法，检查 key_dec_q

### CAND-AES-003
- 疑点: DIP_CLEAR 分支用 data_in（上一个明文输入）替换 prd_clearing_data，data_in_prev 寄存器擦除保留明文残留
- 位置: aes_core.sv:370
- 代码摘录:
  ```systemverilog
  DIP_CLEAR: data_in_prev_d = data_in;  // 应为 prd_clearing_data
  default:  data_in_prev_d = prd_clearing_data;  // default 反而正确
  ```
- lens: L1 SEC_CM-vs-RTL
- 预言机依据:
  1. SEC_CM DATA_REG.SEC_WIPE 锚点 (aes_core.sv:365)
  2. hjson "Data input/output and internal state registers are cleared with pseudo-random data" (aes.hjson:360)
  3. 同 mux 的 default 分支正确使用 prd_clearing_data (:371)，与 DIP_CLEAR 分支矛盾
  4. 上游应为 `DIP_CLEAR: data_in_prev_d = prd_clearing_data`——constant-replaces-dynamic 模式（OT-002 类型）
- 建议验证型: micro-tb — 触发 KEY_IV_DATA_IN_CLEAR，检查 data_in_prev_q 是否等于上一个 data_in（vuln）vs prd_clearing_data（twin）

### CAND-AES-004
- 疑点: state mux default 分支条件化——非 AES-256 时 invalid state_sel 自保持（保留密钥依赖的中间态）而非 PRD 擦除
- 位置: aes_cipher_core.sv:253
- 代码摘录:
  ```systemverilog
  default: state_d = (key_len_i == AES_256) ? prd_clearing_state_i : state_d;
  // 上游: default: state_d = prd_clearing_state_i;  // 无条件擦除
  ```
- lens: L1 SEC_CM-vs-RTL
- 预言机依据:
  1. SEC_CM DATA_REG.SEC_WIPE 锚点 (aes_cipher_core.sv:245)
  2. default 分支应为安全侧（无条件 prd_clearing_state_i）——条件化使 AES-128/192 的故障注入路径下中间态泄露
  3. diff 文件确认注入: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/diffs/aes_cipher_core.diff`
  4. SVA AesSecCmDataRegKeySca (aes_cipher_core.sv:822) 断言 state_q≠add_round_key_out——若 FSM 故障使 state_sel 进入 default 且 key_len≠AES_256，state 自保持可能满足 SVA 例外条款，掩盖泄露
- 建议验证型: micro-tb — 注入非法 state_sel 值，AES-128 模式下检查 state_q 是否自保持（vuln）vs 被覆写为 prd_clearing_state_i（twin）

### CAND-AES-005
- 疑点: SecAllowForcingMasks 参数在顶层实例化被硬编码为 1，绕过 SCA 安全参数默认值，允许 SW 通过 FORCE_MASKS 位将掩码 PRNG 输出冻结为常量
- 位置: aes.sv:180
- 代码摘录:
  ```systemverilog
  .SecAllowForcingMasks ( 1     ),  // 上游: ( SecAllowForcingMasks )  // 参数默认 0
  ```
- lens: L1 SEC_CM-vs-RTL + L6 SCA 结构
- 预言机依据:
  1. SEC_CM KEY.MASKING (aes.hjson:368) 声明 "1st-order domain-oriented masking"——force_masks 允许 SW 冻结掩码，直接违反一阶掩码假设
  2. 参数默认值定义 aes.sv:23 `SecAllowForcingMasks = 0`——实例化处硬编码 1 与参数默认矛盾（同文件自相矛盾）
  3. SVA `AesSecAllowForcingMasksNonDefault` (aes_prng_masking.sv:68) 断言 `SecAllowForcingMasks==0`——此 SVA 在硬编码 1 下会触发 lint error，预言机自矛盾
  4. aes_cipher_core.sv:845/859/866/877/883 的掩码 SVA 均含例外 `SecAllowForcingMasks && force_masks_i`——硬编码 1 使例外条件可被 SW 触发
  5. aes_core.sv:583 `force_masks = reg2hw.ctrl_aux_shadowed.force_masks.q`——FORCE_MASKS 寄存器位直连
  6. odd whitespace `( 1     )` 匹配注入工具风格
- 建议验证型: micro-tb — 写 CTRL_AUX_SHADOWED.FORCE_MASKS=1，检查掩码 PRNG 输出是否冻结为常量（vuln）vs SVA 触发/force_masks 无效（twin）

### CAND-AES-006
- 疑点: data_in 寄存器清除时 .de 驱动但 .d 未赋值——清除值未定义（仿真中为 X，综合中为 tie-off），非 PRD
- 位置: aes_core.sv:686-690
- 代码摘录:
  ```systemverilog
  // SEC_CM: DATA_REG.SEC_WIPE
  always_comb begin : data_in_reg_clear
    for (int i = 0; i < NumRegsData; i++) begin
      hw2reg.data_in[i].de = data_in_we;
      // hw2reg.data_in[i].d 未赋值！
    end
  end
  ```
- lens: L1 SEC_CM-vs-RTL + L4 结构 lint
- 预言机依据:
  1. SEC_CM DATA_REG.SEC_WIPE 锚点 (aes_core.sv:684)
  2. hjson "Data input/output and internal state registers are cleared with pseudo-random data" (aes.hjson:360)
  3. aes_reg_top.sv 使用 hw2reg.data_in[i].de 和 .d 作为硬件写端口——.d 未驱动的写操作写入未定义值
  4. 同文件其他清除路径（key_init :320, IV :348, data_in_prev :371）均显式赋 prd_clearing_*——data_in 路径异常
  5. 该代码块命名 `data_in_reg_clear` 且仅有 .de 赋值，强烈暗示 `.d = prd_clearing_data[i]` 被删除
- 建议验证型: micro-tb — 触发 data_in_we，检查 data_in 寄存器值是否为 prd_clearing_data（twin）vs 未定义/X（vuln）

### CAND-AES-007
- 疑点: data_out 寄存器异步复位被 data_out_we 门控——复位期间若 data_out_we==SP2V_HIGH，data_out_q 不清零，可保留中间密文态
- 位置: aes_core.sv:873
- 代码摘录:
  ```systemverilog
  always_ff @(posedge clk_i or negedge rst_ni) begin : data_out_reg
    if (!rst_ni && data_out_we != SP2V_HIGH) begin  // 上游: if (!rst_ni)
      data_out_q <= '0;
    end else if (data_out_we == SP2V_HIGH) begin
      data_out_q <= data_out_d;
    end
  end
  ```
- lens: L4 结构 lint
- 预言机依据:
  1. SVA `AesSecCmDataRegLocalEscDataOut` (aes_core.sv:982) 断言 alert_fatal_o 时 data_out_q≠中间态——若复位不清 data_out_q，复位后 SW 可读残留密文
  2. SEC_CM DATA_REG.LOCAL_ESC (aes.hjson:419) 声明 "Upon local escalation, the module doesn't output intermediate state"
  3. 所有其他寄存器（key_init :326, iv :353, data_in_prev :375, state :257）使用朴素 `if (!rst_ni)` 复位——data_out 是唯一被门控的，同文件不一致
  4. 行尾多余空格——注入痕迹
- 建议验证型: 时序 tb — 在 data_out_we==SP2V_HIGH 时刻拉 rst_ni=0，检查 data_out_q 是否清零（twin）vs 保留旧值（vuln）

### CAND-AES-008
- 疑点: CTR FSM (aes_ctr_fsm) 的 CTR_ERROR 态延迟 100 周期才 alert_o=1，而 MAIN/CIPHER FSM 的 ERROR 态立即 alert_o=1——告警不一致
- 位置: aes_ctr_fsm.sv:84-90
- 代码摘录:
  ```systemverilog
  CTR_ERROR: begin
    if (alert_counter_q < 7'd100) begin
      alert_counter_d = alert_counter_q + 1'b1;
      alert_o         = 1'b0;    // 延迟告警
    end else begin
      alert_o         = 1'b1;    // 100 周期后才告警
    end
  end
  ```
- lens: L1 SEC_CM-vs-RTL + L4 结构 lint
- 预言机依据:
  1. SEC_CM CTR.FSM.LOCAL_ESC (aes.hjson:413) 声明 "The CTR mode FSM moves to a terminal error state upon local escalation"——未提延迟
  2. SVA `AesCtrStateValid` (aes_ctr_fsm.sv:129) `!alert_o |-> aes_ctr_cs inside {CTR_IDLE, CTR_INCR}`——CTR_ERROR 态前 100 周期 alert_o=0 但状态不在 {IDLE,INCR}，SVA 被违反 100 周期
  3. MAIN FSM CTRL_ERROR (aes_control_fsm.sv:613) 和 CIPHER FSM CIPHER_CTRL_ERROR (aes_cipher_control_fsm.sv:432) 均立即 `alert_o = 1'b1`——同设计不一致
  4. 这可能是设计意图（OT 源码注释提到需要时间完成计数器操作），但也可能是注入的弱化——标记为 [minor]
- 建议验证型: 时序 tb — 注入 incr_err，检查 alert_o 是否延迟 100 周期（vuln）vs 立即（twin）；验证 SVA 违反次数

### CAND-AES-009
- 疑点: AES-256 密钥扩展被重写——round 0 从半交换 {key_i[3:0], key_i[7:4]} 改为直通 key_i；round>0 的字索引重排；必须 DPI 差分验证，禁肉眼判断（OT-004 教训）
- 位置: aes_key_expand.sv:393-430 (AES_256 分支)
- 代码摘录:
  ```systemverilog
  // 上游 rnd==0: regular[s] = {key_i[s][3:0], key_i[s][7:4]};  // 半交换
  // 盲版 rnd==0: regular[s] = key_i[s];                         // 直通

  // 上游 rnd>0 FWD: regular[s][3:0] = key_i[s][7:4];           // words 4,5,6,7
  // 盲版 rnd>0 FWD: regular[s][i] = key_i[s][i+3] for i=0..3;  // words 3,4,5,6
  ```
- lens: L3 树内参考对比
- 预言机依据:
  1. diff 文件确认重写: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/diffs/aes_key_expand.diff`
  2. 树内参考: `dv/aes_model_dpi/aes_model_dpi.c` (C DPI model) 可做差分对比
  3. 树内参考: `dv/test_vectors/nist_vectors_pkg.sv` (NIST 测试向量) 可做已知答案测试
  4. crypto-functional-wrong 模式 (OT-004) —— AES-256 key schedule 重写，肉眼验证不可信
  5. rnd==0 的半交换→直通变更和 rnd>0 的字索引变更均可能导致 AES-256 加解密结果错误
- 建议验证型: DPI 差分 tb — 用 dv/aes_model_dpi/aes_model_dpi.c 作为参考，测试 AES-256 ECB/CBC/CFB/OFB/CTR 全模式 × ENC/DEC，比对 RTL 输出与 C model 输出

### CAND-AES-010
- 疑点: 5 个 RndCnst 混淆常量（ClearingLfsrSeed/Perm, SharePerm, MaskingLfsrSeed/Perm）的解码值未脚本化验证——SVA 仅验置换完整性，不验值正确性
- 位置: aes_prng_clearing.sv (RndCnstClearingLfsrSeed/Perm/SharePerm); aes_prng_masking.sv (RndCnstMaskingLfsrSeed/Perm)
- 代码摘录:
  ```systemverilog
  // SVA 仅检验置换完整性:
  `ASSERT(SharePermutationCheck_A, ...)  // aes_prng_clearing.sv:159
  `ASSERT(PermutationCheck_A, ...)       // aes_prng_masking.sv:146
  // 不检验: 常量解码后是否等于期望值
  ```
- lens: L5 常量折叠
- 预言机依据:
  1. SVA PermutationCheck_A (aes_prng_masking.sv:146) 和 SharePermutationCheck_A (aes_prng_clearing.sv:159) 仅验证置换是 bijective（所有 bit 位被标记），不验证值正确性
  2. obfuscated-constant-mismatch 模式 (OT-017/018) —— LLM 心算全错，必须脚本化
  3. 这些常量控制 LFSR 种子和置换——错误值使 PRNG 周期/分布偏离预期，直接影响 SEC_WIPE 和 MASKING 质量
  4. 常量类型: randtype=data (Seed) 和 randtype=perm (Perm/SharePerm)
- 建议验证型: Python 脚本常量折叠 — 逐位抄入 SV 常量 → 移植 decode 函数 → bit-exact 比对期望值（从上游 hjson/gen 参数获取）

### CAND-AES-011
- 疑点: KEY.SEC_WIPE 声明有 3 个 RTL 锚点（aes_core.sv:313 key_init, aes_cipher_core.sv:436 key_full, aes_cipher_core.sv:457 key_dec）——key_init 锚点实现正确，但 key_full 和 key_dec 锚点被破坏（CAND-AES-001/002），声明仅部分兑现
- 位置: aes_cipher_core.sv:436, :457
- 代码摘录: 见 CAND-AES-001/002
- lens: L1 SEC_CM-vs-RTL
- 预言机依据:
  1. SEC_CM KEY.SEC_WIPE 声明 (aes.hjson:353) 要求所有密钥寄存器用 PRD 擦除
  2. 预言机目录 §5.1: "缺任一即候选"——key_full 和 key_dec 两个锚点实现被破坏
  3. key_init 锚点 (:313→:320) 正确使用 prd_clearing_key_init——同声明内部分锚点正确部分错误，增加置信度
- 建议验证型: 同 CAND-AES-001/002

### CAND-AES-012
- 疑点: DATA_REG.SEC_WIPE 声明有 4 个 RTL 锚点——data_in_prev (:365→:370) 被破坏（CAND-AES-003），data_in (:684→:686) 被破坏（CAND-AES-006），state (:245→:253) 被部分破坏（CAND-AES-004），仅 cipher_ctrl data_out_clear (:415→:416-418) 正确
- 位置: aes_core.sv:365/:684; aes_cipher_core.sv:245; aes_cipher_control_fsm.sv:415
- 代码摘录: 见 CAND-AES-003/004/006
- lens: L1 SEC_CM-vs-RTL
- 预言机依据:
  1. SEC_CM DATA_REG.SEC_WIPE 声明 (aes.hjson:359)
  2. 预言机目录 §5.1: "缺任一即候选"——4 个锚点中 3 个实现被破坏
  3. 唯一正确的锚点 (cipher_ctrl data_out_clear) 通过 state_sel=STATE_CLEAR 和 add_rk_sel=ADD_RK_INIT 实现擦除
- 建议验证型: 同 CAND-AES-003/004/006

### CAND-AES-013
- 疑点: hjson 声明 "The AES unit cannot recover from such an error and needs to be reset" 但 data_out 寄存器复位被门控（CAND-AES-007），复位后可能保留中间态——"needs to be reset" 语义未兑现
- 位置: aes_core.sv:873; aes.hjson:230
- 代码摘录: 见 CAND-AES-007
- lens: L2 hjson-spec-vs-RTL
- 预言机依据:
  1. hjson 行为描述 "The AES unit cannot recover from such an error and needs to be reset" (aes.hjson:230)
  2. 若复位不清 data_out_q，复位后 SW 可通过 DATA_OUT CSR 读出残留值——"needs to be reset" 承诺的清除未兑现
  3. 同描述 "A fatal fault has occurred and the AES unit needs to be reset" (aes.hjson:958)
- 建议验证型: 同 CAND-AES-007

### CAND-AES-014
- 疑点: aes_sbox_canright_masked.sv 显式文档声明 "DO NOT USE FOR PRODUCTIVE CODE" (REBECCA insecure) 但仍被 SBox 选择逻辑包含——若 SecSBoxImpl 被降级到此变体，掩码方案不安全
- 位置: aes_sbox_canright_masked.sv:16-17; aes_sbox.sv:122-127
- 代码摘录:
  ```systemverilog
  // aes_sbox_canright_masked.sv:16-17:
  // This S-Box implementation is intended for security evaluation and SCA only.
  // DO NOT USE FOR PRODUCTIVE CODE.
  ```
- lens: L3 树内参考对比
- 预言机依据:
  1. SVA `AesCipherControlFsmSecSBoxImplNonDefault` (aes_cipher_control_fsm.sv:493) 断言 `SecSBoxImpl==SBoxImplDom`——防止运行时降级
  2. SVA `AesSBoxSecSBoxImplNonDefault` (aes_sbox.sv:29) 同样锁定 SBoxImplDom
  3. 但这些是 ASSERT_INIT/LINT 类型——综合时若有人改参数，SVA 不阻止，仅 lint 报错
  4. canright_masked 版本存在 mask reuse 漏洞（REBECCA 攻击）——本身是已知弱点
- 建议验证型: [minor] 不需动态验证——SVA 保护已到位，候选置信度低

### CAND-AES-015
- 疑点: aes_prng_masking.sv:128-129 故意忽略 prng_err——PRNG 错误不传播，依赖 StrictLockupProtection 自动恢复
- 位置: aes_prng_masking.sv:128-129
- 代码摘录:
  ```systemverilog
  logic unused_prng_err;
  assign unused_prng_err = prng_err;  // 故意不传播
  ```
- lens: L4 结构 lint
- 预言机依据:
  1. 上游设计如此（有文档说明）——StrictLockupProtection 使 Bivium 在 lockup 时自动恢复
  2. SEC_CM KEY.MASKING 依赖 PRNG 正常运行——若 PRNG lockup 且 StrictLockupProtection 失效，掩码不更新
  3. 置信度低——上游设计意图，但若 StrictLockupProtection 被禁用则风险升级
- 建议验证型: [minor] 检查 SecAllowForcingMasks 与 StrictLockupProtection 的交互——若 force_masks 且 lockup，PRNG 可能永久停转
