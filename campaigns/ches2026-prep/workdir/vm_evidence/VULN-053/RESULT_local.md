# RESULT: VULN-053

## Verdict
**[poc-success]** — finding confirmed. L2 fidelity (combinational micro-tb).

## Vulnerability
entropy_src_core.sv:947-961: `sfifo_distr_err[2/1/0]` omitted from
`fifo_write_err_sum`, `fifo_read_err_sum`, `fifo_status_err_sum`.

All three per-type FIFO error category sums include `sfifo_esrng_err`,
`sfifo_observe_err`, and `sfifo_esfinal_err` bits but skip `sfifo_distr_err` bits.
When the distr FIFO signals a write/read/status error, the corresponding
ERR_CODE category fields (`fifo_write_err`, `fifo_read_err`, `fifo_state_err`)
remain 0 — SW cannot see the error via these category bits.

Note: `sfifo_distr_err` IS correctly included in `sfifo_distr_err_sum` (line 921)
and `fatal_loc_events` (line 911), so the error does trigger the fatal alert path.
The omission is specifically in the per-type breakdown fields of ERR_CODE.

## Twin Fix
Add `sfifo_distr_err[2]` to `fifo_write_err_sum`, `sfifo_distr_err[1]` to
`fifo_read_err_sum`, `sfifo_distr_err[0]` to `fifo_status_err_sum` — matching
the pattern used by esrng/observe/esfinal in the same expressions.

Oracle: sibling FIFO terms (esrng, observe, esfinal) all contribute [2] to write,
[1] to read, [0] to status. Distr must follow the same pattern (same prim_fifo
primitive).

## Evidence

### Reproduction Command
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-053
bash build_distr_err_sum.sh
```

### Raw Output
```
sfifo_distr_err=111, all other FIFO err=0:
  vuln deviates (sums all zero): YES
  twin secure  (sums all one):  YES
CONFIRMED: entropy_src_core.sv:947-961 sfifo_distr_err[2/1/0] omitted from
fifo_write_err_sum / fifo_read_err_sum / fifo_status_err_sum.
With distr FIFO errors active and all others zero:
  vuln: all three per-type sums = 0 (distr errors invisible in ERR_CODE categories)
  twin: all three per-type sums = 1 (distr errors correctly propagated, matching esrng/observe/esfinal pattern)
exit code: 1 (1 = finding confirmed)
```

### Twin Diff Summary
Three lines added (one per error-sum expression):
- `fifo_write_err_sum`: add `|| sfifo_distr_err[2]` (after esrng, before observe)
- `fifo_read_err_sum`: add `|| sfifo_distr_err[1]` (after esrng, before observe)
- `fifo_status_err_sum`: add `|| sfifo_distr_err[0]` (after esrng, before observe)

Oracle: sibling FIFO pattern (esrng/observe/esfinal all contribute [2]/[1]/[0] to write/read/status).
