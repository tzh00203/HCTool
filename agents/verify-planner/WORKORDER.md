# 验证工单格式（verify-planner 产出合同）

文件：`workdir/plan-dynverify/skills/<VULN-ID>/skill.md`

```markdown
# 工单: <VULN-ID>

## 目标漏洞
- vulns.md 条目链接（绝对路径 + VULN-ID）
- 一句话疑点
- 预期安全行为（预言机依据原文）

## 工单类型
- tb 型: 组合micro-tb | 时序tb | DPI差分 | 脚本
- 保真度目标: L1 执行级 | L2 数据流级 | L3 脚本级
- 模板: templates/tb_*.tmpl 中的哪个（+ 活样板 examples/ 哪个最接近）

## 环境与依赖
- DUT 模块: <module>（$OT_TREE/hw/ip/<ip>/rtl/<file>.sv）
- twin 修复说明: 改哪几行、依据哪条树内预言机（file:line 原文）
- 依赖文件清单（有序!）:
  1. packages/stubs: ...
  2. prim 原语: ...
  3. DUT 叶子: ...
  4. twin / tb / cpp: ...
- 特殊坑预警:（从 knowledge/standards/verilator-4.210-caveats.md 摘相关条目，
  如"negedge 采样单拍脉冲"、"csr_pmp_addr 字节形"）

## 验证步骤
1. 复制模板填空
2. bash build_*.sh
3. 记录 exit code + stdout 证据

## 成功判据（机器可查）
- exit code == 1 且 test_confirmed_o == 1
- （DPI 型）目标配置 FAIL 且控制配置 PASS
- （矩阵型）逐格列出预期：vuln 错 X 格 / twin 全对

## 失败判据与排查
- 编译失败 → 查文件顺序 / VERILATOR_ROOT sed / 缺 stub
- exit 2（timeout）→ 激励没踩中路径，检查 FSM 状态序列
- NOT CONFIRMED → 双向结论都有效：vuln 行为与 twin 一致 = 候选大概率误报，
  如实记录，不许硬凑成功
```

## 纪律

- 判据里禁止出现"人工确认""目视检查"
- twin 修复依据必须能被 reviewer 复核（file:line + 原文引用）
