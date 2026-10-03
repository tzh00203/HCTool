# Verification Workorder: VULN-049

## Metadata
- VULN-ID: VULN-049
- Title: Ascon valid_bytes>15 无范围检查 + data_out_ready_i unused
- IP: ascon
- Root Cause Type: —
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L4

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/prim_ascon_duplex.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/prim_ascon_duplex.sv

### Stimulus Sequence
驱动 valid_bytes=16 → 检查 bin2thermo 输出

### Success Criteria (machine-checkable)
vuln: bin2thermo 全1, padding 被跳过; twin: 正确处理; 差分输出

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
