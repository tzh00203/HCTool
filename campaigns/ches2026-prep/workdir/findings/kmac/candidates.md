# KMAC Blind Hunt — Candidate Findings

## 覆盖摘要

- 扫描文件: kmac.sv (1597L), kmac_core.sv (483L), kmac_app.sv (911L),
  kmac_entropy.sv (778L), kmac_errchk.sv (464L), kmac_msgfifo.sv (284L),
  kmac_reduced.sv (312L), kmac_reg_top.sv (3326L), kmac_reg_pkg.sv (502L),
  kmac_staterd.sv (126L), kmac_pkg.sv (477L), sha3_pkg.sv (294L),
  sha3.sv (532L), sha3pad.sv (884L), keccak_round.sv (611L), keccak_2share.sv (563L)
- 每个lens产出: L1=4, L2=1, L3=1(与L1重叠), L4=1, L5=0, L6=2
- 未覆盖区域: kmac_reg_pkg.sv 仅做参数/枚举速查（非数据通路）;
  keccak_2share.sv DOM乘法器内部未逐行审计（留作SCA DPI验证）

---

### CAND-kmac-01
- 疑点: MSG.MASKING 用全1常量替换LFSR动态掩码，破坏SCA一阶掩码对策
- 位置: kmac.sv:906-927
  ```systemverilog
  assign static_mask = {MsgWidth{1'b1}};              // line 911
  msg_mask_permuted[i] = static_mask[RndCnstMsgPerm[i]]; // line 919 → 恒1
  msg_data_masked[i] = msg_data[i] ^
                    ({MsgWidth{cfg_msg_mask}} & static_mask); // line 925-926
  ```
- lens: L1 (SEC_CM-vs-RTL) + L3 (树内参考对比)
- 预言机依据:
  1. **树内参考实现 kmac_reduced.sv:152-166** 正确用动态掩码:
     `msg_mask_permuted[i] = msg_mask[RndCnstMsgPerm[i]]` 和
     `msg_masked[i] = msg[i] ^ ({MsgWidth{msg_mask_en_i}} & msg_mask_permuted)`
  2. **hjson 行为描述** (kmac.hjson:558-565): "Message Masking with PRNG.
     If 1, KMAC applies PRNG to the input messages" — RTL用常量全1而非PRNG，直接矛盾
  3. **constant-replaces-dynamic 模式** (OT-006 GT实例): LFSR输出被常量替换，
     PRNG实例仍存在但输出不消耗（dangling PRNG）
  4. **msg_mask 信号悬空**: kmac.sv:313 声明 `msg_mask`，line 1298 连接
     `kmac_entropy.msg_mask_o(msg_mask)`，但 g_msg_mask 块(line 906-927)
     从未引用 msg_mask——PRNG计算了但被丢弃
  5. **RndCnstMsgPerm 排列退化为no-op**: 对全1向量做任意排列仍为全1
- 建议验证型: DPI差分（vuln kmac.sv vs twin kmac_reduced.sv掩码逻辑）;
  时序tb：注入相同消息，XMR-probe msg_data_masked，vuln=确定性取反，twin=PRNG随机

---

### CAND-kmac-02
- 疑点: sha3pad SVA Sequence_a 被注释，命令序列合同未强制执行
- 位置: sha3pad.sv:769
  ```systemverilog
  //`ASSUME(Sequence_a, start_i ##[1:$] process_i ##[1:$] ##[1:$] absorbed_o ##[1:$] done_i)
  ```
- lens: L1 (SEC_CM-vs-RTL) + L2 (hjson-spec-vs-RTL)
- 预言机依据:
  1. **SVA in-file 是最强预言机** (hunter方法论): 注释断言 = 合同降级
  2. 注释内容约束 `start→process→absorbed→done` 序列，去掉后 RTL 不强制此顺序
  3. kmac_errchk 模块部分补位（检查命令序列错误），但仅在 SW 命令路径；
     若通过 App 接口或 FI 改变命令顺序，sha3pad 层无此约束
- 建议验证型: 组合micro-tb：先发 process 再发 start，检查 sha3pad 是否进入
  非预期状态（vuln 可能接受，twin 被 SVA 拒绝）

---

### CAND-kmac-03
- 疑点: kmac_core StTerminalError 延迟100周期才置 sparse_fsm_error_o，
     其他FSM立即置1，违反 FSM.LOCAL_ESC 即时告警语义
- 位置: kmac_core.sv:227-235
  ```systemverilog
  StTerminalError: begin
    st_d = st;
    if (st_err_ct < 8'd100) begin
      st_err_ct_d = st_err_ct + 1'b 1;
      sparse_fsm_error_o = 1'b 0;        // line 232: 延迟期不报错
    end else begin
      sparse_fsm_error_o = 1'b 1;        // line 234: 100周期后才报
    end
  end
  ```
- lens: L1 (SEC_CM-vs-RTL)
- 预言机依据:
  1. **SEC_CM FSM.LOCAL_ESC 声明** (kmac.hjson:330-332): "Local fatal faults
     move all sparse FSMs into an invalid state" — 未提及延迟
  2. **对比同IP内其他5个FSM**:
     - kmac_app.sv:552-555 StTerminalError → `sparse_fsm_error_o = 1'b1` 立即
     - sha3.sv:306-309 StTerminalError_sparse → `sha3_state_error = 1'b1` 立即
     - sha3pad.sv:478-482 StTerminalError → `sparse_fsm_error_o = 1'b1` 立即
     - keccak_round.sv (default分支) → 立即
     - kmac_entropy.sv:719-723 StTerminalError → `sparse_fsm_error_o = 1'b1` 立即
     - kmac_errchk.sv:224-227 StTerminalError → `sparse_fsm_error_o = 1'b1` 立即
  3. **kmac.sv:1558 SVA** `ASSERT_PRIM_FSM_ERROR_TRIGGER_ALERT(KmacCoreFsmCheck_A,
     u_kmac_core.u_state_regs, alert_tx_o[1])` — 断言只检查最终触发，
     不检查延迟周期数；100周期窗口内 FSM 已在错误态但无 alert
  4. **fsm-error-handling 模式**: 延迟告警 = 错误态期间数据通路可能继续输出
- 建议验证型: 注入 sparse FSM error pulse → 计数 sparse_fsm_error_o 置1所需周期；
  vuln=100, twin=0; 同时检查100周期内 kmac_core 数据通路是否仍有输出

---

### CAND-kmac-04
- 疑点: hjson countermeasures 列表缺少 MSG.MASKING 声明
- 位置: kmac.hjson:297-342 (countermeasures 列表仅13条，无 MSG.MASKING)
- lens: L1 (SEC_CM-vs-RTL)
- 预言机依据:
  1. **hjson msg_mask 字段** (kmac.hjson:558-565): 存在 `msg_mask` 配置位，
     描述 "Message Masking with PRNG" — 功能存在但 SEC_CM 未声明
  2. **RTL g_msg_mask 块** (kmac.sv:906-927): 掩码逻辑确实存在（虽已退化为常量）
  3. **sec-cm-mismatch 模式**: 声明缺失 = 对策验证计划不会覆盖此路径
  4. **对比同列表其他条目**: SW_KEY.KEY.MASKING (line 307) 已声明，
     但 MSG.MASKING（消息路径掩码）未声明 — 两个不同掩码对策
- 建议验证型: 文档审计；若 MSG.MASKING 应声明，则 CAND-kmac-01 的漏洞
  同时违反了 SEC_CM 声明与实现两侧

---

### CAND-kmac-05
- 疑点: hjson 声称 msg_mask "applies PRNG" 但 RTL 用常量全1 — 行为性描述矛盾
- 位置: kmac.hjson:558-565 vs kmac.sv:911,925-926
- lens: L2 (hjson-spec-vs-RTL)
- 预言机依据:
  1. **hjson 原文** (kmac.hjson:558-565): "Message Masking with PRNG.
     If 1, KMAC applies PRNG to the input messages to the Keccak module
     when KMAC mode is on."
  2. **RTL 实现** (kmac.sv:911): `static_mask = {MsgWidth{1'b1}}` — 常量全1，非PRNG
  3. **hjson-spec-vs-rtl 模式** (OT-008/021 GT实例): 规格说A，RTL做B → 直接矛盾
  4. 此候选与 CAND-kmac-01 同根因（常量替换动态），但预言机角度不同：
     CAND-01 依据树内参考，CAND-05 依据 hjson 文档
- 建议验证型: 同 CAND-kmac-01

---

### CAND-kmac-06
- 疑点: msg_mask 信号在 EnMasking==1 时悬空——PRNG 输出被计算但从不消耗
- 位置: kmac.sv:313 (声明), kmac.sv:1298 (连接), kmac.sv:906-927 (未使用)
- lens: L4 (结构lint)
- 预言机依据:
  1. **信号生命周期追踪**: msg_mask 在 kmac.sv:313 声明，
     在 kmac.sv:1298 被 kmac_entropy.msg_mask_o 驱动，
     但 g_msg_mask 块(kmac.sv:906-927) 使用 static_mask 而非 msg_mask
  2. **EnMasking==0 分支** (kmac.sv:928-933) 正确标记 unused:
     `assign unused_msgmask = ^{msg_mask, cfg_msg_mask, msg_mask_en}`
  3. **EnMasking==1 分支无 unused 标记**: msg_mask 未被显式标记 unused，
     lint 工具可能不报但信号实质悬空
  4. **constant-replaces-dynamic 模式指标**: "dangling PRNG" = 高风险信号
- 建议验证型: lint 级确认：grep msg_mask 在 kmac.sv 中的 RHS 出现次数，
     预期仅在 unused 赋值和连接赋值中出现，不在功能逻辑中出现

---

### CAND-kmac-07
- 疑点: 消息掩码退化为确定性取反（bitwise NOT），非随机掩码，SCA对策失效
- 位置: kmac.sv:925-926
  ```systemverilog
  msg_data_masked[i] = msg_data[i] ^ ({MsgWidth{cfg_msg_mask}} & static_mask);
  // 当 cfg_msg_mask=1: msg_data[i] ^ all_ones = ~msg_data[i] (确定性取反)
  // 当 cfg_msg_mask=0: msg_data[i] ^ 0 = msg_data[i] (无掩码)
  ```
- lens: L6 (SCA结构)
- 预言机依据:
  1. **正常设计应有两条固定路径** (FWD/INV 各一套) (L6方法论):
     当前实现A路径(XOR全1=取反)和B路径(直通)——两条路径的输出都是
     消息的确定性函数，非操作数依赖的随机掩码
  2. **对比 kmac_reduced.sv:162-163**:
     `msg_masked[i] = msg[i] ^ ({MsgWidth{msg_mask_en_i}} & msg_mask_permuted)`
     这里 msg_mask_permuted 来自 PRNG，是真正的随机掩码
  3. **SW_KEY.KEY.MASKING 声明** (kmac.hjson:307): 密钥掩码用两 share 实现，
     但消息路径掩码(msg_mask)声称用 PRNG 却用常量——两个掩码对策质量不对称
  4. **entropy_fast_process hjson 文档** (kmac.hjson:545-557) 明确警告
     "should not be used if SCA resistance is required" — 说明设计者对 SCA 有意识，
     但 msg_mask 常量化未受同等审查
- 建议验证型: 时序tb：驱动相同消息多次，XMR-probe msg_data_masked；
  vuln 每次输出相同(~msg)，twin 每次输出不同(msg^PRNG)

---

### CAND-kmac-08
- 疑点: RndCnstMsgPerm 排列层对全1常量是no-op，排列安全对策退化为空
- 位置: kmac.sv:914-921
  ```systemverilog
  always_comb begin
    msg_mask_permuted = '0;
    for (int unsigned i = 0 ; i < MsgWidth ; i++) begin
      msg_mask_permuted[i] = static_mask[RndCnstMsgPerm[i]]; // 全1排列=全1
    end
  end
  ```
- lens: L6 (SCA结构)
- 预言机依据:
  1. **数学事实**: 对全1向量做任意双射排列，结果仍为全1——RndCnstMsgPerm
     的安全作用（打散掩码与数据的对应关系）被 static_mask 全1 完全抵消
  2. **对比 kmac_reduced.sv:152-158**: 排列作用于动态 msg_mask，
     不同PRNG周期产生不同的排列后掩码——排列有实际安全效果
  3. **注释误导**: kmac.sv:913 注释 "Permute the mask bits based on predefined
     pattern" 暗示排列有效，但实际因输入全1而无效果
- 建议验证型: 同 CAND-kmac-07；额外可验证：将 static_mask 改为动态 msg_mask，
  重新运行时序tb，确认排列后掩码值随PRNG变化

---

### CAND-kmac-09
- 疑点: msg_mask_en 驱动 PRNG 推进但 PRNG 输出被丢弃——无效功耗与伪安全
- 位置: kmac.sv:552, kmac.sv:1297-1299, kmac_entropy.sv:368,393
- lens: L4 (结构lint) + L6 (SCA结构)
- 预言机依据:
  1. **msg_mask_en 计算** (kmac.sv:552): `msg_mask_en = cfg_msg_mask & msg_valid & msg_ready`
     — 信号有效时驱动 kmac_entropy 推进 PRNG
  2. **kmac_entropy PRNG 推进** (kmac_entropy.sv:368):
     `.en_i(prng_en || msg_mask_en_i)` — PRNG 因 msg_mask_en 而步进
  3. **kmac_entropy 缓冲更新** (kmac_entropy.sv:393):
     `if (data_update || msg_mask_en_i) rand_data_q <= prng_data_permuted`
     — 缓冲因 msg_mask_en 而更新
  4. **msg_mask_o 输出** (kmac_entropy.sv:399):
     `msg_mask_o = rand_data_q[MsgWidth-1:0]` — 有意义的PRNG低64bit
  5. **但此输出在 kmac.sv 中未被使用** — CAND-kmac-06 已述
  6. **效果**: PRNG 按消息节奏步进（功耗模式正确），但输出被丢弃——
     SCA 攻击者可从功耗侧信道推断 PRNG 在运行，但掩码不实际应用
- 建议验证型: 同 CAND-kmac-01

---

### CAND-kmac-10
- 疑点: EnMasking==0 时 msgfifo_data[1] 被硬绑 '0，但 EnMasking==1 时
     kmac_msgfifo 仅输出单 share 数据到 msgfifo_data[0]
- 位置: kmac.sv:218-223, kmac.sv:1155
- lens: L4 (结构lint)
- 预言机依据:
  1. **kmac.sv:218-223**: `if (EnMasking) assign msgfifo_data[1] = '0`
     — EnMasking==1 时 share1 固定为0
  2. **kmac_msgfifo.sv:174-177**: FIFO 仅输出到 msg_data_o（单数据口），
     在 kmac.sv:1155 连接到 msgfifo_data[0]
  3. **SW_KEY.KEY.MASKING 声明** (kmac.hjson:307) 描述密钥用两 share 保护
  4. **消息路径无两 share**: 消息仅通过 share0，share1 固定为0 —
     这在设计上是合理的（消息非秘密，仅密钥需掩码），但若 msg_mask
     正确实现则消息应被 PRNG 重掩码（remasking），当前因 CAND-kmac-01
     此重掩码也失效
- 建议验证型: 此为 CAND-kmac-01 的连带影响，非独立漏洞

---

### CAND-kmac-11
- 疑点: kmac_errchk StTerminalError 立即置 sparse_fsm_error_o=1 但
     StIdle→StMsgFeed 转换时 block_swcmd 可能阻止合法命令
- 位置: kmac_errchk.sv:236-239
  ```systemverilog
  assign block_swcmd = (err_swsequence)
                     || (err_modestrength && !cfg_en_unsupported_modestrength_i)
                     || err_entropy_ready;
  ```
- lens: L4 (结构lint)
- 预言机依据:
  1. **block_swcmd 逻辑**: 三个条件任一为真则阻断 SW 命令
  2. **err_entropy_ready** (kmac_errchk.sv:285-293): 当 EnMasking==1 且
     kmac_en 有效但 entropy 未就绪时阻断——这是安全检查
  3. **但若 SW 先设 kmac_en 再配 entropy**，首次 CmdStart 会被阻断
     且报 ErrSwHashingWithoutEntropyReady 错误——这是正确行为
  4. **存疑点**: cfg_en_unsupported_modestrength_i 可由 SW 写 CFG_SHADOWED
     使 err_modestrength 不阻断——SW 可绕过 mode+strength 检查
  5. **hjson 描述** (kmac.hjson:399-400): "Other value will result error
     when hashing starts" — 但 SW 可通过 en_unsupported_modestrength 绕过
- 建议验证型: 组合micro-tb：设置无效mode+strength，写
     en_unsupported_modestrength=1，发CmdStart，检查是否正常启动；
     若成功则 hjson 描述与 RTL 不一致

---

### CAND-kmac-12
- 疑点: kmac_core StTerminalError 不清零 en_kmac_datapath/en_key_write，
     错误态期间数据通路可能仍有输出
- 位置: kmac_core.sv:227-235
  ```systemverilog
  StTerminalError: begin
    st_d = st;
    if (st_err_ct < 8'd100) begin
      st_err_ct_d = st_err_ct + 1'b 1;
      sparse_fsm_error_o = 1'b 0;
    end else begin
      sparse_fsm_error_o = 1'b 1;
    end
  end
  ```
- lens: L1 (SEC_CM-vs-RTL)
- 预言机依据:
  1. **默认值在 always_comb 开头置**: `en_kmac_datapath = 1'b0; en_key_write = 1'b0`
     (kmac_core.sv:170-171) — 所以 StTerminalError 的 unique case 不覆盖时走 default
  2. **但 StTerminalError 有显式分支**: line 227-235，此分支不赋值
     en_kmac_datapath/en_key_write → 继承默认值0 → 数据通路关闭
  3. **kmac_valid/kmac_process 也继承默认值0** — 无数据输出
  4. **结论**: 数据通路在 StTerminalError 确实被静默 — 此疑点不成立
  5. **但 sparse_fsm_error_o 延迟100周期仍成立** (CAND-kmac-03)
- 建议验证型: 非独立漏洞，归入 CAND-kmac-03

---

### CAND-kmac-13
- 疑点: kmac_app 在 StError/StErrorAwaitSw/StErrorAwaitApp 状态下
     仍接受 app 数据 (fsm_data_ready=1)——错误态未完全静默数据通路
- 位置: kmac_app.sv:451-527
- lens: L4 (结构lint)
- 预言机依据:
  1. **StError** (line 451-503): `fsm_data_ready = ~err_during_sw_q`
     — 若错误非SW引起，app数据仍被接收(fsm_data_ready=1)
  2. **StErrorAwaitApp** (line 515-527): `fsm_data_ready = 1'b1`
     — 持续接收app数据直到last
  3. **设计意图**: 注释说明需要排空(drain) app 接口以完成事务——
     这是有意设计，错误后仍需完成握手协议
  4. **但数据仍进入 MSG_FIFO 和 SHA3 引擎**——错误期间的计算结果
     被标记为 error（line 243: `error: error_i | fsm_digest_done_q | ...`），
     keymgr 应丢弃
  5. **存疑点**: 若 keymgr 未检查 error 位，可能使用错误期间的摘要
- 建议验证型: 需确认 keymgr 消费端是否检查 app_o.error 位；
     若不检查则为跨模块漏洞（kmac_app + keymgr 消费端）

---

### CAND-kmac-14
- 疑点: kmac 顶层 FSM KmacTerminalError 置 kmac_state_error=1 立即，
     但 lc_escalate_en 传播到各子 FSM 有多周期延迟——
     全局升级可能在部分 FSM 到达 TerminalError 前有短暂不一致
- 位置: kmac.sv:834-851, kmac.sv:1510-1515
- lens: L1 (SEC_CM-vs-RTL)
- 预言机依据:
  1. **FSM.GLOBAL_ESC 声明** (kmac.hjson:327-329): "Escalation moves all
     sparse FSMs into an invalid state" — 未说明是否原子（同周期）
  2. **lc_escalate_en 分布**: 6 份同步拷贝 (NumLcSyncCopies=6)，
     通过 prim_lc_sync 2-stage 同步器 → 至少 2 周期延迟
  3. **lc_tx_or_hi 合并** (kmac.sv:1513-1514): 将本地 fatal alert 合入
     lc_escalate_en — 每个子 FSM 收到的是不同延迟的信号
  4. **kmac_core StTerminalError 延迟100周期** (CAND-kmac-03) 加剧不一致
  5. **但在设计上这通常可接受**: prim_lc_sync 延迟是跨时钟域同步的必要代价；
     关键是最终所有 FSM 都到达 TerminalError
- 建议验证型: [minor] 单一依据，存疑；需确认是否存在延迟窗口内可利用的条件

---

### CAND-kmac-15
- 疑点: kmac_core process_latched 在 StKmacFlush 时由 done_i 清除，
     但若 done_i 在 St-非 StKmacFlush 时到来，latched 值不被清
- 位置: kmac_core.sv:275-284
- lens: L4 (结构lint)
- 预言机依据:
  1. **process_latched 清除条件** (line 280-283):
     `process_o || prim_mubi_pkg::mubi4_test_true_strict(done_i)`
     —- done_i 可以在任何状态清除 process_latched
  2. **但 process_latched 仅在 StKmacMsg 有意义** (line 210-217):
     若 done_i 在 StKey 或 StKmacFlush 时到来，会清除一个不相关的 latch
  3. **SVA** (kmac_core.sv:466-467): `ASSERT(ProcessLatchedCleared_A,
     st == StKmacMsg && process_latched |=> !process_latched)` —
     仅约束 StKmacMsg 下的清除
  4. **结论**: process_latched 清除逻辑安全，done_i 清除是保守操作
- 建议验证型: [minor] 非漏洞，记录供参考
