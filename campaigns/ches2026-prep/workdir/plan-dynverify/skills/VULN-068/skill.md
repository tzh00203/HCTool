# Verification Workorder: VULN-068

## Metadata
- VULN-ID: VULN-068
- Title: KMAC en_unsupported_modestrength 可绕过检查 / kmac_app Error 态仍接受数据
- IP: kmac
- Root Cause Type: —
- CVSS Tier: Low

## Verification Plan

### TB Type
- **Type**: tb_comb
- **Fidelity Target**: L4

### Dependency File List
DUT + prim chain:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac_errchk.sv
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac_pkg.sv

Stubs:
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/templates/stubs/edn_pkg_stub.sv

### Locations
  - /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac_errchk.sv

### Stimulus Sequence
写 en_unsupported_modestrength=1 → 检查 mode+strength 检查是否被绕过

### Success Criteria (machine-checkable)
vuln: 检查被绕过; twin: 检查仍生效; 差分输出

### Failure Criteria & Troubleshooting
编译失败→检查 kmac_errchk

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
