# Verification Workorder: VULN-039

## Metadata
- VULN-ID: VULN-039
- Title: HMAC err_code priority case 重复项 + invalid_config 无 err_code 分支
- IP: hmac
- Root Cause Type: structural-anomaly
- CVSS Tier: Medium

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L4

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac.sv

### Stimulus Sequence
组合逻辑: 配置无效 digest_size → hash_start → 检查 err_code

### Success Criteria (machine-checkable)
vuln: err_code=NoError (invalid_config 无分支); twin: err_code=InvalidConfig; 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 hmac 依赖; invalid_config 不可达→直接驱动

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
