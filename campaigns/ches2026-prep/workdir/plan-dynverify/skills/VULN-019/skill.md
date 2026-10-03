# Verification Workorder: VULN-019

## Metadata
- VULN-ID: VULN-019
- Title: entropy_src es_rng_src_valid 被 entropy_data_reg_enable 门控
- IP: entropy_src
- Root Cause Type: hjson-spec-vs-rtl
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/edn_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_core.sv

### Stimulus Sequence
组合逻辑: 设置 entropy_data_reg_enable=0 → enable 模块 → 观测 esrng FIFO push 信号

### Success Criteria (machine-checkable)
vuln: es_rng_src_valid=0 (门控阻断), sfifo_esrng_push=0; twin: es_rng_src_valid=1 (正常), sfifo_esrng_push=1; 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 entropy_src_core 依赖链; FIFO push 不可观测→XMR probe

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
