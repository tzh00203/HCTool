# 权限/锁定检查被短路

## 根因

权限检查、锁定检查、debug 门控的条件被弱化或删去一条子句，
特定调用方/模式下检查失效。

## 代码特征

- 检查表达式从 `A && B && C` 变 `A && C`（少了 B）
- 权限比较从 `==` 弱化为 `>=` 或位掩码不全
- 锁定检查 `locked && ...` 中 locked 被取反或跳过
- debug/异常模式下的豁免条件过宽（该只豁免特定地址，实际豁免全部）

## 盲检方法

1. 列出模块所有"拒绝路径"：哪些条件组合输出 DENY/EXC/err
2. 对照规范（RISC-V spec、Smepmp、Debug spec——树内注释常引用）核对每种模式
   的预期判定矩阵：M/U/S × locked/unlocked × matched/unmatched
3. 特别关注注释与代码矛盾处：注释说 "M-mode cannot access locked regions"，
   代码里 M-mode 分支没检查 lock → 直接候选
4. 反向枚举：构造"应该被拒绝"的组合表，逐格核对代码

## GT 实例

- OT-022 ibex CSR：特权级检查（mstatus.TSR/MPRV 等）被抑制，
  U-mode 可访问受限 CSR —— agent 靠 diff 发现，但树内 CSR 注释本身就是预言机
- OT-026 ibex_pmp：M-mode 对 locked region 的访问检查中 lock 位被取反，
  M-mode 可穿透锁定的 PMP 区 —— 树内注释矛盾同样存在

## 动态验证

判定矩阵直接变 tb：枚举 8-10 个 (mode, lock, match) 组合，
vuln vs twin（按规范修好的副本）各跑一遍，差异格即洞。
ibex_pmp 的 directed 8-test + 3000 随机向量模式可复用。
注意 csr_pmp_addr_i 要喂 byte 形式（{pmpaddr, 2'b00}），
word 形式地址会让 matching 静默失败。
