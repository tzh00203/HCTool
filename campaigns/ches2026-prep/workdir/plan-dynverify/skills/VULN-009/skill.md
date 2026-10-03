# Verification Workorder: VULN-009

## Metadata
- VULN-ID: VULN-009
- Title: HMAC wipe_secret_we 门控极性反转
- IP: hmac
- Root Cause Type: gate-inversion
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac_reg_top.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac_reg_top.sv

### Stimulus Sequence
组合逻辑: 驱动 reg_error=0 (正常 TL-UL) → 检查 wipe_secret_we 值; 驱动 reg_error=1 → 检查 wipe_secret_we 值

### Success Criteria (machine-checkable)
vuln: wipe_secret_we = reg_error (极性反转: 正常=0, 错误=1); twin: wipe_secret_we = !reg_error (正确: 正常=1, 错误=0); 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 hmac_reg_top 文件路径; wipe_secret_we 信号不可观测→加输出端口或 XMR

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
