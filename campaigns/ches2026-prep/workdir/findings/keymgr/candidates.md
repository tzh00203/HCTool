# keymgr 候选漏洞清单

## 覆盖摘要

- 扫描文件：keymgr.sv, keymgr_ctrl.sv, keymgr_data_en_state.sv, keymgr_kmac_if.sv, keymgr_op_state_ctrl.sv, keymgr_sideload_key_ctrl.sv, keymgr_sideload_key.sv, keymgr_err.sv, keymgr_input_checks.sv, keymgr_cfg_en.sv, keymgr_reseed_ctrl.sv, keymgr_pkg.sv, keymgr_reg_top.sv
- L1 SEC_CM-vs-RTL: 2 条候选（CAND-001, CAND-002）
- L2 hjson-spec-vs-RTL: 1 条候选（CAND-001 二次佐证 + CAND-003）
- L3 树内参考对比: 1 条候选（CAND-002 兄弟模块对照）
- L4 结构 lint: 1 条候选（CAND-002 default 分支 + CAND-004）
- L5 常量折叠: 0 条（keymgr 无混淆常量，RndCnst 均为明文 hex）
- L6 SCA 结构: 1 条候选（CAND-005）
- 未覆盖区域：keymgr_reg_pkg.sv（自动生成，无人工注入空间）、keymgr_reseed_ctrl.sv EDN 交互（需动态验证）

---

### CAND-keymgr-001
- 疑点: key_output_ctrl 在 StCtrlInvalid 态跳过 entropy XOR，直接暴露 key_state_q 原值
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_ctrl.sv:289-297
- 代码摘录:
  ```systemverilog
  // Subtle bug: During invalid states, expose unmasked key material
  // by skipping the entropy XOR when certain conditions are met
  if (invalid_stage_sel_o && (state_q == StCtrlInvalid)) begin
    key_o.key[i] = key_state_q[cdi_sel_o][i];  // <-- NO entropy masking!
  end else begin
    key_o.key[i] = invalid_stage_sel_o ?
                   {EntropyRounds{entropy_i[i]}} :  // normal: mask with entropy
                   key_state_q[cdi_sel_o][i];
  end
  ```
- lens: L1 (SEC_CM-vs-RTL) + L2 (hjson-spec-vs-RTL)
- 预言机依据:
  1. **行内注释**（keymgr_ctrl.sv:289-290）明确标注 "Subtle bug: expose unmasked key material"——这是注入标记
  2. **theory_of_operation.md:33** 声明 "Invalid states... supplies random data when invoked"——RTL 在 StCtrlInvalid 暴露的是 key_state_q 而非 random data，与规范矛盾
  3. **SEC_CM OUTPUT_KEYS.CTRL.REDUN**（keymgr.hjson:376）声称 "Software and sideload keys are redundantly controlled"——此分支跳过了 entropy 冗余控制
  4. **结构推理**：StCtrlInvalid 中 stage_sel_o 默认为 Disable（line 484 未覆盖），故 invalid_stage_sel_o 恒为 1；加上 state_q==StCtrlInvalid 恒成立，因此该分支**每个周期**都暴露 unmasked key，而非仅 SW 发命令时
  5. **SVA DataEn_A**（keymgr_ctrl.sv:907）约束 `data_hw_en_o | data_sw_en_o |-> (id_en_o | gen_en_o) & ~adv_en_o`，但 StCtrlInvalid 中 data_en 全零，SVA 不覆盖 key_o.key 端口泄露路径
- 建议验证型: 组合 micro-tb。构造：置 state_q=StCtrlInvalid + invalid_stage_sel_o=1 + key_state_q!=0，检查 key_o.key 是否等于 key_state_q（vuln）vs entropy（twin）。纯组合逻辑，10 分钟可建。

---

### CAND-keymgr-002
- 疑点: data_en_state FSM 的 default 分支不设 fsm_err_o，与其他 4 个 FSM 不一致——FSM 错误不触发 AsyncFaultFsmIntg 告警
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_data_en_state.sv:127-129
- 代码摘录:
  ```systemverilog
  default: begin
    state_d = StCtrlDataDis;   // <-- NO fsm_err_o = 1'b1!
  end
  ```
  对比其他 FSM：
  - keymgr_ctrl.sv:682-684: `state_intg_err_d = 1'b1; state_d = StCtrlWipe;`
  - keymgr_kmac_if.sv:269-273: `fsm_error_o = 1'b1;`
  - keymgr_op_state_ctrl.sv:100-104: `op_fsm_err_o = 1'b1;`
  - keymgr_sideload_key_ctrl.sv:124-126: `fsm_err_o = 1'b1;`
- lens: L1 (SEC_CM-vs-RTL) + L3 (树内参考对比) + L4 (结构 lint)
- 预言机依据:
  1. **兄弟模块一致性**：keymgr 内 5 个独立 FSM 中，data_en_state 是唯一不在 default 分支设 error 的——结构性异常
  2. **SEC_CM DATA.FSM.SPARSE**（keymgr.hjson:397）声明该 FSM 用稀疏编码，默认分支应触发错误——RTL 未兑现
  3. **错误传播链断裂**：fsm_err_o=0 → keymgr_ctrl.data_fsm_err=0 → keymgr_err.async_fault_d[AsyncFaultFsmIntg]=0 → inv_state 不触发 → 主 FSM 不升级到 StCtrlInvalid → 无 fatal alert
  4. **SVA CtrlDataFsmCheck_A**（keymgr.sv:798-799）仅检查 PRIM_FLOP_SPARSE_FSM 原语的 err_o，不覆盖模块级 default 分支错误——两层检测有缝隙
  5. **安全侧分析**：default 分支将 data_hw_en_o/data_sw_en_o 保持为 0（安全侧），但缺少告警意味着系统不知道 FSM 出错，不采取进一步防护（不擦密钥、不进 Invalid 态）
- 建议验证型: 组合 micro-tb。构造：注入 sparse FSM 故障使 data_en 进入 default 态，检查（a）fsm_err_o 是否为 1（vuln=0, twin=1），（b）async_fault 是否传播到 alert（vuln 无, twin 有）。另可构造时序 tb 用 $onehot 检查 state_q 落在合法枚举外时 fsm_err_o 的行为。

---

### CAND-keymgr-003
- 疑点: CTRL.FSM.CONSISTENCY SEC_CM 锚点在 keymgr_err.sv 而非 keymgr_ctrl.sv，声明与实现跨模块
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_err.sv:124（锚点）vs keymgr_ctrl.sv:833,778（信号源）
- 代码摘录:
  ```systemverilog
  // keymgr_err.sv:124
  // SEC_CM: CTRL.FSM.CONSISTENCY
  assign async_fault_d[AsyncFaultFsmChk] = state_change_err_i | op_state_cmd_err_i;

  // keymgr_ctrl.sv:833
  logic state_change_err;
  assign state_change_err = vld_state_change_q & !adv_op;

  // keymgr_ctrl.sv:778
  logic op_state_cmd_err;
  assign op_state_cmd_err = (adv_en_o & ~(advance_sel | disable_sel)) |
                            (gen_en_o & ~gen_op);
  ```
- lens: L1 (SEC_CM-vs-RTL) + L4 (结构 lint)
- 预言机依据:
  1. **SEC_CM 声明** CTRL.FSM.CONSISTENCY 在 keymgr.hjson:409，锚点在 keymgr_err.sv:124
  2. **跨模块依赖**：state_change_err 和 op_state_cmd_err 的定义在 keymgr_ctrl.sv，但 SEC_CM 注释锚点在 keymgr_err.sv——修改 ctrl 的信号定义不会更新 err 的锚点
  3. **与其他 SEC_CM 对比**：CTRL.FSM.SPARSE 锚点在同文件同模块（keymgr_ctrl.sv:260），CTRL.FSM.LOCAL_ESC 也在同文件（keymgr_ctrl.sv:462）；唯有 CONSISTENCY 跨模块
  4. **脆弱性**：若注入者修改 keymgr_ctrl.sv 的 state_change_err 或 op_state_cmd_err 逻辑（如削弱条件），SEC_CM 锚点在另一文件不会同步提醒审查者
- 建议验证型: 人工审查或 grep 脚本：提取 keymgr_err.sv:124 的 state_change_err_i / op_state_cmd_err_i 定义，确认与 keymgr_ctrl.sv 的信号源 bit-exact 匹配。组合 micro-tb 验证 state_change_err 在非 advance 状态变化时是否正确触发。

---

### CAND-keymgr-004
- 疑点: op_update_sel 在 invalid 状态选用 KeyUpdateKmac——若 op_ack 与 inv_state 同周期到达，存在一键宽窗口允许 KMAC 结果写入 key_state
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_ctrl.sv:784
- 代码摘录:
  ```systemverilog
  assign op_update_sel = (op_ack | op_update) & invalid      ? KeyUpdateKmac :
                         (op_ack | op_update) & op_fault_err ? KeyUpdateWipe :
                         (op_ack | op_update) & disabled     ? KeyUpdateKmac :
                         (op_ack | op_update) & op_err       ? KeyUpdateIdle :
                         (op_ack | op_update)                ? KeyUpdateKmac : KeyUpdateIdle;
  ```
- lens: L2 (hjson-spec-vs-RTL)
- 预言机依据:
  1. **hjson 行为描述**（keymgr.hjson:405）："When a fault is detected... the fsm transitions to invalid state to prevent further legal operations"——invalid 态应阻止操作，但 KeyUpdateKmac 允许 KMAC 结果更新 key_state
  2. **竞争窗口**：inv_state 是组合逻辑（|fault_o），op_ack 来自 op_state_ctrl 寄存器输出——同周期可同时为 1；此时 update_sel 优先级链中 wipe_req=random_req=init_o=0，op_update_sel=KeyUpdateKmac 生效
  3. **缓解因素**：下一周期主 FSM 进入 StCtrlWipe，wipe_req=1 覆写 key_state；且 key_output_ctrl 在 invalid_stage_sel_o=1 时正常路径用 entropy 掩码——但 CAND-keymgr-001 漏洞使 StCtrlInvalid 态跳过掩码
  4. **CAND-keymgr-001 联动**：若一键窗口中 key_state 被 KMAC 结果更新，然后进入 StCtrlInvalid，key_output_ctrl 的 bug 分支暴露的是该 KMAC 结果而非已被 wipe 的 entropy 值
- 建议验证型: 时序 tb。构造：启动 advance 操作 → 在 kmac_done 到达同一周期注入 async fault → 检查 key_state_d 是否被 kmac_data_i 更新（vuln 有, twin 无因 op_fault_err 路径）。需同步驱动 fault 和 op_done。

---

### CAND-keymgr-005
- 疑点: gen_in decoy 路径用原始 lfsr[31:0] 而非经 perm_data 置换的 data_rand，减弱 decoy 随机化
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr.sv:490-493
- 代码摘录:
  ```systemverilog
  assign gen_in = invalid_stage_sel ? {GenLfsrCopies{lfsr[31:0]}} : {reg2hw.key_version,
                                                                     reg2hw.salt,
                                                                     dest_seed,
                                                                     output_key};
  // 对比 ctrl_rand/data_rand:
  assign ctrl_rand[0] = lfsr[63:32];
  assign ctrl_rand[1] = perm_data(lfsr[31:0], RndCnstRandPerm);  // permuted
  assign data_rand[0] = lfsr[31:0];
  assign data_rand[1] = perm_data(lfsr[63:32], RndCnstRandPerm); // permuted
  ```
- lens: L6 (SCA 结构)
- 预言机依据:
  1. **兄弟路径对比**：ctrl_rand[1] 和 data_rand[1] 均用 perm_data 置换，gen_in decoy 直接用 lfsr[31:0] 无置换——与同文件其他随机化路径不一致
  2. **SCA 影响**：decoy 数据的目的是在无效操作时填充 KMAC 输入以掩盖有效操作的功耗特征；未置换的 lfsr 输出与置换版本在 Hamming weight 分布上可能不同，提供额外区分维度
  3. **kmac_if decoy**：keymgr_kmac_if.sv:319-320 的 decoy_data 用 `perm_data(entropy_i[1], RndCnstRandPerm)` 置换——gen_in decoy 与 kmac_if decoy 置换策略不一致
  4. **缓解因素**：LFSR 本身已有非线性输出（NonLinearOut=1），且仅影响 decoy 路径（invalid_stage_sel=1 时），不影响有效数据通路
- 建议验证型: 时序 tb + SCA 差分。构造：运行 GenHwOut 有效操作 vs invalid_stage_sel decoy 操作，采集 gen_in 端口的 Hamming weight/距离分布，对比 lfsr[31:0] 直接使用 vs perm_data 置换版本的统计差异。

---

### CAND-keymgr-006
- 疑点: StCtrlInvalid 态 key_o.valid=0 但 key_o.key 端口持续携带 key_state_q 原值——物理端口泄露
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_ctrl.sv:279 + 291-292
- 代码摘录:
  ```systemverilog
  // line 279
  key_o.valid = op_req;   // op_req=0 in StCtrlInvalid

  // line 291-292 (due to CAND-keymgr-001 bug)
  if (invalid_stage_sel_o && (state_q == StCtrlInvalid)) begin
    key_o.key[i] = key_state_q[cdi_sel_o][i];  // raw key on port despite valid=0
  end
  ```
- lens: L2 (hjson-spec-vs-RTL) + L6 (SCA 结构)
- 预言机依据:
  1. **CAND-keymgr-001 的延伸**：key_o.valid=0 意味下游消费者（sideload_key_ctrl）不使用该 key，但物理端口值仍存在——EM/功耗侧信道可观测
  2. **theory_of_operation.md:33** 声明 "supplies random data"——物理端口应输出 entropy 而非 key_state_q
  3. **对比正常路径**：当 invalid_stage_sel_o=1 且 state_q!=StCtrlInvalid 时，key_o.key = entropy（masked）；仅在 StCtrlInvalid 跳过 masking——这创造了 StCtrlInvalid 态独有的 SCA 签名
  4. **SVA LoadKey_A**（keymgr_ctrl.sv:897）仅约束 `key_o.valid |-> op_start_i`，不约束 key_o.key 在 valid=0 时的值——SVA 覆盖缺口
- 建议验证型: 同 CAND-keymgr-001 的组合 micro-tb。额外加 SCA 观测：在 StCtrlInvalid 态对 key_o.key 端口做 Hamming distance 分析，对比 vuln（key_state_q 原值，非零）vs twin（entropy 覆写，随机）。

---

### CAND-keymgr-007
- 疑点: data_en_state FSM default 分支跳转到 StCtrlDataDis 而非 StCtrlDataInvalid——错误态未进入专门的 invalid 态
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_data_en_state.sv:57-64 + 127-129
- 代码摘录:
  ```systemverilog
  // 枚举定义含 StCtrlDataInvalid (line 63)
  StCtrlDataInvalid = 10'b1111001001

  // 但 default 分支不使用它
  default: begin
    state_d = StCtrlDataDis;   // should be StCtrlDataInvalid + fsm_err_o=1
  end
  ```
- lens: L4 (结构 lint)
- 预言机依据:
  1. **枚举定义存在 StCtrlDataInvalid**——设计者预留了 invalid 态，但 default 分支没有使用它，跳转到了 StCtrlDataDis（正常禁用态）
  2. **StCtrlDataDis 语义**：该态等待 op_done_i 后进入 StCtrlDataWait → StCtrlDataIdle——这是正常操作完成后的恢复路径，不是错误恢复路径
  3. **错误态混入正常态**：如果 FSM 因故障进入 default，跳转到 StCtrlDataDis 后会在 op_done 时恢复到 idle——表面上"自愈"，但实际掩盖了 FSM 故障，且 keymgr_err 不知道发生了错误
  4. **对比 ctrl FSM**：keymgr_ctrl default 分支跳转 StCtrlWipe → StCtrlInvalid（不可恢复终态），不跳正常态——data_en FSM 的"自愈"行为与安全设计哲学矛盾
- 建议验证型: 时序 tb。注入 sparse FSM 故障使 data_en 进入 default → 观察 state_d 是否为 StCtrlDataInvalid（vuln=StCtrlDataDis, twin=StCtrlDataInvalid）+ fsm_err_o 是否为 1（vuln=0, twin=1）+ 是否触发 async fault alert。

---

### CAND-keymgr-008
- 疑点: KeyUpdateKmac 路径中 adv_op||dis_op 条件使 advance 操作的 KMAC 结果覆盖 key_state，但 advance 应该更新 key_state 到下一阶段——语义可能正确但条件与 CDI 逻辑交互需验证
- 位置: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_ctrl.sv:402-405
- 代码摘录:
  ```systemverilog
  KeyUpdateKmac: begin
    data_valid_o = gen_op;
    key_state_d[cdi_sel_o] = (adv_op || dis_op) ? kmac_data_i : key_state_q[cdi_sel_o];
  end
  ```
- lens: L2 (hjson-spec-vs-RTL)
- 预言机依据:
  1. **hjson 描述**（keymgr.hjson:565 area around OPERATION descriptions）：advance 操作应"derive the next key state"——KMAC 结果覆盖 key_state 符合预期
  2. **存疑点**：`adv_op || dis_op` 条件中，dis_op（disable 操作）也用 KMAC 结果覆盖 key_state——但 disable 操作的目标是进入 Disabled 态，KMAC 计算的输出（随机化值）写入 key_state 是否必要？disable 操作在 StCtrlOwnerKey:631-635 中 `stage_sel_o = Disable | advance_sel ? Disable : Owner`，所以 disable 时 stage_sel=Disable, invalid_stage_sel=1，KMAC 的输入是 random/decoy 数据
  3. **gen_op 时不更新**：`data_valid_o = gen_op` 但 `key_state_d = key_state_q`——generate 操作不更新 key_state，只产生输出。这是正确的 DICE 行为（generate 不改变 CDI 状态）
  4. **单一依据，存疑**——dis_op 时写入 KMAC decoy 结果的行为可能是设计意图（disable 时仍需随机化 key_state），也可能是冗余操作
- 建议验证型: 人工审查 + 组合 micro-tb。检查 dis_op 时 kmac_data_i 的内容（应为 decoy/random），验证写入 key_state 后是否影响后续行为（StCtrlDisabled 中 key_state 不会被使用，所以写入 decoy 无害）。

---

## 候选统计

| 编号 | 疑点 | lens | 预言机数 | 预估等级 |
|---|---|---|---|---|
| CAND-keymgr-001 | key_output_ctrl unmasked key in StCtrlInvalid | L1+L2 | 5 | major |
| CAND-keymgr-002 | data_en_state default 缺 fsm_err_o | L1+L3+L4 | 5 | major |
| CAND-keymgr-003 | CTRL.FSM.CONSISTENCY 锚点跨模块 | L1+L4 | 4 | minor |
| CAND-keymgr-004 | op_update_sel invalid 竞争窗口 | L2 | 4 | minor |
| CAND-keymgr-005 | gen_in decoy 未置换 | L6 | 4 | minor |
| CAND-keymgr-006 | StCtrlInvalid key_o.key 物理泄露 | L2+L6 | 4 | major |
| CAND-keymgr-007 | data_en default 跳正常态非 invalid 态 | L4 | 4 | major |
| CAND-keymgr-008 | KeyUpdateKmac dis_op 覆写语义 | L2 | 4 | minor |
