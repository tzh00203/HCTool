# Verification Workorder: VULN-028

## Metadata
- VULN-ID: VULN-028
- Title: otp_ctrl 3 个 SVA 断言注释降级 + fatal_prim_otp_alert 未纳入 fatal 错误锁存
- IP: otp_ctrl
- Root Cause Type: sec-cm-mismatch
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_seq
- **Fidelity Target**: L1

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl.sv

### Stimulus Sequence
时序: 使 otp_macro_i.fatal_alert=1 持续 1 周期后拉低 → 观测 (a) alert 是否持续 (b) FSM 是否进入 ErrorSt

### Success Criteria (machine-checkable)
vuln: alert 不持续 (未锁存), FSM 不进 ErrorSt; twin: alert 持续, FSM 进 ErrorSt; verdict 信号差分

### Failure Criteria & Troubleshooting
编译失败→检查 otp_ctrl 大文件依赖; fatal_alert 不可驱动→用简化组合逻辑

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
