# Verification Workorder: VULN-062

## Metadata
- VULN-ID: VULN-062
- Title: ibex-csrs unused RLB / SEC_CM 缺锚点 / napot_mask 截断
- IP: ibex-csrs
- Root Cause Type: sec-cm-mismatch
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L4

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_pmp.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv

### Stimulus Sequence
代码走查: grep RLB 使用 / SEC_CM 锚点 / napot_mask 宽度

### Success Criteria (machine-checkable)
RLB 跨模块使用确认; SIDELOAD 无锚点确认; napot_mask 功能等价→info; exit code: 0

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
