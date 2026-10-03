# Verification Workorder: VULN-015

## Metadata
- VULN-ID: VULN-015
- Title: Ascon EDN 完全断开——PRD/随机掩码不可用
- IP: ascon
- Root Cause Type: fixed-value-signal
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/edn_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/ascon.sv

### Stimulus Sequence
组合逻辑: 检查 edn_req 是否恒 0; 检查 edn_data 是否未进入任何数据通路

### Success Criteria (machine-checkable)
vuln: edn_req=1'b0 (恒零), edn_data 未消费; twin: edn_req 由状态机驱动; 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 ascon 依赖链; edn_req 不可观测→加输出端口

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
