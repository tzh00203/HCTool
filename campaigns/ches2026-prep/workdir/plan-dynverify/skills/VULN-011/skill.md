# Verification Workorder: VULN-011

## Metadata
- VULN-ID: VULN-011
- Title: HMAC WIPE_SECRET 读取泄露 key[0]
- IP: hmac
- Root Cause Type: check-bypass
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
组合逻辑: 读 WIPE_SECRET CSR 地址 (addr_hit[8]) → 检查 rdata 是否返回 key[0]#q 值

### Success Criteria (machine-checkable)
vuln: rdata = key[0] (密钥泄露); twin: rdata = 0 或所有位相同 (只写寄存器正确行为); 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 hmac_reg_top 文件路径; addr_hit[8] 不可达→用简化组合逻辑

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
