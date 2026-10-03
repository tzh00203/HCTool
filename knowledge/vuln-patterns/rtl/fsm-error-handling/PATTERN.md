# FSM 错误处理弱化

## 根因

错误/致命态的处理被延迟、静音或部分放行：告警晚 100 拍、错误态不清密钥、
总线错误时输出通道不静默。

## 代码特征

- 终态错误分支里 alert 被额外条件门控（`if (state == ERR && <extra>)`）
- 错误态进入密钥清除的路径被改走正常态
- 错误响应时数据输出仍来自正常通路（该输出 0/随机）
- in-tree SVA 与代码矛盾（断言说错误态必须 alert，代码只在子条件 alert）
  —— 断言被注释掉/降级也属此类

## 盲检方法

1. 列出 FSM 全部错误/终止态，读每个态的输出行为
2. 对每个错误态自问三件事：立即告警了吗？密钥/状态清了吗？数据通路静默了吗？
3. **in-file SVA 是最强预言机**：`ASSERT_` 宏逐条读，凡断言约束与代码行为
   矛盾处即候选（注入者改代码常忘改断言；或直接删断言）
4. SEC_CM `*.FSM.LOCAL_ESC` 声明交叉

## GT 实例

- OT-019 rom_ctrl：内部 alert 时 rvalid 仍可置位（错误时数据通道未静默）
  —— 盲检命中
- aes_ctr_fsm（额外发现）：`incr_err` 后进 CTR_ERROR 终态但 alert 被压 100 拍，
  in-tree SVA `AesCtrStateValid`（`!alert_o |-> cs inside {IDLE, INCR}`）
  在这 100 拍每拍违反 —— 动态验证：vuln 违反 SVA 100 次，twin 立即告警

## 动态验证

注入错误脉冲 → 计数到 alert 置位的周期数。vuln=100 拍延迟 / twin=0，
再加 SVA 违规计数。leaf-module tb 即可（依赖少）。
