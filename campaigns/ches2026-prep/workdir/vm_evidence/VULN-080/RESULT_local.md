# RESULT: VULN-080

## Verdict: [poc-success]

## Finding

UART `uart_core.sv` has 3 SEC_CM gaps (all `sec-cm-mismatch`):

1. **Break FSM no FSM.LOCAL_ESC** (lines 135-137): The `break_st_q` FSM `default` case
   silently recovers to `BRK_CHK` without asserting any error signal (`fsm_err_o`).
   OpenTitan SEC_CM convention requires `FSM.LOCAL_ESC` — illegal FSM state must
   produce a local escalation alert. Sibling IPs (AES cipher_core, KMAC core,
   OTP ctrl_scrmbl) all assert `fsm_err_o` in their `default` cases.

2. **TX override no security gating** (lines 219-220): When `ovrd_tx_en=1`,
   `tx_out_q` unconditionally takes `ovrd_tx_val`. There is no gate on
   fault/error conditions. SW can override TX output even during security fault
   states. Sibling IPs gate override-like signals on error/fault indicators.

3. **NCO=0 silent stop, no error indication** (lines 167-173): The NCO baud rate
   generator accumulates `reg2hw.ctrl.nco.q` into `nco_sum_q`. When NCO=0,
   `nco_sum_q` stays 0, `tick_baud_x16` is permanently 0, and the UART silently
   stops all TX/RX operations. There is no error signal, no interrupt, and no
   SW-visible indication that the baud clock has stalled.

## Twin Repair

1. **Break FSM** (lines 135-137): In `default` case, add `break_fsm_err_o = 1'b1`.
   Oracle: sibling IP SEC_CM pattern — AES/KMAC/OTP all assert `fsm_err_o` in
   `default` case per `FSM.LOCAL_ESC` countermeasure.

2. **TX override** (lines 219-220): Gate override with `~security_fault`:
   `else if (ovrd_tx_en & ~security_fault)`. Oracle: SEC_CM convention —
   override-like signals gated on error/fault in sibling IPs.

3. **NCO=0** (lines 167-173): Add `nco_zero_err_o = (reg2hw.ctrl.nco.q == '0) & (tx_enable | rx_enable)`.
   Oracle: parameter-zero error detection pattern in sibling IPs.

## Evidence

- **TB type**: combinational micro-tb (tb_comb)
- **Fidelity**: L2 (data-flow evidence)
- **Stimulus**:
  - Issue 1: FSM in illegal state (fault injection)
  - Issue 2: ovrd_tx_en=1 with security_fault=1
  - Issue 3: NCO=0 with tx_enable|rx_enable=1
- **Vuln behavior**: no error on illegal FSM state; TX override active during fault; no error for NCO=0
- **Twin behavior**: fsm_err=1 on illegal state; TX override blocked during fault; nco_zero_err=1 for NCO=0
- **Differential**: all three — vuln produces no security alerts, twin produces appropriate alerts

## Execution

```
$ bash build.sh
VULN-080: UART SEC_CM gaps (3 sub-issues)

Issue 1 — Break FSM no FSM.LOCAL_ESC:
  vuln: fsm_err=0 (no alert on illegal state): YES
  twin: fsm_err=1 (alerts on illegal state):  YES
Issue 2 — TX override no security gating:
  vuln: override active despite fault: YES
  twin: override blocked during fault:  YES
Issue 3 — NCO=0 silent stop, no error:
  vuln: no error indication for NCO=0: YES
  twin: asserts nco_zero_err for NCO=0: YES

CONFIRMED: uart_core.sv 3 SEC_CM gaps:
  1. Break FSM default case (lines 135-137): no fsm_err_o — FSM.LOCAL_ESC missing
  2. TX override (lines 219-220): ovrd_tx_en unconditional, no security gating
  3. NCO baud generator (lines 167-173): NCO=0 causes tick_baud_x16=0 forever, no error
  Oracle: sibling IP SEC_CM patterns (AES/KMAC/OTP all assert fsm_err in default,
  gate overrides on fault, flag parameter-zero errors)
exit code: 1 (1 = finding confirmed)
```

## Deliverables

| File | Path |
|------|------|
| tb | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-080/tb_uart_sec_cm.sv` |
| sim_main | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-080/sim_main.cpp` |
| build | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-080/build.sh` |
| exploit | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-080/exploit.py` |
| RESULT | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-080/RESULT.md` |
