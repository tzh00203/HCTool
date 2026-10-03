# Verification Workorder: VULN-014

## Metadata
- VULN-ID: VULN-014
- Title: Ascon WIPE 触发完全丢弃 + ERROR 寄存器不可清除
- IP: ascon
- Root Cause Type: hjson-spec-vs-rtl
- CVSS Tier: High

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
组合逻辑: 写 TRIGGER.WIPE=1 → 检查 wipe 信号是否到达 key/nonce/state 清除逻辑; 检查 hw2reg.trigger.wipe.d 是否为 0

### Success Criteria (machine-checkable)
vuln: wipe→unused_wipe (丢弃), 寄存器不变; twin: wipe→清除逻辑, 寄存器被覆写; 差分: vuln_key_before==vuln_key_after, twin_key_before≠twin_key_after

### Failure Criteria & Troubleshooting
编译失败→检查 ascon_core 依赖; wipe 信号不可追踪→XMR probe

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
