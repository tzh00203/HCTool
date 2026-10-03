# Verification Workorder: VULN-070

## Metadata
- VULN-ID: VULN-070
- Title: lc_ctrl lc_check_byp_en 无 SEC_CM 声明 / volatile_raw_unlock unused / TestUnlocked7 非对称
- IP: lc_ctrl
- Root Cause Type: sec-cm-mismatch
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L4

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/lc_ctrl_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv

### Stimulus Sequence
代码走查: grep SEC_CM 声明 / unused 信号

### Success Criteria (machine-checkable)
声明缺口→确认; exit code: 0 (info)

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
