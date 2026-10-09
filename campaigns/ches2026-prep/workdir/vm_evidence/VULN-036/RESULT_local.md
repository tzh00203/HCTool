# RESULT: VULN-036

## Verdict

**[poc-success]** L2 fidelity

## Finding

AES `data_out_reg` (aes_core.sv:873) async reset is gated by `data_out_we`:
```systemverilog
if (!rst_ni && data_out_we != SP2V_HIGH) data_out_q <= '0;
else if (data_out_we == SP2V_HIGH)       data_out_q <= data_out_d;
```
When `rst_ni=0` AND `data_out_we==SP2V_HIGH`, the first branch is false and the second is true,
so `data_out_q` loads `data_out_d` instead of clearing. The reset is blocked by the write-enable gate.

## Twin Repair

Twin changes the condition to unconditional async reset:
```systemverilog
if (!rst_ni)                     data_out_q <= '0;
else if (data_out_we == SP2V_HIGH) data_out_q <= data_out_d;
```
Oracle: standard FF async reset pattern used by every other register in aes_core (key_init_reg,
iv_reg, data_in_prev_reg all use `if (!rst_ni) ... <= '0`); SEC_CM: DATA_REG.SEC_WIPE requires
that reset clears sensitive data.

## Build & Run

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-036
bash build.sh
```

## Raw Output

```
VULN-036 data_out reset with we=HIGH: vuln retained nonzero: YES  twin cleared: YES
CONFIRMED: aes_core.sv:873 data_out_reg async reset gated by data_out_we.
When reset is asserted while we==SP2V_HIGH, the vuln retains the previous
value (gate blocks clearing) while the twin (unconditional reset) clears.
Oracle: standard FF async reset pattern used by all other regs in aes_core;
SEC_CM: DATA_REG.SEC_WIPE requires reset clears sensitive data.
exit code: 1 (1 = finding confirmed)
```

## Twin Diff Summary

- File: aes_core.sv line 873
- Vuln: `if (!rst_ni && data_out_we != SP2V_HIGH)` — reset conditional on we
- Twin: `if (!rst_ni)` — unconditional async reset
- Oracle: standard FF async reset pattern (all other regs in same file) + SEC_CM: DATA_REG.SEC_WIPE

## Fidelity

L2 (data-flow evidence at expression level — micro-tb isolates the always_ff pattern)

## In-System Impact

Requires FI to force `data_out_we==SP2V_HIGH` during async reset assertion. Under normal
operation, the control FSM de-asserts data_out_we before reset. Severity: Medium (config
hardening, not directly exploitable without FI).
