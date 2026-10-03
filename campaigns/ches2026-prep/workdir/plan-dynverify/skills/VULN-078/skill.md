# Verification Workorder: VULN-078

## Metadata
- VULN-ID: VULN-078
- Title: rom_ctrl SVA 禁用 / MUX strict/loose / rom_data_i 宽度硬编码 / mux alert 粘性矛盾
- IP: rom_ctrl
- Root Cause Type: hjson-spec-vs-rtl
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L4

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl.sv

### Stimulus Sequence
各 micro-tb + 代码审计: SVA 禁用条件 / strict vs loose / 宽度 / alert 粘性

### Success Criteria (machine-checkable)
约束降级 / 结构脆弱→info; exit code: 0

### Failure Criteria & Troubleshooting
编译失败→检查 rom_ctrl 依赖链

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
