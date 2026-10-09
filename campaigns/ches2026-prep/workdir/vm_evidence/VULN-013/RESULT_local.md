# RESULT: VULN-013

## Verdict
**[poc-success]** — finding confirmed. L2 fidelity.

## Vulnerability
keymgr_ctrl.sv:291-292: In `key_output_ctrl`, when `invalid_stage_sel_o && (state_q == StCtrlInvalid)`,
the code sets `key_o.key[i] = key_state_q[cdi_sel_o][i]`, directly exposing key material
without entropy masking. The correct behavior (shown in the else branch at lines 294-295)
is to output `{EntropyRounds{entropy_i[i]}}` (entropy mask) for all invalid stages,
preventing key exposure in error states.

## Twin Fix
Change line 291-292 from:
```systemverilog
if (invalid_stage_sel_o && (state_q == StCtrlInvalid)) begin
  key_o.key[i] = key_state_q[cdi_sel_o][i];
```
to:
```systemverilog
if (invalid_stage_sel_o && (state_q == StCtrlInvalid)) begin
  key_o.key[i] = {EntropyRounds{entropy_i[i]}};
```
Oracle: Lines 294-295 show the correct masking pattern for invalid stages — output entropy,
not key_state. StCtrlInvalid is an error state where key must never be exposed unmasked.

## Evidence
```
StCtrlInvalid + invalid_stage_sel: vuln exposes key: YES  twin masks with entropy: YES
CONFIRMED: keymgr_ctrl.sv:291-292 key_output_ctrl exposes unmasked key_state_q
when state_q==StCtrlInvalid && invalid_stage_sel_o.
Vuln outputs key_state_q directly (no entropy XOR), leaking key material.
Twin outputs {EntropyRounds{entropy_i[i]}} (entropy mask), consistent with
line 294-295 which masks key for all other invalid-stage cases.
exit code: 1 (1 = finding confirmed)
```

## Reproduction
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-013
bash build.sh
# Expected: exit code 1 (finding confirmed)
```

## Deliverables
- `tb_keymgr_invalid_expose.sv` — combinational micro-tb (vuln + twin inline expressions)
- `sim_main.cpp` — C++ simulation driver
- `build.sh` — Verilator build script
- `exploit.py` — PoC entry (redbud mode)
