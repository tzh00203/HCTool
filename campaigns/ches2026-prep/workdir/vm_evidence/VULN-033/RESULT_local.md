# RESULT: VULN-033

## Verdict
**[poc-success]** — finding confirmed

## Fidelity Level
L1 (执行级实证: negedge-FSM 时序仿真, vuln-vs-twin 差分)

## Finding
kmac_core.sv:227-236 `StTerminalError` state delays `sparse_fsm_error_o` by 100 cycles.
When the sparse FSM enters `StTerminalError`, instead of immediately asserting
`sparse_fsm_error_o = 1`, it counts `st_err_ct` from 0 to 100 before asserting.
This means the FSM error alert is suppressed for 100 cycles after a fatal FSM
error is detected — the error signal stays 0 when it should be 1.

## Twin Fix
In `StTerminalError`, immediately assert `sparse_fsm_error_o = 1` instead of
the 100-cycle count-up delay. Oracle: the `default` case (line 241) already
sets `sparse_fsm_error_o = 1'b1` immediately upon hitting an invalid FSM
encoding — `StTerminalError` should behave the same per SEC_CM: FSM.SPARSE.

Twin diff (conceptual — embedded in tb):
```
- StTerminalError: begin
-   if (st_err_ct < 8'd100) begin
-     st_err_ct_d = st_err_ct + 1'b1;
-     sparse_fsm_error_o = 1'b0;
-   end else begin
-     sparse_fsm_error_o = 1'b1;
-   end
- end
+ StTerminalError: begin
+   sparse_fsm_error_o = 1'b1;
+ end
```

## Reproduction Command
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-033
bash build.sh
# exit code 1 = finding confirmed
```

## Raw Output
```
cycles=115
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: kmac_core.sv:227-236 StTerminalError delays sparse_fsm_error_o by 100 cycles.
  vuln: sparse_fsm_error_o stays 0 for 100 cycles (st_err_ct counts 0..99), then 1.
  twin: sparse_fsm_error_o = 1 immediately upon entering StTerminalError.
  Oracle: default case (line 241) already asserts sparse_fsm_error_o = 1 immediately.
  SEC_CM: FSM.SPARSE expects error signaled upon terminal error entry.
exit code: 1 (1 = finding confirmed)
```

## Observations
- At early checkpoint (5 cycles after entering StTerminalError):
  - vuln: sparse_fsm_error_o = 0 (still counting, delayed)
  - twin: sparse_fsm_error_o = 1 (immediately asserted)
- The 100-cycle delay means alert/escalation logic downstream sees no error
  for 100 cycles after a fatal FSM fault — a window where the system operates
  with a known FSM error but no alert propagation.
