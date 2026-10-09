# Oracle Certification — VULN-064

Generated: 2026-10-09 18:33 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle**: keymgr_err.sv:124 already has `// SEC_CM: CTRL.FSM.CONSISTENCY` for the sink (`AsyncFaultFsmChk`); twin adds it at the source to close the cross-module gap. Pattern matches existing anchors in keymgr_ctrl.sv (CTRL.FSM.SPARSE at line 260, CTRL.FSM.LOCAL_ESC at line 462).
- SEC_CM anchor
- SEC_CM verification
- SEC_CM anchors
- SEC_CM comment

## Evidence Log (excerpt)

```
146:  assign fault_o[FaultCtrlFsmChk] = async_fault_o[AsyncFaultFsmChk];
state_change_err_i refs in keymgr_err.sv: 2
op_state_cmd_err_i refs in keymgr_err.sv: 2
CONFIRMED: keymgr_err.sv AsyncFaultFsmChk maps state_change_err_i | op_state_cmd_err_i

--- Step 4: Signal generation in keymgr_ctrl.sv ---
state_change_err refs in keymgr_ctrl.sv: 3
op_state_cmd_err refs in keymgr_ctrl.sv: 3
CONFIRMED: keymgr_ctrl.sv generates state_change_err and op_state_cmd_err

  state_change_err definition:
832:  logic state_change_err;
833:  assign state_change_err = vld_state_change_q & !adv_op;
855:    .state_change_err_i(state_change_err),

  op_state_cmd_err definition:
777:  logic op_state_cmd_err;
778:  assign op_state_cmd_err = (adv_en_o & ~(advance_sel | disable_sel)) |
856:    .op_state_cmd_err_i(op_state_cmd_err),

--- Step 5: Cross-module port connection ---
state_change_err_i(state_change_err) connection: 1
op_state_cmd_err_i(op_state_cmd_err) connection: 1
CONFIRMED: cross-module port connection exists

--- Step 6: Existing SEC_CM anchors in keymgr_ctrl.sv ---
20:  // SEC_CM: CTRL.FSM.GLOBAL_ESC
260:  // SEC_CM: CTRL.FSM.SPARSE
302:  //SEC_CM: CTRL.KEY.INTEGRITY
420:  // SEC_CM: CTRL.CTR.REDUN
462:  // SEC_CM: CTRL.FSM.LOCAL_ESC

=== VERDICT ===
[poc-success] FINDING CONFIRMED: CTRL.FSM.CONSISTENCY anchor is cross-module
  - Anchor exists in keymgr_err.sv (line 124) but NOT in keymgr_ctrl.sv
  - keymgr_ctrl.sv generates state_change_err (line 833) and op_state_cmd_err (lines 777-779)
  - keymgr_err.sv maps these to AsyncFaultFsmChk (line 125)
  - Cross-module gap: modifying keymgr_ctrl.sv consistency checks
    would not be flagged by SEC_CM verification (anchor missing at source)
  Fidelity: L4 (static conclusion, cross-module structural gap)
```
