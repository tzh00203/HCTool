# VULN-002 Dynamic Verification Result

## Verdict: [poc-success] L2

**Finding confirmed.** pmp_req_err_o is always zero in the vulnerable ibex_pmp module; the twin correctly denies access.

## Vulnerability

In `ibex_pmp.sv` line 285:
```sv
assign pmp_req_err_o[c] = access_violation_detected & ~fault_analysis_result;
```

Since `access_violation_detected = ~debug_bypass_active & fault_analysis_result`, the expression self-cancels:
```
pmp_req_err_o = (~debug_bypass_active & fault_analysis_result) & ~fault_analysis_result = 0
```

Result: PMP never rejects any memory access regardless of configuration.

## Twin Fix

Only line 285 changed (per workorder):
```sv
assign pmp_req_err_o[c] = access_violation_detected;
```

Repair basis: in-tree comment at lines 50-57 shows the intended dataflow:
`access_violation_detected -> pmp_req_err_o` with no additional masking.
The `& ~fault_analysis_result` term is the injected vulnerability that nullifies enforcement.

## Stimulus

- Region 0: NA4 mode, addr=0x20000000, L=1, X=0, R=0, W=0
- Request: U-mode READ to 0x20000000
- debug_mode=0, mseccfg={rlb=0, mmwp=0, mml=0}

## Results

| Instance | pmp_req_err_o | Expected |
|----------|---------------|----------|
| vuln     | 0             | 1 (deny) |
| twin     | 1             | 1 (deny) |

## Reproduction

```bash
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-002/build.sh
```

## Raw Output

```
vuln pmp_req_err_o: 0
twin pmp_req_err_o: 1
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: pmp_req_err_o is always zero in vuln (enforcement dead)
  vuln: pmp_req_err_o=0 even when PMP region denies access
  twin: pmp_req_err_o=1 correctly denies (fix: remove & ~fault_analysis_result)
  Repair basis: in-tree comment lines 50-57 show intended dataflow
  access_violation_detected -> pmp_req_err_o with no additional masking
exit code: 1 (1 = finding confirmed)
```

## Deliverables

| File | Description |
|------|-------------|
| `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-002/tb_pmp_err.sv` | Combinational micro-tb (vuln+twin dual instantiation) |
| `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-002/ibex_pmp_twin.sv` | Twin module (only line 285 fixed) |
| `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-002/sim_main.cpp` | C++ simulation driver |
| `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-002/build.sh` | Verilator build script |
| `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-002/exploit.py` | PoC entry (redbud mode) |
| `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-002/dv_fcov_macros.svh` | Coverage macro stub |
