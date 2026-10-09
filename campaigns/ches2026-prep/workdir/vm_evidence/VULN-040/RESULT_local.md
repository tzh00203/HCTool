# VULN-040 — Dynamic Verification Result

## Verdict: **[poc-success]** — L2 data-flow evidence

## Finding
otp_ctrl_scrmbl.sv:421-423 ErrorSt only sets `fsm_err_o=1`. All register enable signals (`key_state_en`, `data_state_en`, `digest_state_en`) remain at their default values of 0, so `key_state_q`, `data_state_q`, `digest_state_q` retain pre-error values. Sensitive key material and scrambling state survive in the terminal error state.

## Twin Fix
- **Vuln** (lines 421-423): `ErrorSt: begin fsm_err_o = 1'b1; end` — no register clearing
- **Twin**: `ErrorSt: begin fsm_err_o = 1'b1; key_state_en = 1'b1; data_state_en = 1'b1; digest_state_en = 1'b1; end` — asserts register enables with data='0
- **Oracle**: SEC_CM: SCRMBL.FSM.SPARSE annotation; terminal error state security convention requires clearing sensitive working registers to prevent data leakage. The FSM comment (line 420) states "Terminal error state" — no further operations should use retained state.

## Reproduction
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-040
bash build.sh
```

## Raw Output
```
ErrorSt register control signal check:
  vuln: key_state_en=0, data_state_en=0, digest_state_en=0 (NOT cleared)
  twin: key_state_en=1, data_state_en=1, digest_state_en=1 (cleared to 0)
vuln_deviation: YES  twin_secure: YES
CONFIRMED: otp_ctrl_scrmbl.sv ErrorSt doesn't clear sensitive internal state.
  vuln: ErrorSt sets only fsm_err_o=1; key_state_en=0, data_state_en=0,
        digest_state_en=0 -> key_state_q/data_state_q/digest_state_q retain
        pre-error values (sensitive key material survives).
  twin: ErrorSt also asserts key_state_en=1, data_state_en=1,
        digest_state_en=1 with data='0 -> registers cleared to 0.
  Oracle: SEC_CM: SCRMBL.FSM.SPARSE; terminal error state must clear
          sensitive working registers per security convention.
exit code: 1 (1 = finding confirmed)
```

## Twin Diff Summary
- File: otp_ctrl_scrmbl.sv, lines 421-423
- Vuln: `ErrorSt: begin fsm_err_o = 1'b1; end`
- Twin: `ErrorSt: begin fsm_err_o = 1'b1; key_state_en = 1'b1; data_state_en = 1'b1; digest_state_en = 1'b1; end`
- Oracle: SEC_CM: SCRMBL.FSM.SPARSE + terminal error state security convention
