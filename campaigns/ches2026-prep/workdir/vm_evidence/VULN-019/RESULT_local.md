# RESULT: VULN-019

## Verdict
**[poc-success]** Finding confirmed. L2 fidelity.

## Vulnerability
entropy_src_core.sv:813-814 `es_rng_src_valid` is gated by `entropy_data_reg_enable`:

```systemverilog
assign es_rng_src_valid = entropy_src_rng_i.rng_valid &
                         (reg2hw.conf.entropy_data_reg_enable.q != '0);
```

When `entropy_data_reg_enable=0` and `rng_valid=1`, `es_rng_src_valid=0`, which blocks `sfifo_esrng_push` (line 1079), completely stopping RNG entropy flow into the pipeline.

## Twin Fix
Remove the spurious `entropy_data_reg_enable` gate:
```systemverilog
assign es_rng_src_valid = entropy_src_rng_i.rng_valid;
```
Oracle: upstream OpenTitan code has only `es_rng_src_valid = rng_valid`. The `entropy_data_reg_enable` bit controls the ENTROPY_DATA register read path (line 3045: `es_data_reg_rd_en = es_enable_fo[17] && efuse_es_sw_reg_en && entropy_data_reg_en_pfe`), NOT the RNG source validity. Gate is misapplied.

## Twin Diff Summary
- Line 813-814: Remove `(reg2hw.conf.entropy_data_reg_enable.q != '0)` gate from `es_rng_src_valid` assign
- Oracle: upstream OpenTitan code (es_rng_src_valid = rng_valid only)

## Reproduction Command
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-019
bash build.sh
# exit code 1 = finding confirmed
```

## Raw Output
```
rng_valid=1, entropy_data_reg_enable=0:
  vuln blocks RNG: YES  twin accepts RNG: YES
CONFIRMED: entropy_src_core.sv:813-814 es_rng_src_valid gated by
entropy_data_reg_enable (spurious gate). When entropy_data_reg_enable=0
and rng_valid=1, es_rng_src_valid=0 -> sfifo_esrng_push=0.
RNG entropy flow is completely blocked even though the RNG is active.
Twin removes the gate: es_rng_src_valid = rng_valid (upstream oracle).
entropy_data_reg_enable controls ENTROPY_DATA register read path only,
not the RNG source validity.
exit code: 1 (1 = finding confirmed)
```

## Fidelity Level
L2 (data-flow evidence: combinational micro-tb, expression-level differential)

## Files
- `tb_es_rng_valid.sv` — micro-tb (vuln + twin dual instantiation)
- `sim_main.cpp` — C++ simulation driver
- `build.sh` — Verilator build script
- `exploit.py` — PoC entry (redbud mode)
