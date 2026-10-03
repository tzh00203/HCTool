# Hack@CHES 2026 比赛规则备忘

## 硬规则

- **Rule 3：禁止与相似开源 SoC 对比 RTL**。不可 fetch GitHub lowRISC OpenTitan/Ibex
  上游仓库做 diff。一切证据必须树内自洽（本 harness 的 hunter 节点开 `no_web: true`
  机器级强制）。
- 提交格式：Google Form，19 字段（12 必填），见下。

## 评分公式（Phase 1 实测版）

| 项 | 分 |
|---|---|
| 确认的 issue | 5 |
| CVSS + 测试 | 5 |
| user-level exploit（物理类=攻击流描述+仿真脚本证明可行性） | 50 |
| bug 变体 | 3 |
| exploit 变体 | 15 |
| 自动化工具 bonus | 100 / 50 / 5 |

**Tie-breaker = 提交时间** → 先验证完先交，不攒批。

## 提交 19 字段

必填（12）：Email, Team name, Bug number, Security feature bypassed, Finding,
Location or code reference, Detection method, Security impact, Adversary profile,
Proposed mitigation, CVSSv3.1 score and severity, CVSSv3.1 Details。

选填（7）：New Tools, AI Tools(radio), LLM(radio), LLM Details, Online LLM Details,
LLM Prompts, Attachment link。

诚实申报 AI 使用（AI Tools=Yes, LLM=Yes, 填模型名）。

## 策略结论（blind-scan 实测数据支撑）

1. **Report-everything**：below-bar 候选=0 分。found 67% 只 submit 了 48%。
   严重度过滤全部关闭。
2. **提交优先级**：带 PoC 的（+50）> 高 CVSS（+5×2）> 其他；按预估分排序提交。
3. **变体狩猎**：确认一个后立即同模块找变体（+3/个）。
   pmp 一处注入出过 3 个独立洞。
4. 4 个 GT 型别（语义 no-op/端口删除/宏改名/纯文本改动）盲检不可见——
   时间不要浪费在"看起来和注释完全一致但总觉得怪"的地方，除非有外部对照。
