# lc_ctrl 候选清单（dry-chain 手工种子样例）

> 本文件为空载链路验证的手工种子，模拟 hunter 产出格式。非真实挖掘结果。

### CAND-lc_ctrl-1
- 疑点: 状态迁移令牌比较只用了 128bit hashed token 的低 32bit，
  高 96bit 不参与比较——攻击面从 2^128 缩到 2^32
- 位置: hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv:456
  ```systemverilog
  if (hashed_token_i[31:0] == hashed_token_mux[31:0] &&
  ```
- lens: 常量折叠/结构lint（宽度截断形态，对照 knowledge/vuln-patterns/rtl/width-truncation）
- 预言机依据: lc_token_t 为 128bit（lc_ctrl_pkg.sv）；SEC_CM: TOKEN.DIGEST
  （lc_ctrl_fsm.sv:447）声称完整 token digest 防护；hjson testplan 声明
  token 比较必须不可绕过
- 建议验证型: 组合micro-tb（twin 改为全宽比较，差分激励碰撞高 96bit）

### CAND-lc_ctrl-2
- 疑点: RAW unlock 路径用未散列 token 与常量直接比较，且该比较不受
  TOKEN.DIGEST SEC_CM 覆盖——存疑，可能是设计如此
- 位置: hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv:301
  ```systemverilog
  if (unhashed_token_i == RndCnstRawUnlockTokenHashed) begin
  ```
- lens: hjson-spec-vs-RTL
- 预言机依据: 单一依据（testplan 对 raw unlock 的 token 要描述模糊），[minor]
- 建议验证型: 脚本（常量折叠核对 RndCnst 与 hjson 生成参数一致性）
