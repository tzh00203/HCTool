# Verification Workorder: VULN-042

## Metadata
- VULN-ID: VULN-042
- Title: AES 5 个 RndCnst 混淆常量仅验置换完整性
- IP: aes
- Root Cause Type: obfuscated-constant-mismatch
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L3

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_prng_clearing.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_prng_masking.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_prng_clearing.sv

### Stimulus Sequence
Python 脚本常量折叠验证

### Success Criteria (machine-checkable)
脚本验证: 检查 LFSR seed/perm 值与上游 gen-lfsr-seed.py 一致; exit code: 不一致→exit 1

### Failure Criteria & Troubleshooting
Python 环境缺失→安装依赖

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
