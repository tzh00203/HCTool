# VULN-037 — RESULT

## Verdict: **[poc-success]** L2 fidelity

## Finding

rom_ctrl.sv `SecDisableScrambling=1` branch (gen_fsm_scramble_disabled):
- Line 386: `assign pwrmgr_data_o = PWRMGR_DATA_DEFAULT` → `{done: MuBi4True, good: MuBi4True}`
- Line 400: `assign checker_alert = 1'b0;`

When scrambling is disabled, pwrmgr receives done=True/good=True — indicating ROM
integrity check passed — even though both the scrambling block and the checker FSM
are completely bypassed. No alert is raised. This is a sec-cm-mismatch: all security
countermeasures are disabled but the system proceeds as if verification succeeded.

## Twin Repair

- Line 386: `pwrmgr_data_o.done = MuBi4False` (check not actually performed)
- Line 400: `checker_alert = 1'b1` (alert fires when security disabled)

Oracle: SVA `NoReadsBeforeDone_A` (done=True implies check was performed),
SVA `PwrmgrDataChk_A` (done never de-asserted once asserted),
line 20 comment: "Don't use this in a real chip".

## Reproduction

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-037
bash build_rom_scram_disable.sh
# exit code 1 = finding confirmed
```

## Raw Output

```
SecDisableScrambling=1: vuln_done=True(vuln) done=False(twin)  vuln_alert=0(twin=1)
vuln_deviation: YES  twin_secure: YES
CONFIRMED: rom_ctrl.sv SecDisableScrambling=1 sets pwrmgr_data_o.done=MuBi4True
and checker_alert=0, telling pwrmgr the ROM check passed even though
scrambling and the checker FSM are completely bypassed.
Twin: done=MuBi4False (check not performed) + checker_alert=1 (alert fires).
Oracle: SVA NoReadsBeforeDone_A + PwrmgrDataChk_A + line 20 comment.
exit code: 1 (1 = finding confirmed)
```

## Twin Diff Summary

Only 2 lines changed (within gen_fsm_scramble_disabled branch):
1. `pwrmgr_data_o.done`: MuBi4True → MuBi4False (line 386)
2. `checker_alert`: 1'b0 → 1'b1 (line 400)
Oracle: SVA NoReadsBeforeDone_A + PwrmgrDataChk_A + line 20 comment
