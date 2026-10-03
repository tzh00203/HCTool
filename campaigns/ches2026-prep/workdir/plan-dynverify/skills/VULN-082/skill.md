# Verification Workorder: VULN-082

## Metadata
- VULN-ID: VULN-082
- Title: UART rx_fifo_wvalid 门控 / reg_we_check 只读寄存器 / TX/RX baud 不一致 / SEC_CM 声明稀疏
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
micro-tb + lint: rx_fifo_wvalid / we_check / baud / SEC_CM

### Success Criteria (machine-checkable)
功能正确但结构脆弱→info; exit code: 0

### Failure Criteria & Troubleshooting
编译失败→检查 uart 依赖链

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
