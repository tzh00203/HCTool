# RESULT: VULN-020

## Verdict
**[poc-success]** L2 fidelity

## Finding
ibex_pmp.sv:128-151 `access_fault_check` function takes `csr_pmp_mseccfg_mmwp`,
`csr_pmp_mseccfg_mml`, `pmp_req_type`, and `priv_mode` as parameters but **never
uses them** to determine default behavior when no PMP region matches. The function
initializes `access_fail = 1'b0` and only changes it when a region matches, so
unmatched M-mode access always returns allow (0), violating the RISC-V Smepmp spec:

- **MMWP=1** should cause default deny for all unmatched access
- **MML=1 + EXEC + M-mode** should cause default deny for unmatched EXEC
- Normal PMP: M-mode default allow, S/U default deny — vuln always returns allow

## Reproduction
```bash
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-020/build_pmp_mmwp.sh
```

## Raw Output
```
MMWP=1, no region match, M-mode READ:
  vuln_deviation: YES
  twin_secure:    YES
CONFIRMED: ibex_pmp.sv:128-151 access_fault_check ignores MMWP/MML/priv_mode
  for default behavior. When no PMP region matches and MMWP=1,
  RISC-V Smepmp spec requires default deny, but vuln returns allow (0).
  Twin adds: if !matched && mmwp -> access_fail=1 per spec.
exit code: 1 (1 = finding confirmed)
```

## Twin Repair Diff
Only change: in `access_fault_check`, after the region-matching loop, add
unmatched-case handling:

```systemverilog
// Added after the for-loop (vuln has none of this):
if (!matched) begin
  if (csr_pmp_mseccfg_mmwp) begin
    access_fail = 1'b1;  // MMWP: default deny
  end else if (csr_pmp_mseccfg_mml && pmp_req_type == PMP_ACC_EXEC && priv_mode == PRIV_LVL_M) begin
    access_fail = 1'b1;  // MML + EXEC in M-mode: deny
  end else begin
    access_fail = (priv_mode != PRIV_LVL_M);  // Normal: M allow, S/U deny
  end
end
```

Oracle: ibex_pmp.sv line 137-138 comment ("When MSECCFG.MMWP is set default deny
always, otherwise allow for M-mode, deny for other modes") + RISC-V Smepmp specification.

## Files
- tb: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-020/tb_pmp_mmwp.sv`
- sim_main: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-020/sim_main.cpp`
- build: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-020/build_pmp_mmwp.sh`
- exploit: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-020/exploit.py`
