# Verification Workorder: VULN-065

## Metadata
- VULN-ID: VULN-065
- Title: keymgr op_update_sel invalid 竞争窗口
- IP: keymgr
- Root Cause Type: —
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_seq
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
时序: op_ack 与 inv_state 同周期 → 检查一键窗口

### Success Criteria (machine-checkable)
vuln: 允许 KMAC 写入; twin: 阻止写入; 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 keymgr_ctrl

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
