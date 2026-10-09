# RESULT.md — VULN-066

## Verdict
**[poc-success]** — finding confirmed. Exit code 1.

## Fidelity
**L2** — data flow evidence (combinational micro-tb, expression-level)

## Finding
Two issues in keymgr confirmed:

1. **gen_in decoy not permuted (SCA weakening)**: keymgr.sv:490-493 — when `invalid_stage_sel=1`, the decoy path uses `{GenLfsrCopies{lfsr[31:0]}}` (raw LFSR, no permutation). Twin applies `perm_data(lfsr[31:0], RndCnstRandPerm)` matching the pattern of `ctrl_rand[1]` (line 238) and `data_rand[1]` (line 241). Without permutation, the decoy value has higher SCA correlation with the raw LFSR state, weakening side-channel protection when the keymgr enters an invalid stage.

2. **dis_op catches invalid opcodes (5,6,7)**: keymgr_ctrl.sv:154 — `dis_op = ~(op_i inside {OpAdvance, OpGenId, OpGenSwOut, OpGenHwOut})` is true for OpDisable (value 4) AND invalid encodings (5,6,7). Twin: `dis_op = (op_i == OpDisable)` — only true for the actual OpDisable operation. Invalid opcodes should not be silently treated as disable; they may indicate a fault injection or encoding error.

## Reproduction Command
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-066
bash build_keymgr_genin_decoy.sh
# Expected: exit code 1 (finding confirmed)
```

## Raw Output
```
VULN-066: keymgr gen_in decoy + dis_op semantics
  vuln_deviation: YES
  twin_secure:    YES
  test_confirmed: YES
CONFIRMED: keymgr gen_in decoy uses raw LFSR without permutation (SCA weakening)
  + dis_op catches invalid opcodes (5,6,7) as well as OpDisable
  vuln (keymgr.sv:490): gen_in decoy = {GenLfsrCopies{lfsr[31:0]}} (raw, no perm)
  twin: gen_in decoy = {GenLfsrCopies{perm_data(lfsr[31:0], RndCnstRandPerm)}}
  Oracle: ctrl_rand[1] and data_rand[1] both use perm_data (lines 238,241)
  vuln (keymgr_ctrl.sv:154): dis_op = ~(op_i inside {OpAdvance..OpGenHwOut})
  twin: dis_op = (op_i == OpDisable) — invalid encodings not treated as disable
exit code: 1 (1 = finding confirmed)
```

## Twin Repair Diff
1. **keymgr.sv:490** (gen_in decoy):
   - Vuln: `assign gen_in = invalid_stage_sel ? {GenLfsrCopies{lfsr[31:0]}} : ...`
   - Twin: `assign gen_in = invalid_stage_sel ? {GenLfsrCopies{perm_data(lfsr[31:0], RndCnstRandPerm)}} : ...`
   - Oracle: ctrl_rand[1] = perm_data(lfsr[31:0], RndCnstRandPerm) at line 238

2. **keymgr_ctrl.sv:154** (dis_op):
   - Vuln: `assign dis_op = ~(op_i inside {OpAdvance, OpGenId, OpGenSwOut, OpGenHwOut})`
   - Twin: `assign dis_op = (op_i == OpDisable)`
   - Oracle: keymgr_ops_e enum defines only 0-4 as valid operations

## Deliverables
| File | Absolute Path |
|------|---------------|
| tb | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-066/tb_keymgr_genin_decoy.sv |
| sim_main.cpp | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-066/sim_main.cpp |
| build.sh | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-066/build_keymgr_genin_decoy.sh |
| exploit.py | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-066/exploit.py |
