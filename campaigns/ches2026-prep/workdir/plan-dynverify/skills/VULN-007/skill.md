# Verification Workorder: VULN-007

## Metadata
- VULN-ID: VULN-007
- Title: AES DIP_CLEAR 用上一个明文（data_in）而非 PRD
- IP: aes
- Root Cause Type: constant-replaces-dynamic
- CVSS Tier: High

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
组合逻辑: 触发 KEY_IV_DATA_IN_CLEAR → 检查 DIP_CLEAR 分支 mux 选择 data_in_prev vs prd_clearing_data

### Success Criteria (machine-checkable)
vuln: dip_clear_src=data_in (明文残留); twin: dip_clear_src=prd_clearing_data (PRD); mux_sel 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 aes_core 文件路径; DIP_CLEAR 分支不可达→简化为表达式级 micro-tb

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
