# 密码算法功能错误

## 根因

密码数据通路被改坏：key schedule 错、轮常数错、pad 长度错、mux 漏选。
功能上密文/标签错误或可逆——但**肉眼验证极其不可靠**，
blind-scan 中 agent "验证过 FIPS-197 全对" 而实际 key schedule 是错的（OT-004 miss）。

## 代码特征

- key schedule 轮密钥导出与标准不符
- 常数表（S-box、轮常数、pad 值）个别项被改
- 数据通路 mux 选择信号缺失（某 stage 输入接错源）
- 长度/偏移常数错（opad 长度 384 vs 512）
- 吸收/挤出阶段的状态字选通遗漏（ascon-128a 型）

## 盲检方法（必须工具验证，禁止肉眼）

1. **树内参考实现差分**：prim_ascon 的 dv/ 下有 vendored ascon-c 参考实现，
   kmac 有 kmac_reduced.sv —— 用 DPI 把 RTL 和 C 参考跑同一组输入比对
2. 标准文档常数表逐项核对（FIPS-197 S-box/轮常数、SHA-2 pad、ascon 轮常数）
   —— 用脚本生成期望值，不靠记忆
3. 多配置矩阵测试：不同 key 长度 / AD 长度（整块 vs 非整块）/ ENC vs DEC，
   单一路径测试会漏条件分支洞
4. 发现"功能正确但路径可疑"时标注 SCA 候选（见 SCA 模式）

## GT 实例

- OT-004 aes-256 key schedule 被重写：agent 声称验证过、实际错 —— **miss**。
  教训：密码验证必须跑真差分，"检查过"不算数
- OT-007 hmac SHA2-512 opad 长度 384（应 512）：树内 HMAC 规格可算出预期
  —— 命中但 filed below-bar（白丢分）
- ascon-128a duplex（额外发现）：AbsorbMSG-ENC 与 AbsorbADEmpty 分支漏
  `sel_mux_key_word1 = WORD`，128a 全部加密输出错 + AD 整块时解密标签必错
  —— DPI 差分 6 配置矩阵全部复现

## 动态验证（DPI 差分模板）

tb 里 DPI-C 调 vendored ascon-c；矩阵至少覆盖：
128/128a × ENC/DEC × AD 整块/非整块。RTL 输出 vs C 参考逐字节比对。
"哪个配置挂、哪个过"还能直接隔离出坏的 FSM 分支。
