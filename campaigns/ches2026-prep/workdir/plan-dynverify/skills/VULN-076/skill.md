# Verification Workorder: VULN-076

## Metadata
- VULN-ID: VULN-076
- Title: otp_ctrl part_buf ecc_err→ErrorSt 不设 fsm_err_o / KDI nonce 索引 / OTP 宏命令 sparse 编码
- IP: otp_ctrl
- Root Cause Type: —
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L4

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_part_buf.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_part_buf.sv

### Stimulus Sequence
micro-tb + 脚本验证: FSM 断言 / nonce 索引 / 命令码 HD

### Success Criteria (machine-checkable)
断言漏检 / 已验证通过→info; exit code: 0

### Failure Criteria & Troubleshooting
编译失败→检查 otp_ctrl 依赖链

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
