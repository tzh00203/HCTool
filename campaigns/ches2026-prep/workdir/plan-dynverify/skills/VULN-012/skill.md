# Verification Workorder: VULN-012

## Metadata
- VULN-ID: VULN-012
- Title: KMAC MSG.MASKING 常量替换动态掩码
- IP: kmac
- Root Cause Type: constant-replaces-dynamic
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/edn_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac.sv

### Stimulus Sequence
组合逻辑: 检查 g_msg_mask 块中 static_mask vs msg_mask 使用; EnMasking=1, cfg_msg_mask=1 时检查实际掩码值

### Success Criteria (machine-checkable)
vuln: msg_mask_used = {MsgWidth{1'b1}} (static_mask 常量); twin: msg_mask_used = LFSR 动态输出; 差分输出: vuln 掩码确定性 vs twin 掩码随机

### Failure Criteria & Troubleshooting
编译失败→检查 kmac 依赖链; msg_mask 信号不可观测→XMR probe g_msg_mask 块输出

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
