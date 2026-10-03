# Verification Workorder: VULN-018

## Metadata
- VULN-ID: VULN-018
- Title: entropy_src SHA3 lc_escalate_en_i 硬布 Off
- IP: entropy_src
- Root Cause Type: constant-replaces-dynamic
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_seq
- **Fidelity Target**: L1

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/edn_pkg_stub.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/lc_ctrl_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv

### Stimulus Sequence
时序: SHA3 吸收过程中注入 lc_escalate_en=On → 观测 SHA3 是否停止; negedge 采样

### Success Criteria (machine-checkable)
vuln: SHA3 继续运行 (lc_escalate 被硬布 Off 忽略); twin: SHA3 停止/进入 error; verdict 信号差分

### Failure Criteria & Troubleshooting
编译失败→检查 entropy_src_core 大文件依赖链; SHA3 实例不可控→XMR 探 sha3 状态机

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
