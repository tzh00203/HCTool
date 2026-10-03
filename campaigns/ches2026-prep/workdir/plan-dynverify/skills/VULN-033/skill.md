# Verification Workorder: VULN-033

## Metadata
- VULN-ID: VULN-033
- Title: KMAC StTerminalError 延迟 100 周期才置 sparse_fsm_error_o
- IP: kmac
- Root Cause Type: fsm-error-handling
- CVSS Tier: Medium

## Verification Plan

### TB Type
- **Type**: tb_seq
- **Fidelity Target**: L1

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/edn_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac_core.sv

### Stimulus Sequence
时序: 注入 sparse FSM error pulse → 计数 sparse_fsm_error_o 置 1 所需周期数

### Success Criteria (machine-checkable)
vuln: sparse_fsm_error_o 延迟 100 周期; twin: sparse_fsm_error_o 立即置 1; 计数器差分

### Failure Criteria & Troubleshooting
编译失败→检查 kmac_core 依赖; error 注入不可达→直接驱动 st_err_ct

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
