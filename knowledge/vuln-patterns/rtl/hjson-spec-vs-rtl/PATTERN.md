# hjson 规格与 RTL 矛盾

## 根因

寄存器规格 `data/{ip}.hjson` 是行为合同：字段访问权限（hwaccess/swaccess）、
复位值、寄存器间依赖、TRIGGER 行为描述。注入者改 RTL 不改 hjson，
留下规格-实现分歧——这是最好的"树内预言机"。

## 代码特征

- hjson 说某字段 `swaccess: "rw"` 但 RTL 从不回读（hw2reg 缺失）
- hjson 描述 TRIGGER 效果（如 "Performs a secure wipe of sensitive data"）但 RTL 的
  trigger 位是 noop
- hjson 声称 escalate 输入 "fatal, needs reset" 但 RTL unused / 不拉 alert
- hwext 寄存器：SW 写不进 / 该读出关键数据却接了 key
- 端口在 hjson 的 `wired_to`/文档描述中出现但模块端口列表缺失

## 盲检方法

1. 全文读 `data/{ip}.hjson`，抽出行为性描述句（"performs/needs/cannot recover/
   secure wipe/fatal"）逐条编号
2. 对每条找 RTL 实现点：grep 关键词（寄存器名、信号名、TRIGGER 位名）
3. 验证实现存在且语义匹配
4. 特别核对：
   - WIPE/RESEED/START 类 TRIGGER → 找到对应 FSM 路径真的清/重播种
   - escalate/lc_escalate_en 输入 → 落到 alert + 状态清除，不是 dangling
   - "cannot be recovered" → 对应 fatal alert 而非 recoverable
5. 寄存器位对齐：`reg2hw`/`hw2reg` 字段的 we/re/de/d/q 五件套完整性

## GT 实例

- OT-008 hmac：reg_top 的 `wipe_secret_we` 门控极性反转（对 valid 写不生效），
  hjson 描述 wipe 语义 —— 盲检命中（配 gate-inversion 模式）
- OT-021 uart：LSIO 触发语义与 hjson 描述不符（触发后卡高）—— 盲检命中

另：ascon_core 的 escalate-ignored + WIPE-noop 两个 fork 原生洞都是
"hjson 说了、RTL 没做"型（动态验证已确认）。

## 证据要求

引用双端：hjson 的行号+原文句，RTL 的 file:line+代码摘录。
只有两端对照才有说服力。
