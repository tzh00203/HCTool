# Verification Workorder: VULN-040

## Metadata
- VULN-ID: VULN-040
- Title: otp_ctrl scrmble FSM ErrorSt 不清敏感内部状态
- IP: otp_ctrl
- Root Cause Type: fsm-error-handling
- CVSS Tier: Medium

## Verification Plan

### TB Type
- **Type**: tb_seq
- **Fidelity Target**: L1

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_scrmbl.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_scrmbl.sv

### Stimulus Sequence
时序: 使 scrmbl FSM 进入 ErrorSt → DPI 探测 key_state_q 是否保持错误前值

### Success Criteria (machine-checkable)
vuln: key_state_q 保持 (残留); twin: key_state_q=0 (正确清除); verdict 信号差分

### Failure Criteria & Troubleshooting
编译失败→检查 otp_ctrl_scrmbl; ErrorSt 不可达→直接驱动 state_q

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
