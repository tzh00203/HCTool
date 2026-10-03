# Verification Workorder: VULN-046

## Metadata
- VULN-ID: VULN-046
- Title: Ascon STATUS.stall/wait_edn 恒零
- IP: ascon
- Root Cause Type: hjson-spec-vs-rtl
- CVSS Tier: Low

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
产生未读输出 → 检查 STATUS.STALL

### Success Criteria (machine-checkable)
vuln: STATUS.STALL=0 (恒零); twin: STATUS.STALL=1 (反映真实状态); 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 ascon_core

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
