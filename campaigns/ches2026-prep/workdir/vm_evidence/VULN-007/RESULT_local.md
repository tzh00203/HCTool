# RESULT: VULN-007

## Verdict
**[poc-success]** L2 data-flow evidence

## Finding
AES DIP_CLEAR mux branch uses `data_in` (previous plaintext) instead of `prd_clearing_data`
(pseudo-random data). When `KEY_IV_DATA_IN_CLEAR` is triggered, the `data_in_prev` register
is "cleared" to the previous plaintext value — the wipe is a no-op and plaintext residue
survives in the register.

## Twin Fix
File: `aes_core.sv:370`
```diff
- DIP_CLEAR:   data_in_prev_d = data_in;
+ DIP_CLEAR:   data_in_prev_d = prd_clearing_data;
```
Oracle: default branch of the same mux already uses `prd_clearing_data`; all other
SEC_WIPE muxes in aes_core (`key_init_mux` line 320, `iv_mux` line 348) use PRD for
their CLEAR cases.

## Reproduction
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-007
bash build.sh
```

## Raw Output
```
DIP_CLEAR selected: vuln_deviation=YES  twin_secure=YES
CONFIRMED: aes_core.sv:370 data_in_prev_mux DIP_CLEAR uses data_in
instead of prd_clearing_data. When KEY_IV_DATA_IN_CLEAR is triggered,
the previous plaintext (data_in) survives the "secure wipe" instead of
being overwritten by pseudo-random data. Twin fix: DIP_CLEAR -> prd_clearing_data
Oracle: default branch of same mux + all other SEC_WIPE muxes use PRD.
exit code: 1 (1 = finding confirmed)
```

## Evidence Summary
- **Fidelity**: L2 (combinational micro-tb, expression-level)
- **exit code**: 1 = finding confirmed
- **vuln_deviation**: YES (DIP_CLEAR returns `data_in` != `prd_clearing_data`)
- **twin_secure**: YES (DIP_CLEAR returns `prd_clearing_data`)
- **tb type**: tb_comb (no clock sequencing needed)

## Deliverables
| File | Path |
|---|---|
| testbench | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-007/tb_dip_clear.sv` |
| sim driver | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-007/sim_main.cpp` |
| build script | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-007/build.sh` |
| exploit | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-007/exploit.py` |
| result | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-007/RESULT.md` |
