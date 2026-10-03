# Verification Workorder: VULN-024

## Metadata
- VULN-ID: VULN-024
- Title: lc_ctrl IdleSt 允许 DEV/PROD 时钟旁路与 SVA 矛盾
- IP: lc_ctrl
- Root Cause Type: hjson-spec-vs-rtl
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_seq
- **Fidelity Target**: L1

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_pkg.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_state_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/lc_ctrl_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv

### Stimulus Sequence
时序: 在 LcStProd + IdleSt 下置 use_ext_clock_i=1 → 观察 lc_clk_byp_req_o

### Success Criteria (machine-checkable)
vuln: lc_clk_byp_req_o=On (PROD 态允许旁路); twin: lc_clk_byp_req_o=Off (PROD 态禁止旁路); verdict 信号差分

### Failure Criteria & Troubleshooting
编译失败→检查 lc_ctrl_fsm 依赖; IdleSt 不可达→增加 FSM 驱动周期

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
