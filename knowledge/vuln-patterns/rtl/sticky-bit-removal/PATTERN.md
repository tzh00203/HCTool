# 粘性位语义移除

## 根因

规范定义某些位一旦置位只能被复位清除（sticky），注入者删掉"只能置位/不可软件清除"
的保持逻辑，使攻击者可写 0 清除痕迹或解除锁定。

## 代码特征

- 寄存器的写逻辑从 `q | wdata`（只能置位）变成 `wdata`（可任意写）
- `else q <= q;` 保持分支被删，落到默认 `q <= '0` 或被写值覆盖
- mseccfg 的 MML/MMWP：RISC-V 规范定义为 WARL + 只能由硬件/复位清除的场景

## 盲检方法

1. 找配置类寄存器（mseccfg、锁定位、debug 控制位）
2. 读规范/注释判定每位的预期写语义：RW / WARL / sticky / write-1-to-set
3. 核对 RTL 写路径：sticky 位必须有"不可清零"的保持逻辑
4. hjson 的 swaccess 字段（"rw1s" 等）对照实现

## GT 实例

- OT-023 ibex mseccfg：MML/MMWP 的 sticky 性被移除，SW 可随时关闭
  Smepmp 保护。RTL 注释本身写着规范要求 —— 树内注释预言机可用。

## 动态验证

写 1 → 写 0 → 读回：vuln 读到 0（被清），twin 读到 1（sticky 保持）。
