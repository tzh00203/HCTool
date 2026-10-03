# Verification Workorder: VULN-002

## Metadata
- VULN-ID: VULN-002
- Title: PMP pmp_req_err_o 恒零——PMP 永不拒绝内存访问
- IP: ibex
- Root Cause Type: fixed-value-signal
- CVSS Tier: Critical

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
组合逻辑: 配置 PMP region 0 拒绝地址 0x20000000 (pmpaddr+ pmpcfg.L=1,X=0,R=0,W=0) → 从该地址访问 → 检查 pmp_req_err_o

### Success Criteria (machine-checkable)
vuln: pmp_req_err_o=0 (永不拒绝); twin: pmp_req_err_o=1 (正确拒绝); exit code 差分: vuln_exit≠twin_exit

### Failure Criteria & Troubleshooting
编译失败→检查 ibex_pmp 参数化; pmp_req_err 信号不可观测→加 XMR probe 或输出端口

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
