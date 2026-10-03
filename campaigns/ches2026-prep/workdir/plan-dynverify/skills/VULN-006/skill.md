# Verification Workorder: VULN-006

## Metadata
- VULN-ID: VULN-006
- Title: AES 密钥擦除用密钥派生材料（key_expand_out）而非 PRD
- IP: aes
- Root Cause Type: constant-replaces-dynamic
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_cipher_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_cipher_core.sv

### Stimulus Sequence
组合逻辑: 触发 cipher_key_clear 信号 → 检查 KEY_FULL_CLEAR/KEY_DEC_CLEAR 分支 mux 选择

### Success Criteria (machine-checkable)
vuln: key_clear_src=key_expand_out (密钥派生材料); twin: key_clear_src=prd_clearing_key_i (PRD); mux_sel 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 aes_cipher_core 文件路径和 prim 导入; mux 不可观测→加 XMR probe

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
