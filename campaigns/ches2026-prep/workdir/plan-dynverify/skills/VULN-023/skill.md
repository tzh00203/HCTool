# Verification Workorder: VULN-023

## Metadata
- VULN-ID: VULN-023
- Title: keymgr data_en_state FSM default 不设 fsm_err_o
- IP: keymgr
- Root Cause Type: fsm-error-handling
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_data_en_state.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/keymgr_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_data_en_state.sv

### Stimulus Sequence
组合逻辑: 注入 sparse FSM 故障 (非法 state 编码) → default 分支 → 检查 fsm_err_o

### Success Criteria (machine-checkable)
vuln: fsm_err_o=0 (default 不设错误); twin: fsm_err_o=1 (正确设错误); 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 keymgr_data_en_state 依赖; 非法 state 编码不可注入→直接驱动 state_q

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
