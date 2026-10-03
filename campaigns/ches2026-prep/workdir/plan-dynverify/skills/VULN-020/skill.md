# Verification Workorder: VULN-020

## Metadata
- VULN-ID: VULN-020
- Title: PMP access_fault_check MMWP/MML 默认拒绝语义未实现
- IP: ibex-pmp
- Root Cause Type: hjson-spec-vs-rtl
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
组合逻辑: 配置 MMWP=1, 无 region 匹配, M-mode READ → 检查 access_fault_check 返回值

### Success Criteria (machine-checkable)
vuln: return=allow (默认允许); twin: return=fault (默认拒绝); 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 ibex_pmp 参数; mmwp 参数不可驱动→直接传入组合函数输入

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
