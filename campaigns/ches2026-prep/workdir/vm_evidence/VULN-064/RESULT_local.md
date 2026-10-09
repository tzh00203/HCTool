# VULN-064 Result

## Verdict: [poc-success] CONFIRMED

keymgr CTRL.FSM.CONSISTENCY SEC_CM anchor is only in `keymgr_err.sv` (sink, line 124),
missing from `keymgr_ctrl.sv` (source of `state_change_err` and `op_state_cmd_err`).
Cross-module coverage gap: modifying consistency check logic in `keymgr_ctrl.sv`
would not be flagged by SEC_CM verification since the anchor is only at the consumer.

## Fidelity: L4 (static conclusion)

Pure oracle comparison — cross-module anchor gap verification via grep, no dynamic simulation.

## Evidence

### Check 1: CTRL.FSM.CONSISTENCY anchor in keymgr_err.sv
```
$ grep -n 'CTRL\.FSM\.CONSISTENCY' keymgr_err.sv
124:  // SEC_CM: CTRL.FSM.CONSISTENCY
```

### Check 2: CTRL.FSM.CONSISTENCY anchor NOT in keymgr_ctrl.sv
```
$ grep -c 'CTRL\.FSM\.CONSISTENCY' keymgr_ctrl.sv
0
```

### Check 3: Anchor signal mapping in keymgr_err.sv
```
$ grep -n 'AsyncFaultFsmChk' keymgr_err.sv
125:  assign async_fault_d[AsyncFaultFsmChk]   = state_change_err_i | op_state_cmd_err_i;
146:  assign fault_o[FaultCtrlFsmChk] = async_fault_o[AsyncFaultFsmChk];
```

### Check 4: Signal generation in keymgr_ctrl.sv
```
state_change_err (line 833): assign state_change_err = vld_state_change_q & !adv_op;
op_state_cmd_err (lines 778-779): assign op_state_cmd_err = (adv_en_o & ~(advance_sel | disable_sel)) |
                                                    (gen_en_o & ~gen_op);
```

### Check 5: Cross-module port connection in keymgr_ctrl.sv
```
$ grep -n 'state_change_err_i\|op_state_cmd_err_i' keymgr_ctrl.sv
855:    .state_change_err_i(state_change_err),
856:    .op_state_cmd_err_i(op_state_cmd_err),
```

### Check 6: Existing SEC_CM anchors in keymgr_ctrl.sv
```
20:  // SEC_CM: CTRL.FSM.GLOBAL_ESC
260:  // SEC_CM: CTRL.FSM.SPARSE
302:  //SEC_CM: CTRL.KEY.INTEGRITY
420:  // SEC_CM: CTRL.CTR.REDUN
462:  // SEC_CM: CTRL.FSM.LOCAL_ESC
(missing: CTRL.FSM.CONSISTENCY)
```

## Reproduction Commands

```bash
# Full verification
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-064/verify_anchor.sh /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind

# Python PoC (redbud mode)
python3 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-064/exploit.py

# Quick manual check
grep 'CTRL\.FSM\.CONSISTENCY' /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/keymgr/rtl/keymgr_ctrl.sv
# Expected: no match (exit 1) = confirmed cross-module gap
```

## Twin Repair

- **File**: `keymgr_ctrl_twin.sv`
- **Change**: Added `// SEC_CM: CTRL.FSM.CONSISTENCY` at two locations:
  1. Before `op_state_cmd_err` definition (line 775) — operation-state consistency check
  2. Before `state_change_err` definition (line 830) — state-advance consistency check
- **Oracle**: keymgr_err.sv:124 already has `// SEC_CM: CTRL.FSM.CONSISTENCY` for the sink (`AsyncFaultFsmChk`); twin adds it at the source to close the cross-module gap. Pattern matches existing anchors in keymgr_ctrl.sv (CTRL.FSM.SPARSE at line 260, CTRL.FSM.LOCAL_ESC at line 462).
- **Diff**: 2 lines added (two SEC_CM comment lines only)

## Impact

Missing SEC_CM anchor at the source module means:
- SEC_CM verification (V2S security countermeasure testing) only traces through `keymgr_err.sv`
- Modifying `state_change_err` or `op_state_cmd_err` in `keymgr_ctrl.sv` (e.g., weakening the check, removing a term, changing polarity) would not be flagged as a countermeasure regression
- The cross-module path (keymgr_ctrl generates check → keymgr_err consumes check) has incomplete coverage
- Other CTRL.* SEC_CM anchors (SPARSE, LOCAL_ESC, GLOBAL_ESC, CTR.REDUN, KEY.INTEGRITY) are all in keymgr_ctrl.sv; CONSISTENCY is the only outlier placed solely in keymgr_err.sv

## Related Findings

- **VULN-023**: keymgr_data_en_state default branch doesn't set fsm_err_o — another CTRL.FSM consistency issue (sparse FSM error detection)

## Upgrade (2026-09-23)

### Verdict: [poc-success] CONFIRMED at L3

Upgraded from L4 (static conclusion) to L3 (script-level empirical).

### Sub-claim decomposition

| Claim | Type | Level | Result | Method |
|-------|------|-------|--------|--------|
| C1: CTRL.FSM.CONSISTENCY anchor in keymgr_err.sv but absent from keymgr_ctrl.sv (cross-module gap) | Declaration gap | L3 | CONFIRMED | Python script: grep SEC_CM anchors in both files + trace signal flow (AsyncFaultFsmChk←state_change_err_i/op_state_cmd_err_i) |
| C2: CONSISTENCY is the only CTRL.* anchor not in keymgr_ctrl.sv — all 5 other CTRL.* anchors are in ctrl | Declaration gap | L3 | CONFIRMED | Python script: enumerate CTRL.* anchors across both files, compute set difference |
| C3: hjson declares CTRL.FSM.CONSISTENCY, testplan targets u_ctrl signals, but anchor missing from keymgr_ctrl.sv | Declaration gap | L3 | CONFIRMED | Python script: parse hjson countermeasures + grep testplan for sec_cm_ctrl_fsm_consistency |

### L2 not achievable

SEC_CM comment annotations have no I/O behavioral effect. Adding `// SEC_CM: CTRL.FSM.CONSISTENCY` to keymgr_ctrl.sv does not change any signal value, output, or timing. No micro-tb differential is possible — this is purely a structural/declarative gap.

### Evidence (L3 script proof)

```
C1: CTRL.FSM.CONSISTENCY anchor cross-module gap
  keymgr_err.sv CTRL.FSM.CONSISTENCY anchors: 1 (line 124)
  keymgr_ctrl.sv CTRL.FSM.CONSISTENCY anchors: 0
  Signal flow: keymgr_err.sv:125 AsyncFaultFsmChk = state_change_err_i | op_state_cmd_err_i
               keymgr_ctrl.sv:833 state_change_err = vld_state_change_q & !adv_op
               keymgr_ctrl.sv:778 op_state_cmd_err = (adv_en_o & ~(advance_sel | disable_sel)) | ...
               keymgr_ctrl.sv:855 .state_change_err_i(state_change_err)
               keymgr_ctrl.sv:856 .op_state_cmd_err_i(op_state_cmd_err)

C2: CONSISTENCY is sole CTRL.* outlier
  CTRL.* anchors in keymgr_ctrl.sv (5): CTRL.FSM.GLOBAL_ESC(L20), CTRL.FSM.SPARSE(L260), CTRL.KEY.INTEGRITY(L302), CTRL.CTR.REDUN(L420), CTRL.FSM.LOCAL_ESC(L462)
  CTRL.* anchors in keymgr_err.sv (1): CTRL.FSM.CONSISTENCY(L124)
  Set difference (err-only): {CTRL.FSM.CONSISTENCY}

C3: hjson/testplan gap
  hjson countermeasure: CTRL.FSM.CONSISTENCY declared (6 CTRL.* total in hjson)
  testpoint: sec_cm_ctrl_fsm_consistency at line 140, stage V2S, tests: keymgr_custom_cm
  testplan desc forces tb.dut.u_ctrl.adv_en_o / u_ctrl.gen_en_o (keymgr_ctrl instance)
  Anchor NOT in keymgr_ctrl.sv: CONFIRMED
```

### Reproduction Commands

```bash
# L3 script proof (exit 1 = confirmed)
python3 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-064/upgrade/prove_cross_module_gap.py --repo /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind

# Original L4 verification (still valid)
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-064/verify_anchor.sh /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
```
