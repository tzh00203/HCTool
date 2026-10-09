# RESULT: VULN-018

## Verdict
**[poc-success]** Finding confirmed. exit 1.

## Vulnerability
entropy_src_core.sv:2770 — SHA3 instance `u_sha3` has `lc_escalate_en_i` hardcoded to `lc_ctrl_pkg::Off`.

## Impact
SHA3 conditioner never responds to lifecycle escalation. When `lc_escalate_en=On` is asserted
(e.g., by lifecycle controller during security escalation), SHA3 continues running instead of
entering error state / halting. This breaks the escalation security guarantee — compromised
lifecycle state cannot force SHA3 to stop processing.

## Twin Repair
Changed `.lc_escalate_en_i (lc_ctrl_pkg::Off)` to `.lc_escalate_en_i (lc_escalate_en_i)`,
routing the actual module input to SHA3. Oracle: sibling modules (kmac, otbn) pass
`lc_escalate_en_i` through to their SHA3 instances; SHA3 module has `lc_escalate_en_i` port
specifically designed for dynamic lifecycle escalation input.

## Verification Method
- **Type**: Combinational micro-tb (L2 data-flow fidelity)
- **Approach**: Direct signal comparison — drive `lc_escalate_en_i = On`, observe that
  vuln SHA3 always sees `Off` (escalation ignored) while twin SHA3 sees `On` (escalation triggers)
- **Fidelity**: L2 (constant-replaces-dynamic signal routing)

## Evidence
```
lc_escalate_en_i=On: vuln ignores escalate: YES  twin responds escalate: YES
CONFIRMED: entropy_src_core.sv:2770 SHA3 lc_escalate_en_i hardcoded to Off
exit code: 1 (1 = finding confirmed)
```

## Build Command
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-018
bash build.sh
```

## Files
- `tb_entropy_src_lc_escalate.sv` — micro-tb (vuln + twin dual comparison)
- `sim_main.cpp` — C++ driver
- `build.sh` — Verilator build script
- `lc_ctrl_pkg_stub.sv` — lc_ctrl_pkg stub
- `exploit.py` — redbud-mode PoC entry
