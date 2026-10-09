# RESULT: VULN-035

## Verdict

**[poc-success]** L2 fidelity (data-flow evidence, combinational micro-tb)

## Finding

aes_core.sv:686-689 `data_in_reg_clear` block drives `hw2reg.data_in[i].de = data_in_we`
but **never assigns `hw2reg.data_in[i].d`**. When SEC_WIPE triggers (`data_in_we=1`),
the `.d` input is undefined (synthesis tie-off to 0 or retains old value) instead of
`prd_clearing_data[i]`. The secure wipe of the input data register is a no-op:
data_in is zeroed or retains its value rather than being overwritten with pseudo-random data.

## Twin Fix

Add `hw2reg.data_in[i].d = prd_clearing_data[i];` inside the `data_in_reg_clear` loop,
so that when `data_in_we=1`, the register updates to PRD clearing data (matching all
sibling SEC_WIPE registers in aes_core).

**Oracle**: SEC_CM: DATA_REG.SEC_WIPE comment immediately above the vuln code; all
sibling registers (key_init at line 316-323, iv at line 341-351, data_out at line 872-878)
assign both `.de` and `.d` with PRD clearing data.

## Execution

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-035
bash build.sh
```

## Raw Output

```
data_in .de/.d check: vuln_deviation=YES  twin_secure=YES
CONFIRMED: aes_core.sv:686-689 data_in_reg_clear drives .de (data_in_we)
but never assigns .d. When SEC_WIPE triggers (data_in_we=1), .d is undefined
(synthesis tie-off to 0 or old value) instead of prd_clearing_data.
Secure wipe is a no-op: data_in register retains or zeros instead of PRD.
Twin fix: add hw2reg.data_in[i].d = prd_clearing_data[i] in the loop.
Oracle: SEC_CM: DATA_REG.SEC_WIPE comment + all sibling SEC_WIPE registers
(key_init, iv, data_out) assign both .de and .d with PRD.
exit code: 1 (1 = finding confirmed)
```

## Exit Code

1 (= finding confirmed per harness convention)

## Twin Diff Summary

- File: `aes_core.sv`, lines 686-689
- Change: In `data_in_reg_clear` always_comb block, add `hw2reg.data_in[i].d = prd_clearing_data[i];`
  inside the for loop, after the existing `hw2reg.data_in[i].de = data_in_we;` line.
- Oracle: SEC_CM: DATA_REG.SEC_WIPE + sibling register patterns (key_init, iv, data_out)
