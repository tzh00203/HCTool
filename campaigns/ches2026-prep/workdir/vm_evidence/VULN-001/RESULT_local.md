# RESULT: VULN-001 — ibex CSR privilege check completely bypassed

## Verdict: **[poc-success]** — L1 执行级实证

## Finding Summary

U-mode can read/write ALL M-only CSRs because the privilege check in
`ibex_cs_registers.sv` is completely dead:

- **Bug 1** (line 331): `privilege_level_violation = (csr_addr[9:8] > {priv_lvl_q}) | (~dbg_csr | debug_mode_i)`
  - For non-debug CSRs: `(~dbg_csr | debug_mode_i) = 1`, making `privilege_level_violation` **always 1**
- **Bug 2** (line 340): `illegal_csr_insn_o = csr_access_i & combined_access_check & ~privilege_level_violation`
  - `& ~privilege_level_violation` **cancels** the check instead of enforcing it
- **Combined**: `priv_violation=1 → ~priv=0 → illegal_csr_insn_o=0` for ALL non-debug CSR accesses
  → U-mode can write `mstatus`, `CPUCTRLSTS` (SEC_CM bypass), `DCSR` (debug priv escalation), etc.

## Fidelity Level

L1 执行级实证 — Verilator 仿真, vuln-vs-twin 差分比对, 8 项 directed tests

## Reproduction Command

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-001
bash build.sh
# exit code 1 = finding confirmed
```

## Raw Output

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
exit code: 1 (1 = finding confirmed)
```

## Twin Repair Diff

Only 2 lines changed in the privilege check logic (lines 331, 340 of ibex_cs_registers.sv):

**Line 331** — privilege_level_violation:
- Vuln: `privilege_level_violation = (csr_addr[9:8] > {priv_lvl_q}) | (~dbg_csr | debug_mode_i);`
- Twin: `privilege_level_violation = (csr_addr[9:8] > {priv_lvl_q});`
- Oracle: The `(~dbg_csr | debug_mode_i)` term makes the signal always-1 for non-debug CSRs, conflating privilege and debug checks. Debug access is handled separately by `illegal_csr_dbg`. Fix removes this always-true term.

**Line 340** — illegal_csr_insn_o:
- Vuln: `illegal_csr_insn_o = csr_access_i & combined_access_check & ~privilege_level_violation;`
- Twin: `illegal_csr_insn_o = csr_access_i & (illegal_csr | privilege_level_violation | illegal_csr_dbg | illegal_csr_write);`
- Oracle: RISC-V Privileged Spec v1.12 §3.1.1 — "Any attempt to access a CSR from a less privileged mode raises an illegal-instruction exception." The `& ~priv` cancels the check; the fix uses OR semantics (any violation → illegal).

## Directed Test Matrix

| Test | Scenario | Golden | Vuln | Twin | Diff? |
|------|----------|--------|------|------|-------|
| t0 | U-mode write MSTATUS | illegal | allow | block | YES |
| t1 | U-mode write CPUCTRLSTS | illegal | allow | block | YES |
| t2 | U-mode write DCSR (no dbg) | illegal | allow | block | YES |
| t3 | M-mode write MSTATUS | allow | allow | allow | no |
| t4 | U-mode read MSTATUS | illegal | allow | block | YES |
| t5 | U-mode write MIE | illegal | allow | block | YES |
| t6 | M-mode access debug CSR (no dbg_mode) | illegal | block | block | no |
| t7 | U-mode access non-existent CSR | illegal | allow | block | YES |

6/8 tests show vuln-vs-twin behavioral difference. Vuln wrongly allows 6 access violations.
