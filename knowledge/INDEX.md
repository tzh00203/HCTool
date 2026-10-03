# Hack@CHES 知识库索引

结构仿 logos-knowledge/_global/。准入规则：模式必须可泛化（"抽象，不编目"），
修正用带日期的追加段（"只追加，不覆写"）。

## vuln-patterns/rtl/ — RTL 漏洞模式（盲检导向）

每个 PATTERN.md：root cause / 代码特征 / 盲检方法（不依赖上游 diff）/ GT 实例与命中率。

| 模式 | 一句话 | GT 实例 |
|---|---|---|
| [sec-cm-mismatch](vuln-patterns/rtl/sec-cm-mismatch/PATTERN.md) | SEC_CM 声称的对策 RTL 未实现 | OT-001,006,012,013,016 |
| [hjson-spec-vs-rtl](vuln-patterns/rtl/hjson-spec-vs-rtl/PATTERN.md) | 寄存器规格文档与 RTL 行为矛盾 | OT-008,021 |
| [obfuscated-constant-mismatch](vuln-patterns/rtl/obfuscated-constant-mismatch/PATTERN.md) | 混淆常量解码后≠文档值（必须脚本算） | OT-017,018 |
| [fixed-value-signal](vuln-patterns/rtl/fixed-value-signal/PATTERN.md) | 安全信号被绑死常量 | OT-025, markov |
| [gate-inversion](vuln-patterns/rtl/gate-inversion/PATTERN.md) | 使能/错误门控极性反转 | OT-008 wipe gate |
| [check-bypass](vuln-patterns/rtl/check-bypass/PATTERN.md) | 权限/锁定检查被短路 | OT-022,026 |
| [sticky-bit-removal](vuln-patterns/rtl/sticky-bit-removal/PATTERN.md) | 粘性位（不可清除）语义丢失 | OT-023 mseccfg |
| [width-truncation](vuln-patterns/rtl/width-truncation/PATTERN.md) | 比较/赋值位宽截断 | OT-013 token 32bit |
| [constant-replaces-dynamic](vuln-patterns/rtl/constant-replaces-dynamic/PATTERN.md) | 动态值（PRD/mask）被常量替换 | OT-002,006 |
| [fsm-error-handling](vuln-patterns/rtl/fsm-error-handling/PATTERN.md) | 错误态不告警/不清态/绕过输出 | OT-019, aes_ctr |
| [crypto-functional-wrong](vuln-patterns/rtl/crypto-functional-wrong/PATTERN.md) | 密码算法功能错误（必须工具验证） | OT-004,007, ascon-128a |
| [structural-anomaly](vuln-patterns/rtl/structural-anomaly/PATTERN.md) | 端口删除/重复case/窗口条件错误 | OT-015,016,027, lc dup |

## tech-stacks/

- [rtl-opentitan](tech-stacks/rtl-opentitan/SECURITY_NOTES.md) — 目录结构、SEC_CM 约定、
  盲预言机地图（hjson/testplan/SVA/树内参考）、12 IP 清单、Verilator 构建要点

## standards/

- [ches-2026-rules](standards/ches-2026-rules.md) — Rule 3、评分公式、19 字段提交格式
- [verilator-twin-methodology](standards/verilator-twin-methodology.md) — vuln-vs-twin 方法 +
  保真度分级 + 10 个已验证案例索引
- [verilator-4.210-caveats](standards/verilator-4.210-caveats.md) — 全部已知坑

## 盲检命中率备忘（blind-scan eval 实测）

- 纯盲（不用上游 diff）≈ 10/27 (37%)；盲预言机找到的都是最难的那批（OT-001,006,012,013,016）
- 上游 diff 辅助 ≈ 18/27 (67%) —— **决赛 Rule 3 禁止，不可依赖**
- 4 个 GT 是纯文本改动（语义 no-op/端口删除/宏改名），盲检不可见，决赛大家都找不到
- 2 个 miss 是 LLM 心算混淆常量出错 → 必须脚本化常量折叠
- 2 个真实检测缺口：密码功能错误（肉眼验证不可信）和 SCA 结构弱化
