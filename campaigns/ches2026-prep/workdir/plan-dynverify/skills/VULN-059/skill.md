# Verification Workorder: VULN-059

## Metadata
- VULN-ID: VULN-059
- Title: HMAC FIFO 硬件侧写入不受 msg_allowed 门控
- IP: hmac
- Root Cause Type: —
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L4

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/hmac/rtl/hmac.sv

### Stimulus Sequence
存疑: 正常路径不会在非运行状态进入 StPushToMsgFifo → 无需验证

### Success Criteria (machine-checkable)
exit code: 0 (info only, 正常路径不触发)

### Failure Criteria & Troubleshooting
需理解 FSM 状态转换

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
