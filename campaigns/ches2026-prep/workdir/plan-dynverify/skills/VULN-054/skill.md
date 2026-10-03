# Verification Workorder: VULN-054

## Metadata
- VULN-ID: VULN-054
- Title: entropy_src SHA3 EnMasking=0 + rand 全零
- IP: entropy_src
- Root Cause Type: —
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_seq
- **Fidelity Target**: L3

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/edn_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv

### Stimulus Sequence
检查 SHA3 EnMasking 参数和 rand 连接

### Success Criteria (machine-checkable)
EnMasking=0 确认→info; exit code: 0

### Failure Criteria & Troubleshooting
编译失败→检查 entropy_src_core

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
