# 结构异常（端口删除 / 重复 case / 窗口条件错误）

## 根因

不属于数据流语义的结构级改动：端口删除、case 重复项、
地址窗口/模式条件用错逻辑操作符（| vs &）。

## 代码特征

- **端口删除**：模块端口列表少了信号，上层连线的地方悬空/被删；
  hjson 或文档还有该信号的文字引用
- **重复 case 项**：同一 case 值出现两次，第一项生效（如 lc_ctrl 的
  `LcStProd` 重复，测试分支吃掉生产分支）→ 生产芯片解码出测试态权限
- **窗口条件错误**：地址/模式窗口判断 `| ~mask` vs `& mask`
  （OT-027 debug 窗口 `| ~DmAddrMask` 永不满足）
- **默认分支改写**：case default 从安全值改成放行值

## 盲检方法

1. **端口清单 lint**：模块端口列表 vs (a) 实例化处连线 (b) hjson 提及
   (c) SEC_CM/testplan 文字引用 —— 三方对照找缺失
2. **case 值查重**：脚本提取 case 项常量，重复即候选（SV 仿真 first-match-wins）
3. 窗口/掩码条件手工真值表：构造应命中窗口的输入验证表达式可满足
4. default 分支核对：必须是安全侧（拒绝/保持/告警）

## GT 实例

- OT-015 lc_ctrl `hw_debug_clr` 端口删除：树内零引用残留 —— 盲检不可见
  （端口清单 lint 需要外部文档对照，赛内 hjson 残留是唯一机会）
- OT-016 lc_ctrl Dev/Prod clkbyp allow：in-file 断言矛盾盲检命中
- OT-027 ibex_pmp debug 窗口 `| ~DmAddrMask`：XMR 探针实测窗口永不匹配 ——
  动态验证确认（twin 用 `&` 后正确匹配）
- lc_ctrl `LcStProd` 重复 case（额外发现 #1，Critical）：PROD 解码成
  TEST_UNLOCKED0 权限（DFT/hw_debug/RMA 全开）—— testbench 直接驱动
  signal_decode 复现，这是全部额外发现里最严重的一个

## 动态验证

- 重复 case：枚举驱动该状态值，解码输出 vs 预期权限表逐项比
- 窗口条件：喂真实 dm 地址，XMR 探窗口匹配信号（vuln 永假 / twin 有真）
