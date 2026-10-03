# Verification Workorder: VULN-029

## Metadata
- VULN-ID: VULN-029
- Title: Ascon lc_escalate_en_i 被 unused
- IP: ascon
- Root Cause Type: sec-cm-mismatch
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
组合逻辑: 拉高 lc_escalate_en_i → 观测 alert[1] 是否变化

### Success Criteria (machine-checkable)
vuln: alert[1] 不变 (lc escalation 无响应); twin: alert[1] 触发; 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 ascon_core 依赖

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
