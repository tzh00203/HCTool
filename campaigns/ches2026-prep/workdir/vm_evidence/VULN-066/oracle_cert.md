# Oracle Certification — VULN-066

Generated: 2026-10-09 18:58 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-CONFIRMED

## Twin Repair Diff

- Vuln: `assign gen_in = invalid_stage_sel ? {GenLfsrCopies{lfsr[31:0]}} : ...`
- Twin: `assign gen_in = invalid_stage_sel ? {GenLfsrCopies{perm_data(lfsr[31:0], RndCnstRandPerm)}} : ...`
- Oracle: ctrl_rand[1] = perm_data(lfsr[31:0], RndCnstRandPerm) at line 238

## Oracle References

- Oracle: ctrl_rand[1] and data_rand[1] both use perm_data (lines 238,241)
- Oracle: ctrl_rand[1] = perm_data(lfsr[31:0], RndCnstRandPerm) at line 238
- Oracle: keymgr_ops_e enum defines only 0-4 as valid operations

## Evidence Log (excerpt)

```
VERILATE FAILED
build_vm.sh: line 14: /data_hdd/tzh24/miniconda3/pkgs/verilator-5.052-py311pl5321h11e3653_0/bin/verilator: No such file or directory
```
