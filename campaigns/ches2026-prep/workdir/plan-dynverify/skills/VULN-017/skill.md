# Verification Workorder: VULN-017

## Metadata
- VULN-ID: VULN-017
- Title: entropy_src markov_ht fail_pulse 硬布零
- IP: entropy_src
- Root Cause Type: fixed-value-signal
- CVSS Tier: High

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_markov_ht.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_pkg.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/entropy_src/rtl/entropy_src_markov_ht.sv

### Stimulus Sequence
组合逻辑: 注入已知 Markov 失败模式 (cnt>thresh, active=1, wrap=1) → 观测 test_fail_hi/lo_pulse_o

### Success Criteria (machine-checkable)
vuln: test_fail_hi_pulse_o=0, test_fail_lo_pulse_o=0 (硬布零); twin: test_fail_hi_pulse_o=1 或 lo=1 (正确触发); 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 entropy_src_markov_ht 依赖; 阈值不满足→调整 test_cnt 和 thresh 值

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
