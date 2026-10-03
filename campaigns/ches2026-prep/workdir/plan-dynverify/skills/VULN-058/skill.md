# Verification Workorder: VULN-058

## Metadata
- VULN-ID: VULN-058
- Title: HMAC done_state 冷却计数器不重置
- IP: hmac
- Root Cause Type: —
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_seq
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac.sv

### Stimulus Sequence
时序: hash_running 重拉高 → 检查 cool_down_ct_q 是否保留

### Success Criteria (machine-checkable)
vuln: cool_down_ct_q 保留; twin: cool_down_ct_q 重置; 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 hmac

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
