# Verification Workorder: VULN-030

## Metadata
- VULN-ID: VULN-030
- Title: Ascon KEY/NONCE SEC_WIPE 用全零而非 PRD
- IP: ascon
- Root Cause Type: constant-replaces-dynamic
- CVSS Tier: Medium

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
组合逻辑: 触发 SEC_WIPE → 检查 KEY/NONCE share0/share1 清除值是否为 '0

### Success Criteria (machine-checkable)
vuln: clear_value='0 (全零非 PRD); twin: clear_value=edn_data (PRD); 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 ascon_core 依赖; EDN 断开使 PRD 不可达→与 VULN-015 联动

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
