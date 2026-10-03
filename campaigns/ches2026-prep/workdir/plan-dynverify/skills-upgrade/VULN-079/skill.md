# 证据升级工单: VULN-079

## 元数据
- VULN-ID: VULN-079
- 标题: rom_ctrl checker 侧地址无冗余 / FSM 提取依赖枚举 / PRINCE 参数需脚本比对
- 当前档位: L4（静态/脚本结论）
- 目标: 升级到本 VULN 可达到的最高证据档

## 必读输入
1. 原工单: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/plan-dynverify/skills/VULN-079/skill.md
2. 原验证结果: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-079/RESULT.md（先读，保留其历史结论）
3. 模板与已验证样板: /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/REF.md

## 升级分析（预判，可修正但需说明理由）
PRINCE 参数升级路径：L3 脚本——用 Python 实现 PRINCE 参考模型（树内 prim Prince 多项式表为预言机），随机向量比对 RTL 参数集。地址冗余/FSM 枚举部分保持 L4 并说明。

## 升级方法论（硬性要求）
1. **先拆分**：把工单的每个子 claim 分成「行为可仿真」/「属性缺失」/「声明缺失」三类。
2. 行为可仿真 → L2 组合 micro-tb（vuln vs twin 差分，exit 1 = 确认）。twin 修复必须有树内预言机
   依据（hjson 措辞/兄弟模块/SVA/规范参考表），禁止凭空造 twin。
3. 属性/声明缺失 → L3 脚本证明：写可复核的 Python 脚本（解析 hjson/grep/常量追踪），运行并留存输出。
4. 确实无法升级的子项 → 诚实保留 L4 并写明原因。**禁止伪造动态证据。**
5. 产出：在 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-079/RESULT.md 末尾追加 `## Upgrade (2026-09-23)` 段落——
   新 verdict + 新档位 + 每个子 claim 的升级结果表 + 复现命令。不删除原有内容。
6. 新建文件（tb/twin/build.sh/脚本）放在 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-079/upgrade/ 子目录。

## 约束
- Rule 3：禁止访问网络/上游仓库（no_web 已强制）。
- Verilator 4.210 已知坑见 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/knowledge/standards/verilator-4.210-caveats.md。
- 若 30 分钟内无法建立可运行实验，降级为 L3 脚本证明并如实记录。
