# RESULT: VULN-022

## Verdict
**[poc-success]** L1 fidelity

## Finding
ibex_cs_registers.sv:1270-1272 MSECCFG MML and MMWP next-state logic lacks
sticky-one semantics. The comment on line 1270 says "cannot be unset once set"
but the implementation is just passthrough:

```systemverilog
assign pmp_mseccfg_d.mml  = csr_wdata_int[CSR_MSECCFG_MML_BIT];
assign pmp_mseccfg_d.mmwp = csr_wdata_int[CSR_MSECCFG_MMWP_BIT];
```

Per the RISC-V Smepmp specification, MML and MMWP are sticky-one bits: once
set, software cannot clear them. The correct next-state logic should OR with
the current register value:

```systemverilog
assign pmp_mseccfg_d.mml  = pmp_mseccfg_q.mml  | csr_wdata_int[CSR_MSECCFG_MML_BIT];
assign pmp_mseccfg_d.mmwp = pmp_mseccfg_q.mmwp | csr_wdata_int[CSR_MSECCFG_MMWP_BIT];
```

Impact: SW can clear MML/MMWP after setting them, undermining the security
guarantees these bits provide (MML = Machine Memory Lockdown, MMWP = Machine
Memory Whitespace Permission). For example, firmware could set MML=1 to lock
down memory, then clear it to relax restrictions — defeating the sticky
guarantee.

## Reproduction
```bash
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-022/build_mseccfg_sticky.sh
```

## Raw Output
```
MSECCFG sticky-one test:
  test_confirmed: YES
CONFIRMED: ibex_cs_registers.sv:1270-1272 MSECCFG MML/MMWP lack sticky-one semantics.
  pmp_mseccfg_d.mml  = csr_wdata_int[CSR_MSECCFG_MML_BIT]  (passthrough)
  pmp_mseccfg_d.mmwp = csr_wdata_int[CSR_MSECCFG_MMWP_BIT] (passthrough)
  After set-then-clear: vuln reads 0 (SW can clear), twin reads 1 (sticky).
  Spec (RISC-V Smepmp): once MML/MMWP are set, they cannot be cleared.
exit code: 1 (1 = finding confirmed)
```

## Twin Repair Diff
Only change: in `ibex_cs_registers.sv` lines 1270-1272, replace passthrough
next-state with sticky-one (OR with current value):

```systemverilog
// Before (vuln):
assign pmp_mseccfg_d.mml  = csr_wdata_int[CSR_MSECCFG_MML_BIT];
assign pmp_mseccfg_d.mmwp = csr_wdata_int[CSR_MSECCFG_MMWP_BIT];

// After (twin):
assign pmp_mseccfg_d.mml  = pmp_mseccfg_q.mml  | csr_wdata_int[CSR_MSECCFG_MML_BIT];
assign pmp_mseccfg_d.mmwp = pmp_mseccfg_q.mmwp | csr_wdata_int[CSR_MSECCFG_MMWP_BIT];
```

Oracle: ibex_cs_registers.sv:1270 comment "cannot be unset once set" +
RISC-V Smepmp specification (MSECCFG.MML and MSECCFG.MMWP are sticky-one).

## Files
- tb: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-022/tb_mseccfg_sticky.sv`
- sim_main: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-022/sim_main.cpp`
- build: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-022/build_mseccfg_sticky.sh`
- exploit: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-022/exploit.py`
