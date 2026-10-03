# Verification Workorder: VULN-080

## Metadata
- VULN-ID: VULN-080
- Title: UART Break FSM 无 FSM.LOCAL_ESC / TX override 无安全门控 / NCO=0 静默停转
- IP: uart
- Root Cause Type: sec-cm-mismatch
- CVSS Tier: Low

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
各 micro-tb: 非法态恢复 / TX override / NCO=0

### Success Criteria (machine-checkable)
SEC_CM 缺失 / 无安全门控 / 无错误指示→info; exit code: 0

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
