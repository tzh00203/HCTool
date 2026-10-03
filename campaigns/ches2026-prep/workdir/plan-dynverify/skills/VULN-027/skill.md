# Verification Workorder: VULN-027

## Metadata
- VULN-ID: VULN-027
- Title: otp_ctrl scrmbl 命令解码 empty default 吞没 2 个无效编码
- IP: otp_ctrl
- Root Cause Type: check-bypass
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_scrmbl.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/top_earlgrey/ip_autogen/otp_ctrl/rtl/otp_ctrl_scrmbl.sv

### Stimulus Sequence
组合逻辑: 向 scrmbl 发送无效命令编码 → 观测 FSM 状态和错误信号

### Success Criteria (machine-checkable)
vuln: FSM 留 IdleSt (ignore); twin: FSM 跳 ErrorSt; 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 otp_ctrl_scrmbl 路径; 无效编码不可注入→直接驱动

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
