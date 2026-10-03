# Verification Workorder: VULN-052

## Metadata
- VULN-ID: VULN-052
- Title: entropy_src rng_bit_sel 被 health_test_window[0] 掩码
- IP: entropy_src
- Root Cause Type: —
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L4

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/edn_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv

### Stimulus Sequence
rng_bit_en=1, rng_bit_sel=2'b01 → 观测实际选择位

### Success Criteria (machine-checkable)
vuln: 选择位被掩码修改; twin: 选择位未修改; 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 entropy_src_core

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
