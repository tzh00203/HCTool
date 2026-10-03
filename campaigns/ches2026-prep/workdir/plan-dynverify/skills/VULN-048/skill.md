# Verification Workorder: VULN-048

## Metadata
- VULN-ID: VULN-048
- Title: Ascon core/duplex 无 SVA 断言 + reqParity ASSUME 被注释
- IP: ascon
- Root Cause Type: —
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L4

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv

### Stimulus Sequence
grep SVA 断言数量; grep reqParity ASSUME 注释状态

### Success Criteria (machine-checkable)
SVA=0, ASSUME 被注释→确认; exit code: 0 (info only)

### Failure Criteria & Troubleshooting
grep 路径错误

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
