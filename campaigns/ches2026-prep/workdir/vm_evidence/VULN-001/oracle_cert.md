# Oracle Certification — VULN-001

Generated: 2026-10-09 18:31 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: [poc-success]
Fidelity: L1
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle: The `(~dbg_csr | debug_mode_i)` term makes the signal always-1 for non-debug CSRs, conflating privilege and debug checks. Debug access is handled separately by `illegal_csr_dbg`. Fix removes this always-true term.
- Oracle: RISC-V Privileged Spec v1.12 §3.1.1 — "Any attempt to access a CSR from a less privileged mode raises an illegal-instruction exception." The `& ~priv` cancels the check; the fix uses OR semantics (any violation → illegal).
- SEC_CM bypass

## Evidence Log (excerpt)

```
cycles=17  test_done=1
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: ibex CSR privilege check completely bypassed
  vuln: illegal_csr_insn_o = csr_access & combined & ~priv_violation;
        priv_violation is always 1 for non-debug CSRs, so ~priv=0,
        making illegal_csr_insn_o=0 always -> U-mode can write any M-only CSR.
  twin: illegal_csr_insn_o = csr_access & (illegal_csr | priv_viol | dbg_viol | wr_viol);
        privilege_level_violation = (csr_addr[9:8] > priv_lvl_q);
        OR semantics: any violation -> illegal insn (RISC-V Priv Spec v1.12 s3.1.1).
```
