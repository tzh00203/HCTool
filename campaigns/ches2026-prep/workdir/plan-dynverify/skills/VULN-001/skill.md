# Verification Workorder: VULN-001

## Metadata
- VULN-ID: VULN-001
- Title: ibex 特权检查完全旁路——U-mode 可读写所有 M-only CSR + 级联绕过 3 个 SEC_CM + 调试特权升级
- IP: ibex
- Root Cause Type: check-bypass
- CVSS Tier: Critical

## Verification Plan

### TB Type
- **Type**: tb_seq
- **Fidelity Target**: L1

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_pmp.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_tracer_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/vendor/lowrisc_ibex/rtl/ibex_cs_registers.sv

### Stimulus Sequence
FSM 驱 priv_lvl=U → 写 mstatus/MPP → MRET → 检查特权提升；写 CPUCTRLSTS 清 data_ind_timing/dummy_instr_en → 检查 SEC_CM 失效；写 DCSR.ebreakm=1 → 检查调试特权升级

### Success Criteria (machine-checkable)
vuln: illegal_csr_insn_o=0, csr_we_int=1 (U-mode写入放行); twin: illegal_csr_insn_o=1, csr_we_int=0 (正确拒绝); verdict信号: vuln_privilege_bypass=1

### Failure Criteria & Troubleshooting
编译失败→检查 ibex 文件路径和 prim 导入; verdict 不反→确认 priv_lvl 切换时序正确, XMR probe csr_we_int 信号路径

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
