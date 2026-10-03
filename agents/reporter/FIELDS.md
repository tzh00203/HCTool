# 提交字段映射表（reporter 工具书）

内部产物 → Google Form 19 字段。规则原文见
`knowledge/standards/ches-2026-rules.md`。

## 必填 12 字段

| # | Google Form 字段 | 内部来源 | 措辞规范 |
|---|---|---|---|
| 1 | Email | 队伍固定值 | 队长邮箱，写进 campaign context.md |
| 2 | Team name | 队伍固定值 | 同上 |
| 3 | Bug number | VULN-00N 的 N | 与 submissions 文件名一致 |
| 4 | Security feature bypassed | vulns.md 条目的安全特性 | 用预言机原词（如 "PMP entry locking", "CSR privilege check"），不自己发明词 |
| 5 | Finding | 现象一句话 + 触发条件 + 安全后果 | 不写修复过程；黑体一句话开头 |
| 6 | Location or code reference | vulns.md 位置字段（file:line） | 仓库相对路径 + 函数/always 块名 |
| 7 | Detection method | review.md 的方法记录 | lens 名 + 预言机引用 + (PoC 档加) twin 差分实验描述——bonus 申报入口 |
| 8 | Security impact | 知识库同 pattern GT 实例的 impact 措辞 | 机密性/完整性/可用性 + 攻击者能力假设 |
| 9 | Adversary profile | 攻击路径推导（hunter 候选 + PoC 激励） | 明确能力边界：物理/固件/user-level；信息缺失标 [assumed] |
| 10 | Proposed mitigation | twin 修复 diff 的正向描述 | 依据工单预言机原文，给 file:line |
| 11 | CVSSv3.1 score and severity | review.md 校准值 | 格式 `7.1 (High)`；与 review 一致不许调 |
| 12 | CVSSv3.1 Details | 向量串 | 按 CVSS v3.1 规范展开 AV/AC/PR/UI/S/C/I/A，与 11 自洽 |

## 选填 7 字段

| # | Google Form 字段 | 内部来源 |
|---|---|---|
| 13 | New Tools | 如实：logos-lite harness（多 agent 流水线 + twin 差分验证） |
| 14 | AI Tools (radio) | Yes |
| 15 | LLM (radio) | Yes |
| 16 | LLM Details | 模型名（当前网关配置的模型，从 context.md 读） |
| 17 | Online LLM Details | 离线网关则 N/A |
| 18 | LLM Prompts | agent 合同目录路径 + 一句话说明角色分工 |
| 19 | Attachment link | `workdir/poc/<VULN-ID>/` 整包（exploit.py 路径无关可复现） |

## 档位与预估分（排序依据）

| 档 | 判据 | 预估分 |
|---|---|---|
| PoC 档 | RESULT.md = [poc-success] + exploit.py 存在 | 50+5+5 |
| CVSS 档 | poc-success 但无 user-level 路径，或高 CVSS | 5+5 |
| 静态档 | 未验证（poc-fail/blocked）但有树内证据链 | 5 |

变体（+3/个）与 exploit 变体（+15/个）在主条目提交后追加，
Detection method 注明 "variant of bug #N"。
