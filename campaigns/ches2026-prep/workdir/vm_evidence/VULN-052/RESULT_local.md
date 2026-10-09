# RESULT: VULN-052

## Verdict
**[poc-success]** Finding confirmed. L2 fidelity.

## Vulnerability
`entropy_src_core.sv:2424`:
```systemverilog
assign rng_bit_sel = reg2hw.conf.rng_bit_sel.q & {1'b1, health_test_window[0]};
```
`health_test_window[0]` spuriously masks `rng_bit_sel[0]`. When the health test window is even (bit 0 = 0), SW's bit selection is silently overridden: `rng_bit_sel[0]` is forced to 0 regardless of SW config.

## Twin Fix
```systemverilog
assign rng_bit_sel = reg2hw.conf.rng_bit_sel.q;
```
Oracle: `health_test_window` is a window size parameter, semantically unrelated to bit selection. No in-tree comment, SVA, or spec justifies the mask. `rng_bit_sel` should be a direct passthrough from the SW configuration register.

## Evidence
```
cycles=1
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: rng_bit_sel masked by health_test_window[0]
  vuln: rng_bit_sel = sel_reg & {1'b1, hw[0]} → 2'b01 & {1,0} = 2'b00 (bit selection silently overridden)
  twin: rng_bit_sel = sel_reg → 2'b01 (SW config respected)
  oracle: health_test_window is window size, semantically unrelated to bit selection
exit code: 1 (1 = finding confirmed)
```

## Build Command
```bash
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-052/build_rng_bit_sel.sh
```

## Fidelity
L2 (combinational micro-tb, expression-level data flow evidence)
