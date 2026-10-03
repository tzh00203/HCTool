# Verification Workorder: VULN-047

## Metadata
- VULN-ID: VULN-047
- Title: Ascon ascon_operation 在 duplex FSM 中未使用
- IP: ascon
- Root Cause Type: hjson-spec-vs-rtl
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/prim_ascon_duplex.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/prim_ascon_duplex.sv

### Stimulus Sequence
设 operation=ASCON_HASH → 检查输出是否等于 ASCON_ENC

### Success Criteria (machine-checkable)
vuln: 输出相同 (operation 被忽略); twin: 输出不同; 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 prim_ascon_duplex

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
