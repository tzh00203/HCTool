# VULN-024: lc_ctrl_fsm IdleSt allows clock bypass in PROD/DEV states

## Verdict
**[poc-success]** — finding confirmed. L2 fidelity.

## Finding
lc_ctrl_fsm.sv IdleSt (lines 335-357) includes `LcStDev` and `LcStProd` in the
`inside` set for `lc_clk_byp_req`, allowing clock bypass to be requested (On) in
PROD and DEV life cycle states when `use_ext_clock_i=1`. This directly contradicts
SVA assertion `NoClkBypInProdStates_A` (lines 860-863) which states that
`lc_clk_byp_req_o` must be `Off` in PROD/PROD_END/DEV states.

Notably, `ClkMuxSt` (lines 369-385) already correctly excludes DEV and PROD from
its clock bypass set, confirming the SVA is the intended behavior and IdleSt is
the bug.

## Twin Repair
Only IdleSt inside-set changed (lines 335-357). Removed `LcStDev` and `LcStProd`.
Oracle: SVA `NoClkBypInProdStates_A` (line 860-863):
```sv
// VULN (lines 335-357):
        if (lc_state_q inside {LcStRaw, ...,
                               LcStDev,    // <-- VULN: allows bypass
                               LcStProd,   // <-- VULN: allows bypass
                               LcStRma}) begin

// TWIN (per SVA NoClkBypInProdStates_A):
        if (lc_state_q inside {LcStRaw, ...,
                               // LcStDev  removed
                               // LcStProd removed
                               LcStRma}) begin
```

## Testbench
Type: tb_comb (combinational micro-tb, L2 data-flow evidence)
- Uses actual `lc_state_e` enum values from `lc_ctrl_state_pkg.sv`
- Stimulus: `use_ext_clock_i=1`, test states LcStProd, LcStDev, LcStRma
- vuln: `lc_clk_byp_req=On` for PROD and DEV (states in inside set)
- twin: `lc_clk_byp_req=Off` for PROD and DEV (states removed per SVA oracle)
- Sanity: RMA still allows bypass in both vuln and twin

## Reproduction
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-024
unset VERILATOR_ROOT
bash build_clkbyp.sh
# Expected: exit code 1 = finding confirmed
```

## Raw Output
```
Using verilator: /data_hdd/tzh24/miniconda3/pkgs/verilator-5.052-py311pl5321h11e3653_0/bin/verilator
Verilator 5.052 2026-09-05 rev conda-forge build
vuln_deviation: YES
twin_secure:    YES
test_confirmed: YES
test_done:      YES
CONFIRMED: lc_ctrl_fsm IdleSt allows clock bypass in PROD/DEV states
  vuln: lc_clk_byp_req=On in PROD/DEV (LcStDev/LcStProd in inside set)
  twin: lc_clk_byp_req=Off in PROD/DEV (per SVA NoClkBypInProdStates_A oracle)
exit code: 1 (1 = finding confirmed)
```

## Deliverables
- `tb_lc_ctrl_clkbyp.sv` — combinational micro-tb (vuln vs twin inside-set comparison)
- `lc_ctrl_fsm_twin.sv` — documentation twin showing the exact fix
- `build_clkbyp.sh` — Verilator build + run script
- `sim_main.cpp` — C++ simulation driver
- `exploit.py` — redbud-mode PoC entry
