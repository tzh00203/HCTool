# Verification Workorder: VULN-041

## Metadata
- VULN-ID: VULN-041
- Title: AES CTR FSM 延迟 100 周期告警
- IP: aes
- Root Cause Type: fsm-error-handling
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_seq
- **Fidelity Target**: L1

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_ctr_fsm.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_ctr_fsm.sv

### Stimulus Sequence
时序: 注入 incr_err → 计数 alert_o 延迟周期数

### Success Criteria (machine-checkable)
vuln: alert_o 延迟 100 周期; twin: alert_o 立即; 计数差分

### Failure Criteria & Troubleshooting
编译失败→检查 aes_ctr_fsm

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
