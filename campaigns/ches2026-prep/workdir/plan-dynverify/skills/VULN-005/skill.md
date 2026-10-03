# Verification Workorder: VULN-005

## Metadata
- VULN-ID: VULN-005
- Title: AES SecAllowForcingMasks 硬编码 1——SW 可冻结掩码 PRNG，一阶掩码对策失效
- IP: aes
- Root Cause Type: constant-replaces-dynamic
- CVSS Tier: Critical

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L2

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_core.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_prng_masking.sv

Stubs:
  - (none)

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes.sv

### Stimulus Sequence
组合逻辑: 写 FORCE_MASKS=1 → 检查 SecAllowForcingMasks 参数值; 检查掩码 PRNG 输出是否冻结为常量

### Success Criteria (machine-checkable)
vuln: SecAllowForcingMasks=1 (硬编码); twin: SecAllowForcingMasks=0 (参数传递); PRNG freeze 检测: 连续两周期 mask_out 相同

### Failure Criteria & Troubleshooting
编译失败→检查 aes 参数列表; PRNG 输出不可观测→XMR probe prng_data_o

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
