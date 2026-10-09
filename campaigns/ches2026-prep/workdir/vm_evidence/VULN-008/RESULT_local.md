# RESULT.md — VULN-008: AES-256 密钥扩展被重写——密码功能可能错误

## 裁决: `[poc-success]`

**保真度级别: L1 执行级实证** — Verilator 全模块 vuln-vs-twin 仿真

## 发现描述

AES-256 FWD 方向密钥扩展中，旧半部分下移索引错误：使用 `key_i[s][i+3]` 而非正确的 `key_i[s][i+4]`（等价于 `key_i[s][7:4]`），导致展开的轮密钥完全错误。

同时 round 0 行为被改为 passthrough（`regular = key_i`），上游为半交换（`{key_i[3:0], key_i[7:4]}`），但 round 0 在正常运算中不影响结果（初始轮不做密钥扩展），主漏洞是 rnd!=0 的 off-by-one 索引。

## 完整复现命令

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-008
bash build.sh
# 或
./exploit.py --repo /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
```

## 原始输出摘录

```
cycles=4
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: AES-256 FWD key expansion shift off-by-one (key_i[i+3] instead of key_i[i+4])
  vuln: lower half of expanded key uses key_i[3..6] (wrong shift index i+3)
  twin: lower half of expanded key uses key_i[4..7] (correct shift index i+4, upstream)
exit code: 1 (1 = finding confirmed)
```

## Twin 修复 diff 摘要

仅改两行（diff 以 blind 版为基线）：

1. **Line 396**（FWD round 0 默认值）:
   - vuln: `regular[s] = key_i[s]; // default: passthrough`
   - twin: `regular[s] = {key_i[s][3:0], key_i[s][7:4]}; // twin fix: upstream rnd==0 is half-swap`
   - 依据: 上游 `aes_key_expand.sv` diff（`diffs/aes_key_expand.diff` 第 10 行 `-` 侧）

2. **Line 401**（FWD shift 索引）:
   - vuln: `regular[s][i] = key_i[s][i+3]; // shift upper half down`
   - twin: `regular[s][i] = key_i[s][i+4]; // twin fix: upstream uses key_i[7:4], i+4 not i+3`
   - 依据: 上游 `aes_key_expand.sv` diff（`diffs/aes_key_expand.diff` 第 13 行 `-` 侧 `regular[s][3:0] = key_i[s][7:4]`）

INV 分支与 default 分支与上游功能等价（已逐一验证），无需修改。

## 验证方法

- 类型: L1 执行级实证（Verilator 4.210 vuln-vs-twin 全模块仿真）
- 激励: NIST AES-256 ECB 测试向量密钥（FIPS 197 Appendix A.3），AES-256 FWD 方向，round 1 和 round 2
- 判据: vuln key_o != twin key_o → exit 1 = confirmed
- 结果: round 1 即出现 8 个 word 中多个 mismatch，确认 off-by-one shift 产生错误的轮密钥

## 产出文件清单

| 文件 | 说明 |
|---|---|
| `aes_key_expand_twin.sv` | 修复后的 twin 模块（仅改 2 行） |
| `tb_aes_key_expand_256.sv` | 时序 tb：FSM 驱动 AES-256 FWD，双实例化 vuln/twin |
| `sim_main.cpp` | C++ 半拍驱动 + verdict 输出 |
| `build.sh` | Verilator 4.210 构建脚本 |
| `exploit.py` | redbud 模式 PoC 入口 |
| `RESULT.md` | 本文件 |
