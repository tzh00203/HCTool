# RESULT: VULN-065

## Verdict
**[poc-success]** keymgr_ctrl.sv:784 op_update_sel race window in invalid state — KMAC data written to key_state even in StCtrlInvalid fault state.

## Fidelity
L2 (combinational micro-tb, expression-level)

## Vulnerability
In `keymgr_ctrl.sv:784`, the `op_update_sel` priority mux selects `KeyUpdateKmac` when `invalid=1` and `(op_ack|op_update)=1`:
```systemverilog
assign op_update_sel = (op_ack | op_update) & invalid      ? KeyUpdateKmac : ...
```
This creates a race window: when an async fault (`inv_state`) is asserted in the same cycle as `op_ack`, KMAC data is written into `key_state` even though the FSM is in `StCtrlInvalid` (fault state). The KMAC result persists in key state, contradicting the invariant that invalid/fault states must not modify key material.

## Twin Fix
When `invalid=1`, use `KeyUpdateIdle` instead of `KeyUpdateKmac`:
```systemverilog
assign op_update_sel = (op_ack | op_update) & invalid      ? KeyUpdateIdle : ...  // FIX
```
Oracle: `StCtrlInvalid` (line 676-679) is a fault state; KMAC results must not update `key_state`. Same pattern as `op_err` branch (`KeyUpdateIdle` = no key_state update).

## Evidence
```
Build: Verilator --cc --exe, combinatorial tb (no clock needed)
Run:   ./obj/Vtb
Output:
  op_ack|op_update=1, invalid=1: vuln allows KMAC write: YES  twin blocks KMAC write: YES
  CONFIRMED: keymgr_ctrl.sv:784 op_update_sel race window in invalid state
  exit code: 1 (1 = finding confirmed)
```

## Files
- `tb_keymgr_op_update_sel_race.sv` — micro-tb (vuln vs twin dual expression comparison)
- `sim_main.cpp` — C++ driver
- `build.sh` — Verilator 4.210 build script
- `exploit.py` — redbud-mode PoC entry

## Commands
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-065
bash build.sh
# exit code 1 = finding confirmed
```
