# Verification Workorder: VULN-069

## Metadata
- VULN-ID: VULN-069
- Title: KMAC lc_escalate 传播延迟 / process_latched 清除逻辑
- IP: kmac
- Root Cause Type: —
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L4

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/edn_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac.sv

### Stimulus Sequence
2-sync 延迟是跨时钟域必要代价 → 非漏洞

### Success Criteria (machine-checkable)
设计意图→info; exit code: 0

### Failure Criteria & Troubleshooting
需理解跨时钟域设计

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
