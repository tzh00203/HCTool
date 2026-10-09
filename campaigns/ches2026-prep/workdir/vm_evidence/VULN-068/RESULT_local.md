# RESULT: VULN-068

## Verdict: [poc-success]

KMAC `en_unsupported_modestrength` bypasses mode+strength check — SW-writable CSR bit completely disables security validation of mode+strength combinations.

## Fidelity: L2 (data-flow evidence, expression-level comparison)

## Vulnerability

In `kmac_errchk.sv:236-239`, the `block_swcmd` expression:
```systemverilog
assign block_swcmd =  (err_swsequence)
                   || (err_modestrength
                       && !cfg_en_unsupported_modestrength_i)
                   || err_entropy_ready;
```

When `cfg_en_unsupported_modestrength_i=1` (SW enables bypass), `err_modestrength` is excluded from `block_swcmd`, so unsupported mode+strength combinations proceed without blocking.

## Twin Repair

Twin removes the bypass condition, making `err_modestrength` always block:
```systemverilog
assign block_swcmd =  (err_swsequence)
                   || err_modestrength
                   || err_entropy_ready;
```

Oracle: mode+strength check is a security invariant (SEC_CM). The `cfg_en_unsupported_modestrength_i` input (line 65 comment: "errchk propagates the command...even with err_modestrength") documents intent to bypass, but this contradicts the security purpose of the check.

## Stimulus

- `err_modestrength = 1` (unsupported mode+strength combination)
- `cfg_en_unsupported_modestrength_i = 1` (SW enables bypass)
- `err_swsequence = 0`, `err_entropy_ready = 0`

## Observed Output

```
err_modestrength=1, cfg_en_unsupported_modestrength=1:
  vuln block_swcmd: 0 (0=bypassed)  twin block_swcmd: 1 (1=enforced)
vuln_deviation: YES  twin_secure: YES
CONFIRMED: kmac_errchk.sv:236-239 en_unsupported_modestrength bypasses mode+strength check
```

## Reproduce

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-068
bash build_kmac_errchk_modestrength.sh
# exit code 1 = finding confirmed
```

## Twin Diff Summary

- File: `kmac_errchk.sv` line 236-239
- Change: `(err_modestrength && !cfg_en_unsupported_modestrength_i)` → `err_modestrength`
- Oracle: SEC_CM security invariant; SW-writable bit should not bypass mode+strength check
