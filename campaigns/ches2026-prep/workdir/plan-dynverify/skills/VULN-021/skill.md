# Verification Workorder: VULN-021

## Metadata
- VULN-ID: VULN-021
- Title: PMP debug 地址窗口 | 误用——debug 窗口永不匹配
- IP: ibex-pmp
- Root Cause Type: structural-anomaly
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_pmp.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_pmp.sv

### Stimulus Sequence
组合逻辑: 驱动 debug_mode=1 + DM 地址 (DmBaseAddr=0x1A110000) → XMR probe debug_address_range_match

### Success Criteria (machine-checkable)
vuln: debug_address_range_match=0 (| 误用, 永不匹配); twin: debug_address_range_match=1 (& 正确, 匹配); 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 ibex_pmp; DmBaseAddr 不可参数化→硬编码测试值

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
