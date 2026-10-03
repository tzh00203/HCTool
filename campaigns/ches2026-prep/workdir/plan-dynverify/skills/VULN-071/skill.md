# Verification Workorder: VULN-071

## Metadata
- VULN-ID: VULN-071
- Title: lc_ctrl D[15] ECC 注释 typo / hashed token 需 cSHAKE128 脚本验证
- IP: lc_ctrl
- Root Cause Type: obfuscated-constant-mismatch
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L3

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_state_pkg.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/lc_ctrl_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_state_pkg.sv

### Stimulus Sequence
Python 脚本: 验证 ECC parity / cSHAKE128 hashed token

### Success Criteria (machine-checkable)
D[15] parity bit 差 1 (注释 typo); hashed token 需脚本验证; exit code: 不一致→exit 1

### Failure Criteria & Troubleshooting
Python 环境缺失

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
