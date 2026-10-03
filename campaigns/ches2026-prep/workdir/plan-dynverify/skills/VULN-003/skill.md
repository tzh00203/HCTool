# Verification Workorder: VULN-003

## Metadata
- VULN-ID: VULN-003
- Title: lc_ctrl LcStProd 重复 case 值——PROD 态获得 TEST_UNLOCKED 级权限
- IP: lc_ctrl
- Root Cause Type: structural-anomaly
- CVSS Tier: Critical

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_signal_decode.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_pkg.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_state_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/lc_ctrl_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_signal_decode.sv

### Stimulus Sequence
组合逻辑: 驱动 lc_state_i=LcStProd → 检查 lc_dft_en_o/lc_hw_debug_en_o

### Success Criteria (machine-checkable)
vuln: lc_dft_en_o=On, lc_hw_debug_en_o=On (PROD获得测试权限); twin: lc_dft_en_o=Off, lc_hw_debug_en_o=Off; assign 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 lc_ctrl_pkg 导入; LcStProd 编码不匹配→核对 lc_ctrl_state_pkg.sv 枚举值

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
