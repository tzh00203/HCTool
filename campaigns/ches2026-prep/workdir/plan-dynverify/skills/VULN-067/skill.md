# Verification Workorder: VULN-067

## Metadata
- VULN-ID: VULN-067
- Title: KMAC sha3pad SVA 被注释 + msg_mask 信号悬空
- IP: kmac
- Root Cause Type: hjson-spec-vs-rtl
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
micro-tb + lint 确认: grep SVA 注释 / msg_mask 连接

### Success Criteria (machine-checkable)
SVA 降级 + 信号悬空→确认; exit code: 0 (info)

### Failure Criteria & Troubleshooting
grep 路径错误

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
