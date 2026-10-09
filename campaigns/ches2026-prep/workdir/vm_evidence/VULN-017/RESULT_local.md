# VULN-017: entropy_src_markov_ht fail_pulse hardcoded zero

## Verdict
**[poc-success]** — finding confirmed. L2 fidelity.

## Finding
entropy_src_markov_ht.sv:158-159 hardcodes `test_fail_hi_pulse_o = 1'b0` and
`test_fail_lo_pulse_o = 1'b0`. The Markov health test can never report a
threshold violation, even when the counter exceeds the threshold with active=1
and window_wrap_pulse=1. This completely disables the Markov health test's
alarm path.

## Twin Repair
Only lines 158-159 changed (per oracle: sibling module entropy_src_adaptp_ht.sv:128-129):
```sv
// VULN:
assign test_fail_hi_pulse_o = 1'b0;
assign test_fail_lo_pulse_o = 1'b0;

// TWIN (oracle: entropy_src_adaptp_ht.sv:128-129):
assign test_fail_hi_pulse_o = active_i && window_wrap_pulse_i && (test_cnt_hi_o > thresh_hi_i);
assign test_fail_lo_pulse_o = active_i && window_wrap_pulse_i && (test_cnt_lo_o < thresh_lo_i);
```

## Testbench
Type: tb_comb (combinational micro-tb, L2 data-flow evidence)
- Input constants: active=1, window_wrap_pulse=1, test_cnt_hi=100 > thresh_hi=50, test_cnt_lo=10 < thresh_lo=50
- vuln: fail_hi_pulse=0, fail_lo_pulse=0 (hardcoded zero — never fires)
- twin: fail_hi_pulse=1, fail_lo_pulse=1 (correctly fires on threshold violation)

## Reproduction
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-017
unset VERILATOR_ROOT
bash build_markov_ht_fail_pulse.sh
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
CONFIRMED: entropy_src_markov_ht test_fail_hi/lo_pulse_o hardcoded to 1'b0
  vuln: fail_hi_pulse=0, fail_lo_pulse=0 (hardcoded, never fires)
  twin: fail_hi_pulse=1 (active && window_wrap_pulse && cnt_hi>thresh_hi), per adaptp_ht oracle
exit code: 1 (1 = finding confirmed)
```

## Deliverables
- `tb_markov_ht_fail_pulse.sv` — combinational micro-tb (vuln vs twin expression comparison)
- `entropy_src_markov_ht_twin.sv` — repaired twin module
- `build_markov_ht_fail_pulse.sh` — Verilator build + run script
- `sim_main.cpp` — C++ simulation driver
- `exploit.py` — redbud-mode PoC entry
