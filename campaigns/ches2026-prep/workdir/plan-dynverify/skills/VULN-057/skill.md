# Verification Workorder: VULN-057

## Metadata
- VULN-ID: VULN-057
- Title: HMAC wipe_v 来自 SW 非 PRD + SEC_CM 仅 BUS.INTEGRITY
- IP: hmac
- Root Cause Type: sec-cm-mismatch
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L4

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac.sv

### Stimulus Sequence
grep SEC_CM 声明列表 → 确认仅 BUS.INTEGRITY

### Success Criteria (machine-checkable)
SEC_WIPE 等无声明→确认; exit code: 0 (info only)

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
