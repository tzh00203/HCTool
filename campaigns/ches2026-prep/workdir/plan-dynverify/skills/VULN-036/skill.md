# Verification Workorder: VULN-036

## Metadata
- VULN-ID: VULN-036
- Title: AES data_out 异步复位被 data_out_we 门控
- IP: aes
- Root Cause Type: fsm-error-handling
- CVSS Tier: Medium

## Verification Plan

### TB Type
- **Type**: tb_seq
- **Fidelity Target**: L1

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_core.sv

### Stimulus Sequence
时序: 在 data_out_we==SP2V_HIGH 时刻拉 rst_ni=0 → 检查 data_out_q

### Success Criteria (machine-checkable)
vuln: data_out_q 残留 (复位被门控); twin: data_out_q=0 (正确复位); verdict 信号差分

### Failure Criteria & Troubleshooting
编译失败→检查 aes_core; 复位时序不可控→调整 rst_ni 拉低时机

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
