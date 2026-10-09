# VULN-027 — Dynamic Verification Result

## Verdict: **[poc-success]** — L2 data-flow evidence

## Finding
otp_ctrl_scrmbl.sv:369 `default: ; // ignore` in the IdleSt `cmd_i` decode silently swallows 2 invalid command encodings (3'b110, 3'b111). The FSM stays in IdleSt with `fsm_err_o=0` instead of transitioning to ErrorSt and raising `fsm_err_o=1`.

## Twin Fix
- **Vuln**: `default: ; // ignore` (line 369)
- **Twin**: `default: begin state_d = ErrorSt; fsm_err_o = 1'b1; end`
- **Oracle**: The outer `state_q` case default (lines 427-430) already transitions to ErrorSt on invalid FSM state encoding; `SEC_CM: SCRMBL.FSM.SPARSE` annotation expects error detection for all invalid encodings.

## Reproduction
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-027
bash build.sh
```

## Raw Output
```
Invalid cmd 3'b110 in IdleSt:
  vuln: stays Idle (no error)
  twin: goes ErrorSt (fsm_err_o=1)
Invalid cmd 3'b111 in IdleSt:
  vuln: stays Idle (no error)
  twin: goes ErrorSt (fsm_err_o=1)
vuln_deviation: YES  twin_secure: YES
CONFIRMED: otp_ctrl_scrmbl.sv:369 default case in IdleSt cmd_i decode
silently ignores 2 invalid command encodings (3'b110, 3'b111).
Vuln: default: ; // ignore — FSM stays IdleSt, fsm_err_o=0.
Twin: default: begin state_d=ErrorSt; fsm_err_o=1'b1; end
Oracle: outer state_q default (lines 427-430) already transitions to
ErrorSt on invalid state; SEC_CM: SCRMBL.FSM.SPARSE expects error
detection for all invalid encodings.
exit code: 1 (1 = finding confirmed)
```

## Twin Diff Summary
- File: otp_ctrl_scrmbl.sv, line 369
- Vuln: `default: ; // ignore`
- Twin: `default: begin state_d = ErrorSt; fsm_err_o = 1'b1; end`
- Oracle: outer state_q default (lines 427-430) + SEC_CM: SCRMBL.FSM.SPARSE
