# Verification Workorder: VULN-037

## Metadata
- VULN-ID: VULN-037
- Title: rom_ctrl SecDisableScrambling=1 全废安全但 pwrmgr 认为通过
- IP: rom_ctrl
- Root Cause Type: sec-cm-mismatch
- CVSS Tier: Medium

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
组合逻辑: 设 SecDisableScrambling=1 → 检查 pwrmgr_data_o.done==MuBi4True 且 checker_alert==0

### Success Criteria (machine-checkable)
vuln: pwrmgr_data_o.done=MuBi4True, checker_alert=0 (安全全废但无告警); twin: pwrmgr_data_o.done=MuBi4False 或 alert=1; 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 rom_ctrl 参数化; SecDisableScrambling 不可设→编译时参数

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
