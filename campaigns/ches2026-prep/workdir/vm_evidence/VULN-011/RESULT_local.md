# RESULT: VULN-011

## Verdict: [poc-success] L2 fidelity

## Finding
HMAC WIPE_SECRET read leaks key[0]. In `hmac_reg_top.sv:2419`, the rdata mux at
`addr_hit[8]` returns `reg2hw.key[0].q` — the first key word — when the
WIPE_SECRET CSR is read. Since WIPE_SECRET is a write-only register
(`u_wipe_secret` declared with `.re(1'b0)` and `.qs()`), reads must return 0.
The vuln leaks key material.

## Twin Fix
Change line 2419 from:
```systemverilog
reg_rdata_next[31:0] = reg2hw.key[0].q;
```
to:
```systemverilog
reg_rdata_next[31:0] = '0;
```
Oracle: `u_wipe_secret` is SwAccessWO (`.re(1'b0)`, `.qs()`); all other WO
registers in the same file (`intr_test` addr_hit[2], `cmd` addr_hit[5]) return
`'0` on read in their rdata mux branches.

## Reproduction
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-011
bash build.sh
```

## Raw Output
```
WIPE_SECRET read: vuln_deviation=YES  twin_secure=YES
CONFIRMED: hmac_reg_top.sv:2419 addr_hit[8] rdata mux returns reg2hw.key[0].q instead of '0. Reading WIPE_SECRET (a write-only register) leaks key[0]. Twin fix: rdata = '0. Oracle: u_wipe_secret declared .re(1'b0) .qs() (SwAccessWO); intr_test and cmd WO regs both return '0 on read.
exit code: 1 (1 = finding confirmed)
```

## Twin Diff Summary
- File: `hmac_reg_top.sv` line 2419
- Change: `reg2hw.key[0].q` → `'0`
- Oracle: SwAccessWO register convention (intr_test, cmd return '0 on read)
