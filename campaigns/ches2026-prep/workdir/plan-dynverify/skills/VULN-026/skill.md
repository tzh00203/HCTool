# Verification Workorder: VULN-026

## Metadata
- VULN-ID: VULN-026
- Title: otp_ctrl DAI 命令解码 empty default 吞没 5 个无效编码
- IP: otp_ctrl
- Root Cause Type: check-bypass
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_dai.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_dai.sv

### Stimulus Sequence
组合逻辑: 向 DAI 发送无效命令编码 (dai_cmd_e 3/8 未定义值) → 观测 FSM 状态和错误信号

### Success Criteria (machine-checkable)
vuln: FSM 留 IdleSt, fsm_err_o=0 (无错误); twin: FSM 跳 ErrorSt, fsm_err_o=1 (正确报错); 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 otp_ctrl_dai 路径; 无效编码不可注入→直接驱动 dai_cmd_i

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
