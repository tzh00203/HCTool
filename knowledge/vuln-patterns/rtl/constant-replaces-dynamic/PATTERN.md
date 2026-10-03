# 动态值被常量替换

## 根因

本应来自 PRNG/LFSR/输入的动态值被换成常量（全 0、全 1、固定字节）。
常带"优化"伪装注释。SCA 防护 mask 和清除 PRD 是重灾区。

## 代码特征

- `assign mask = {Width{1'b1}};` / `= '0;` 旁边 LFSR/PRNG 实例还在但输出未被使用
- `static_mask`、`const_mask` 类命名替换 `lfsr_mask`/`prng_mask`
- 清除路径用常数 0 而不是 `prd_clearing_data`（SEC_WIPE 语义）
- 注释说 "optimization: mask is fixed for timing"——正常设计不会这么做

## 盲检方法

1. grep 全模块常数驱动：`assign <signal> = '{...}'`、`{N{1'b1}}`、`'0`
2. 反向查 PRNG/LFSR 实例：输出端口是否被消费（dangling PRNG = 高危）
3. 树内参考实现对照：kmac 有 `kmac_reduced.sv` 参考版，mask 机制可对比
4. SEC_CM 交叉：`*.MASKING` 声明 + 常数 mask = 直接矛盾

## GT 实例

- OT-006 kmac：LFSR msg mask 被换成全 1 常量 —— 树内 kmac_reduced.sv 参考对照盲检命中
- OT-002 aes cipher_core：默认态保持内部状态（复位/清除用常数路径）—— 盲检命中
- aes_core F1/F2（额外发现）：data_in 清除写 0 不写 PRD、DIP_CLEAR mux 选
  data_in 不选 prd_clearing_data —— 动态验证确认

## 动态验证

触发清除路径，XMR 探内部寄存器：vuln 变 0（或明文残留），
twin（补 `.d = prd_clearing_data`）变 PRD 值。aes_core tb 模式。
