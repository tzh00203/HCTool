# 混淆常量解码后与文档值不符

## 根因

lc_ctrl/otp_ctrl 的 package 常量用编码形式存储（sparse encoding、XOR 混淆、
permutation），注入者改常量的个别位或 OR 进额外位，肉眼极难发现，
LLM 心算"看起来等价"就放过了。这是 blind-scan eval 最惨痛的 miss 类型。

## 代码特征

- `localparam` 常量带位操作装饰：`& {mask}`、`| {bits}`、拼接、reduction
- 多个常量共享同一编码函数（decode 函数在别处）
- 常量注释声称等价于某个简单值（如 "equivalent to LcStRma"）

## 盲检方法（强制脚本化，禁止 LLM 心算）

1. 找到编码函数（如 `dec_otp_lci`、`lc_tx_t` 的 decode）
2. **写 Python 脚本**：把 SV 常量逐位抄进脚本，实现同一 decode 逻辑，
   输出解码值 hex
3. 与"期望值"bit-exact 比对（期望值来自树内文档/枚举定义/兄弟常量模式）
4. 任何一位不同 = 立即发现，无需人工判断
5. 同时检查：OR 进额外位（如 `| LcStRmaBits`）不是恒等操作——
   "或上某位"几乎必然改变解码结果，"semantically equivalent noise" 是错误结论

## GT 实例（两个全 miss，教训）

- OT-017 otp LC 默认态常量 OR 进 Rma 位：agent 完整解码了常量，然后**错误判断**
  "语义等价的噪声"而放行。实际 OR 改变了解码结果。
- OT-018 flash key 默认值混淆形式被改：同样的错误结论。

修复方法：生成可执行的 eval 脚本（`emit evaluable check scripts`），
bit-exact 数值比较，零 LLM 算术参与。

## 工具

Python 三件套：`int(x, 2)` 抄位 → decode 函数移植 → `assert decoded == expected`。
10 行脚本，5 分钟写完，杜绝这类 miss。
