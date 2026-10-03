# Verification Workorder: VULN-032

## Metadata
- VULN-ID: VULN-032
- Title: KMAC hjson 缺 MSG.MASKING SEC_CM 声明
- IP: kmac
- Root Cause Type: sec-cm-mismatch
- CVSS Tier: Medium

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L4

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/data/kmac.hjson

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/data/kmac.hjson

### Stimulus Sequence
grep hjson countermeasures 列表 'MSG.MASKING' → 确认缺失

### Success Criteria (machine-checkable)
countermeasures 列表无 MSG.MASKING (确认); hjson:558 msg_mask 字段存在; exit code: grep 无匹配→exit 1

### Failure Criteria & Troubleshooting
hjson 路径错误→检查文件位置

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
