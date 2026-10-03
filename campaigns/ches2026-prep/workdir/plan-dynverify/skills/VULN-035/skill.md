# Verification Workorder: VULN-035

## Metadata
- VULN-ID: VULN-035
- Title: AES data_in .de 驱动但 .d 未赋值
- IP: aes
- Root Cause Type: sec-cm-mismatch
- CVSS Tier: Medium

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_core.sv

### Stimulus Sequence
组合逻辑: 触发 data_in_we → 检查 data_in 寄存器 .d 赋值

### Success Criteria (machine-checkable)
vuln: data_in.d 未赋值 (X/tie-off); twin: data_in.d = prd_clearing_data; 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 aes_core; data_in_we 不可达→简化组合逻辑

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
