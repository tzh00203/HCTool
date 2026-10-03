# Verification Workorder: VULN-010

## Metadata
- VULN-ID: VULN-010
- Title: HMAC SHA2_512 外层轮消息长度计算错误
- IP: hmac
- Root Cause Type: crypto-functional-wrong
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_dpi
- **Fidelity Target**: L1

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac_core.sv

### Stimulus Sequence
DPI 差分: 对比 OpenSSL HMAC-SHA512 输出; 驱动 SHA2_512 模式 HMAC 计算

### Success Criteria (machine-checkable)
vuln: RTL HMAC-SHA512 output ≠ OpenSSL reference; twin: output 匹配; exit code 差分

### Failure Criteria & Troubleshooting
DPI 编译失败→检查 OpenSSL 链接; HMAC 未完成→增加仿真周期数

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
