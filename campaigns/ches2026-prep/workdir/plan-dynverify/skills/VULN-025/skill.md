# Verification Workorder: VULN-025

## Metadata
- VULN-ID: VULN-025
- Title: rom_ctrl BUS.LOCAL_ESC rvalid 泄漏
- IP: rom_ctrl
- Root Cause Type: fsm-error-handling
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl.sv

### Stimulus Sequence
组合逻辑: 驱动 internal_alert=1, bus_rom_req=1 → 观测 bus_rom_rvalid

### Success Criteria (machine-checkable)
vuln: bus_rom_rvalid=1 (alert+req 时泄漏); twin: bus_rom_rvalid=0 (正确抑制); 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 rom_ctrl 依赖链; alert/req 不可同时驱动→组合逻辑简化

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
