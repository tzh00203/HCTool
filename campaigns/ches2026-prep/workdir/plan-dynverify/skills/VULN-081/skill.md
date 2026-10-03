# Verification Workorder: VULN-081

## Metadata
- VULN-ID: VULN-081
- Title: UART rxilvl=7 使 rx_watermark 永不触发 / EnableRacl=0 退化为无权限
- IP: uart
- Root Cause Type: —
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L4

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_core.sv

### Stimulus Sequence
micro-tb: 写 rxilvl=7 → 检查 watermark; 检查 EnableRacl 默认值

### Success Criteria (machine-checkable)
rxilvl=7 使 watermark 失效 / RACL 默认关闭→info; exit code: 0

### Failure Criteria & Troubleshooting
编译失败→检查 uart_core

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
