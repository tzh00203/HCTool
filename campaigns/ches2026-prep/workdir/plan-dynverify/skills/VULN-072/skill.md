# Verification Workorder: VULN-072

## Metadata
- VULN-ID: VULN-072
- Title: lc_ctrl KMAC FSM error 2-sync 延迟传播
- IP: lc_ctrl
- Root Cause Type: —
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_seq
- **Fidelity Target**: L3

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_kmac_if.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/lc_ctrl_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_kmac_if.sv

### Stimulus Sequence
时序: 注入 FSM error → 检查 2-sync 延迟窗口

### Success Criteria (machine-checkable)
2-sync 延迟是必要的→info; exit code: 0

### Failure Criteria & Troubleshooting
编译失败→检查 lc_ctrl_kmac_if

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
