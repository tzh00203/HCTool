# Verification Workorder: VULN-034

## Metadata
- VULN-ID: VULN-034
- Title: AES state default 条件化
- IP: aes
- Root Cause Type: sec-cm-mismatch
- CVSS Tier: Medium

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_cipher_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_cipher_core.sv

### Stimulus Sequence
组合逻辑: 注入非法 state_sel 值, AES-128 模式 → 检查 state_q 赋值源

### Success Criteria (machine-checkable)
vuln: state_d = state_q (自保持, 条件化); twin: state_d = prd_clearing_state_i (无条件 PRD); 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 aes_cipher_core; state_sel 不可注入→直接驱动

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
