# Verification Workorder: VULN-050

## Metadata
- VULN-ID: VULN-050
- Title: Ascon SCA: data_out/tag_out 无 blinding + S-box 无掩码
- IP: ascon
- Root Cause Type: —
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_seq
- **Fidelity Target**: L3

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/prim_ascon_duplex.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/ascon/rtl/prim_ascon_duplex.sv

### Stimulus Sequence
DPA 攻击模拟: 多次加密相同明文 → 检查输出掩码变化

### Success Criteria (machine-checkable)
vuln: 输出无掩码 (确定性); twin: 输出有掩码 (随机化); 差分统计

### Failure Criteria & Troubleshooting
编译失败→检查 duplex 依赖

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
