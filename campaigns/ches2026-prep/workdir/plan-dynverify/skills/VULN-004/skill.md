# Verification Workorder: VULN-004

## Metadata
- VULN-ID: VULN-004
- Title: lc_ctrl Token 比较截断 128→32 位——碰撞空间从 2^128 降至 2^32
- IP: lc_ctrl
- Root Cause Type: width-truncation
- CVSS Tier: Critical

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_pkg.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_state_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/lc_ctrl_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/lc_ctrl/rtl/lc_ctrl_fsm.sv

### Stimulus Sequence
组合逻辑: 构造两个仅高96位不同的128位token (token_a[31:0]=token_b[31:0], token_a[127:32]≠token_b[127:32]) → 驱动 TokenHashSt → 检查比较结果

### Success Criteria (machine-checkable)
vuln: token_match=1 (截断比较判等); twin: token_match=0 (全宽比较判不等); 差分输出: vuln_match≠twin_match

### Failure Criteria & Troubleshooting
编译失败→检查 LcTokenWidth 参数; TokenHashSt 状态不可达→简化为组合表达式级 micro-tb

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
