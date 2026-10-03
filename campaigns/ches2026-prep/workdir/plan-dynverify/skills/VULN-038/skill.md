# Verification Workorder: VULN-038

## Metadata
- VULN-ID: VULN-038
- Title: UART lsio_trigger_o 无条件赋常量 1'b1
- IP: uart
- Root Cause Type: fixed-value-signal
- CVSS Tier: Medium

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/uart/rtl/uart_core.sv

### Stimulus Sequence
组合逻辑: 驱动 RX FIFO 低于/高于 watermark → 观测 lsio_trigger_o

### Success Criteria (machine-checkable)
vuln: lsio_trigger_o=1'b1 (恒常量); twin: lsio_trigger_o=rx_watermark|tx_watermark (条件触发); 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 uart_core 依赖; watermark 信号不可观测→XMR probe

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
