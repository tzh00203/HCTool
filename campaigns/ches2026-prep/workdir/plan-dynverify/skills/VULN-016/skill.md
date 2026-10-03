# Verification Workorder: VULN-016

## Metadata
- VULN-ID: VULN-016
- Title: Ascon nonce_error 不阻塞 start_ok——nonce 重用导致 AEAD 安全性失效
- IP: ascon
- Root Cause Type: check-bypass
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv

### Stimulus Sequence
组合逻辑: nonce_error=1 (未加载 nonce) → 触发 START → 检查 start_ok 是否为 1

### Success Criteria (machine-checkable)
vuln: start_ok=1 (nonce 错误不阻塞); twin: start_ok=0 (正确拒绝); 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 ascon_core; nonce_error 不可达→直接驱动信号

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
