# RESULT: VULN-028

## Verdict
**[poc-success]** L2 fidelity

## Finding
otp_ctrl.sv `fatal_prim_otp_alert` (from `otp_macro_i.fatal_alert`, line 768) is **not latched** into `fatal_macro_error_q`. The error latching logic (lines 413-438, `p_errors_alerts`) only ORs partition-level `part_error[k]==MacroError` into `fatal_macro_error_d`, never ORs `fatal_prim_otp_alert`. A transient pulse on `otp_macro_i.fatal_alert` does NOT set `fatal_macro_error_q`, so:
- No escalation: `lc_escalate_en` stays Off (escalation gated on `fatal_macro_error_q || fatal_check_error_q`, line 450-452)
- FSMs do not enter ErrorSt
- Alert may not persist (depends on alert sender timing)

Additionally, 3 SVA assertions are commented out (lines 1489-1499), and an "IMPORTANT TODO" at line 1485 acknowledges the gap: "Add checks that the incoming fatal conditions from prim_otp trigger alerts."

## Twin Repair
Add `fatal_prim_otp_alert` to `fatal_macro_error_d`:
```sv
// VULN (line 417):
fatal_macro_error_d = fatal_macro_error_q;  // then |= part_error[k]==MacroError

// TWIN:
fatal_macro_error_d = fatal_macro_error_q | fatal_prim_otp_alert;  // then |= part_error[k]==MacroError
```
Oracle: `AlertIsFatal[1]=1'b1` (line 591) confirms `fatal_prim_otp_alert` is a fatal alert that must be latched like all other fatal alerts. Lines 1485-1487 "IMPORTANT TODO" + commented-out SVA assertions (lines 1489-1499) confirm the design intent was to latch these.

## Reproduction
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-028
bash build.sh
# exit code 1 = finding confirmed
```

## Raw Output
```
fatal_prim_otp_alert=1, part_macro_errors=0, fatal_macro_error_q=0:
  vuln: fatal_macro_error_d=0 escalate=0  (skips latch: YES)
  twin: fatal_macro_error_d=1 escalate=1  (latches alert: YES)
CONFIRMED: otp_ctrl.sv fatal_prim_otp_alert not latched into
fatal_macro_error_q. fatal_macro_error_d (line 417) only ORs
part_error[k]==MacroError (lines 427-437), never ORs
fatal_prim_otp_alert (line 768). Pulse on otp_macro_i.fatal_alert
does NOT set fatal_macro_error_q -> no escalation -> FSMs do not
enter ErrorSt. 3 SVA assertions also commented out (lines 1489-1499).
Twin adds fatal_prim_otp_alert to fatal_macro_error_d per
IMPORTANT TODO at line 1485 and AlertIsFatal[1]=1 at line 591.
exit code: 1 (1 = finding confirmed)
```

## Fidelity
L2 (data-flow empirical): combinational micro-tb comparing the error-latch expression between vuln and twin. The vulnerability is a missing OR term in a combinational expression, which is fully captured at the expression level.
