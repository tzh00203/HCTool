# Verification Workorder: VULN-022

## Metadata
- VULN-ID: VULN-022
- Title: mseccfg MML/MMWP 缺 sticky-one 语义
- IP: ibex
- Root Cause Type: sticky-bit-removal
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_seq
- **Fidelity Target**: L1

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_pmp.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv

### Stimulus Sequence
时序: 写 MML=1 → 读回确认 → 写 MML=0 → 读回; 写 MMWP=1 → 写 MMWP=0 → 读回

### Success Criteria (machine-checkable)
vuln: 读回 0 (SW 可清已置位); twin: 读回 1 (sticky-one, 不可清); verdict 信号差分

### Failure Criteria & Troubleshooting
编译失败→检查 ibex_cs_registers; CSR 写入不生效→检查 csr_we_int 时序

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
