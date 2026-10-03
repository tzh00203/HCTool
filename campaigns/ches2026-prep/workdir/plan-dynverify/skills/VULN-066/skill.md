# Verification Workorder: VULN-066

## Metadata
- VULN-ID: VULN-066
- Title: keymgr gen_in decoy 未置换 + KeyUpdateKmac dis_op 语义存疑
- IP: keymgr
- Root Cause Type: —
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_seq
- **Fidelity Target**: L3

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/keymgr_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr.sv

### Stimulus Sequence
时序 + SCA 差分: 检查 decoy 随机化强度

### Success Criteria (machine-checkable)
decoy 未置换→SCA 弱化; exit code: 0 (info)

### Failure Criteria & Troubleshooting
编译失败→检查 keymgr

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
