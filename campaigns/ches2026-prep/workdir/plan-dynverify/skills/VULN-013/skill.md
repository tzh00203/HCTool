# Verification Workorder: VULN-013

## Metadata
- VULN-ID: VULN-013
- Title: keymgr StCtrlInvalid 态跳过 entropy XOR 直接暴露 key_state_q
- IP: keymgr
- Root Cause Type: fsm-error-handling
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_ctrl.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/keymgr_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_ctrl.sv

### Stimulus Sequence
组合逻辑: 置 state_q=StCtrlInvalid → 检查 key_output_ctrl 中 key_o.key 是否跳过 entropy XOR

### Success Criteria (machine-checkable)
vuln: key_o.key = key_state_q (未掩码暴露); twin: key_o.key = key_state_q ^ entropy (正确掩码); 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 keymgr_ctrl 依赖链和 keymgr_pkg; StCtrlInvalid 不可达→用简化组合逻辑直接驱动 state_q

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
