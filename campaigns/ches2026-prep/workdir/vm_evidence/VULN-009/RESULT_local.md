# RESULT: VULN-009

## Verdict
**[poc-success]** L2 data-flow evidence

## Finding
HMAC `hmac_reg_top.sv:2128` — `wipe_secret_we` gate uses `reg_error` instead of
`!reg_error`, inverting the polarity. All other write-enables in the same file
(`intr_state_we`, `cfg_we`, `cmd_we`, `key_*_we`, `digest_*_we`, etc.) gate on
`!reg_error`. The consequence: on a valid SW write (reg_error=0), `wipe_secret_we=0`
so the wipe never fires — key/hash state survives the "secure wipe" operation.
On a bus error (reg_error=1), the wipe fires instead, which is the opposite of
the intended behavior.

## Twin Fix
File: `hmac_reg_top.sv:2128`
```diff
- assign wipe_secret_we      = (addr_hit[8]  && reg_we && reg_error);
+ assign wipe_secret_we      = (addr_hit[8]  && reg_we && !reg_error);
```
Oracle: every other write-enable in hmac_reg_top.sv uses `!reg_error`:
  - `intr_state_we` (L2073), `intr_enable_we` (L2078), `intr_test_we` (L2085),
  - `cfg_we` (L2096), `cmd_we` (L2119), `key_0_we` (L2131), `digest_0_we` (L2229), etc.

## Reproduction
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-009
bash build.sh
```

## Raw Output
```
Valid SW write (addr_hit8=1, reg_we=1, reg_error=0):
  vuln wipe_secret_we: deviates (expected 1 -> DEVIATION)
  twin wipe_secret_we: secure (expected 1 -> SECURE)
CONFIRMED: hmac_reg_top.sv:2128 wipe_secret_we gated on reg_error
(inverted polarity). Valid SW writes (reg_error=0) have
wipe_secret_we=0 -> wipe never fires on valid write -> key/hash
state survive "secure wipe". Twin uses !reg_error (same as all
other write-enables in the file: intr_state_we, cfg_we, key_*_we, etc.)
exit code: 1 (1 = finding confirmed)
```

## Evidence Summary
- **Fidelity**: L2 (combinational micro-tb, expression-level)
- **exit code**: 1 = finding confirmed
- **vuln_deviation**: YES (valid write: we=0, expected we=1)
- **twin_secure**: YES (valid write: we=1, matches expected)
- **tb type**: tb_comb (no clock sequencing needed)

## Deliverables
| File | Path |
|---|---|
| testbench | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-009/tb_hmac_wipe_gate.sv` |
| sim driver | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-009/sim_main.cpp` |
| build script | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-009/build.sh` |
| exploit | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-009/exploit.py` |
| result | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-009/RESULT.md` |
