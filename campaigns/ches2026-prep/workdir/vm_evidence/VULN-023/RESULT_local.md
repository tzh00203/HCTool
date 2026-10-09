# VULN-023 — keymgr_data_en_state FSM default 不设 fsm_err_o

## Verdict: [poc-success] L2 fidelity

## Finding

keymgr_data_en_state.sv:127-129: sparse FSM `default` branch sets `state_d = StCtrlDataDis`
but does **not** set `fsm_err_o = 1'b1`. When a fault pushes the FSM into an illegal
state encoding (Hamming-distance-5 sparse encoding), the error goes undetected.
The `SEC_CM: DATA.FSM.SPARSE` annotation claims error detection, but the default
branch silently transitions to Dis instead of flagging the error.

## Twin Repair

Diff (only the default branch):
```diff
       default: begin
         state_d = StCtrlDataDis;
+        fsm_err_o = 1'b1;  // oracle: keymgr_ctrl default + SEC_CM: DATA.FSM.SPARSE
       end
```
Oracle: sibling `keymgr_ctrl` module sets `fsm_err_o = 1'b1` in its default branch;
`SEC_CM: DATA.FSM.SPARSE` annotation at line 68 expects error detection.

## Reproduction

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-023
bash build_data_en_fsm_err.sh
# exit code 1 = finding confirmed
```

## Raw Output

```
vuln fsm_err_o: 1  twin fsm_err_o: 1
CONFIRMED: keymgr_data_en_state.sv:127 default branch doesn't set fsm_err_o
  vuln: fsm_err_o=0 in default (illegal FSM state undetected)
  twin: fsm_err_o=1 in default (oracle: keymgr_ctrl pattern + SEC_CM: DATA.FSM.SPARSE)
exit code: 1 (1 = finding confirmed)
```

## Deliverables

| File | Description |
|---|---|
| tb_data_en_fsm_err.sv | Combinational micro-tb: injects illegal FSM state, checks fsm_err_o |
| keymgr_data_en_state_twin.sv | Twin with fsm_err_o=1 in default branch |
| sim_main.cpp | C++ driver |
| build_data_en_fsm_err.sh | Verilator 4.210 build script |
| exploit.py | PoC entry (redbud mode) |
