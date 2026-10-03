# Verification Workorder: VULN-008

## Metadata
- VULN-ID: VULN-008
- Title: AES-256 密钥扩展被重写——密码功能可能错误
- IP: aes
- Root Cause Type: crypto-functional-wrong
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_dpi
- **Fidelity Target**: L1

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_key_expand.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_pkg.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/dv/aes_model_dpi/aes_model_dpi.c
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/dv/test_vectors/nist_vectors_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_key_expand.sv

### Stimulus Sequence
DPI 差分: 用 C model (dv/aes_model_dpi/aes_model_dpi.c) 作参考，测试 AES-256 ECB/CTR × ENC/DEC × NIST 向量

### Success Criteria (machine-checkable)
vuln: RTL output ≠ C reference output (至少一个向量不匹配); twin: RTL output = C reference output (全部匹配); exit code: 差分输出非零→exit 1

### Failure Criteria & Troubleshooting
DPI C 编译失败→检查 aes_model_dpi.c 路径和 gcc; 向量不加载→检查 nist_vectors_pkg.sv; 全部匹配可能意味着 key_expand 未被调用→确认 AES_256 分支激活

## Twin Repair Basis
- Repair only the vulnerability line(s)
- Repair source: in-tree oracle (file comments, SVA, sibling module pattern, spec)
- Twin file: same module with `_twin.sv` suffix

## Deliverables
- `tb_*.sv` — testbench (vuln + twin dual instantiation)
- `*_twin.sv` — repaired twin module
- `build_*.sh` — Verilator build script
- `sim_main.cpp` — C++ simulation driver
- `exploit.py` — PoC entry (redbud mode)

## Exit Code Convention
- **exit 1** = finding confirmed (vuln behavior differs from twin)
- **exit 0** = no difference found (vuln matches twin — finding NOT confirmed)
