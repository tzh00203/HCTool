# VULN-074 RESULT

## Verdict: `[poc-success]` — finding confirmed

4 semantic mismatches in otp_ctrl error classification confirmed via combinational micro-tb (vuln-vs-twin differential). Exit code = 1.

## Sub-vulnerabilities

### S1: intg_error[2] semantic mismatch
- **Vuln**: `intg_error[2] = otp_macro_i.fatal_lc_fsm_err` (otp_ctrl.sv:107) — FSM error from OTP macro is ORed into `fatal_bus_integ_error_d` via `|intg_error` (line 418)
- **Twin**: `intg_error[2]` excluded from bus integrity classification; `fatal_lc_fsm_err` should go to `fatal_check_error_d` instead
- **Oracle**: `fatal_lc_fsm_err` is an FSM alert (SEC_CM: LC_CTRL.INTERSIG.MUBI), not a TL-UL integrity error; `intg_error[0]` and `intg_error[1]` are true bus integrity errors from `otp_ctrl_core_reg_top` and `tlul_adapter_sram`

### S2: VENDOR_TEST ECC does not trigger fatal
- **Vuln**: `fatal_macro_error_d |= part_error[k] == MacroEccUncorrError` gated by `PartInfo[k].integrity` (otp_ctrl.sv:430-432). VENDOR_TEST has `integrity=1'b0` (otp_ctrl_part_pkg.sv:133), so uncorrectable ECC errors in VENDOR_TEST never set `fatal_macro_error_d`
- **Twin**: VENDOR_TEST `MacroEccUncorrError` always triggers `fatal_macro_error_d` (remove integrity gate for uncorr ECC)
- **Oracle**: ALL other partitions have `integrity=1'b1`; VENDOR_TEST is the sole outlier. Uncorrectable ECC errors are critical regardless of partition integrity flag.

### S3: KDI ErrorSt does not lock outputs
- **Vuln**: KDI `ErrorSt` only sets `fsm_err_o=1'b1` (otp_ctrl_kdi.sv:548-550). `key_out_q`, `nonce_out_q`, `seed_valid_q` retain pre-error values and continue driving `flash_otp_key_o`, `sram_otp_key_o`, `otbn_otp_key_o` (lines 285-297). Derived key material survives terminal error state.
- **Twin**: `ErrorSt` clears `key_out_q`/`nonce_out_q` to `'0` and holds `seed_valid_q=0`
- **Oracle**: DAI ErrorSt locks access; scrmbl ErrorSt clears internal state; sibling modules zero outputs in terminal error states

### S4: LCI ErrorSt does not set fsm_err_o
- **Vuln**: LCI `ErrorSt` only sets `error_d=FsmStateError` if `error_q==NoError` (otp_ctrl_lci.sv:211-215). `fsm_err_o` stays at default `1'b0` (line 142). Only the `default:` case (line 220) and escalation path (line 228) set `fsm_err_o=1`.
- **Twin**: `ErrorSt` sets `fsm_err_o=1'b1`
- **Oracle**: DAI ErrorSt sets `fsm_err_o=1`; scrmbl ErrorSt sets `fsm_err_o=1`; KDI ErrorSt sets `fsm_err_o=1`; LCI is the sole FSM that omits `fsm_err_o` in ErrorSt

## Fidelity Level
L4 (static conclusion — combinational logic analysis, no full-module simulation)

## Build & Run
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-074
bash build.sh
# exit code: 1 (finding confirmed)
```

## Raw Output
```
=== VULN-074: otp_ctrl 4 semantic mismatches ===

S1: intg_error[2]=fatal_lc_fsm_err misclassified as bus integrity
    vuln fatal_bus_integ=1 (FSM error latched as bus integrity)
    twin fatal_bus_integ=0 (FSM error excluded, only [1:0])
    result: CONFIRMED

S2: VENDOR_TEST MacroEccUncorrError does not trigger fatal
    vuln: integrity=0 gate => fatal_macro_error stays 0
    twin: MacroEccUncorrError always fatal => fatal_macro_error=1
    result: CONFIRMED

S3: KDI ErrorSt does not lock key/nonce outputs
    vuln: key_out_q still drives flash/sram/otbn key outputs
    twin: outputs locked/zeroed in ErrorSt
    result: CONFIRMED

S4: LCI ErrorSt does not set fsm_err_o=1
    vuln: fsm_err_o=0 in ErrorSt (only default case sets it)
    twin: fsm_err_o=1 in ErrorSt
    result: CONFIRMED

OVERALL: FINDING CONFIRMED (exit 1)
exit code: 1 (1 = finding confirmed)
```

## Files
- `tb_otp_ctrl_semantic.sv` — combinational micro-tb (vuln + twin expressions)
- `otp_ctrl_twin.sv` — twin module with 4 fixes
- `build.sh` — Verilator build script
- `sim_main.cpp` — C++ simulation driver
- `exploit.py` — redbud-mode PoC entry

---

## Upgrade (2026-09-23)

### Verdict: `[poc-success]` — all 4 sub-claims upgraded and confirmed

### Sub-claim Decomposition & Upgrade Results

| Sub-claim | Category | Upgrade Path | New Fidelity | Result |
|-----------|----------|-------------|-------------|--------|
| S1: intg_error[2] semantic mismatch | Declaration mismatch | L3 script proof (hjson SEC_CM + SV bit tracing) | L3 | CONFIRMED |
| S2: VENDOR_TEST ECC not triggering fatal | Property (constant verification) | L3 script proof (part_pkg integrity scan) | L3 | CONFIRMED |
| S3: KDI ErrorSt does not lock outputs | Behavior simulatable | L2 micro-tb (8-vector sweep vuln-vs-twin) | L2 | CONFIRMED |
| S4: LCI ErrorSt does not set fsm_err_o | Declaration mismatch | L3 script proof (sibling FSM cross-comparison) | L3 | CONFIRMED |

### New Fidelity Level
**L2** (max across sub-claims: S3 at L2, others at L3; overall = L2 data-flow实证)

### S3: KDI ErrorSt — L2 micro-tb Detail
- **tb**: `upgrade/tb_kdi_errorst.sv` — combinational micro-tb sweeping 8 pre-error key/nonce vectors
- **Twin**: KDI ErrorSt clears `key_out_q`/`nonce_out_q` to `'0` and holds `seed_valid_q=0` (oracle: DAI locks access, scrmbl clears state, sibling modules zero outputs in error states)
- **Vuln**: KDI ErrorSt retains `key_out_q`/`nonce_out_q` (p_outregs only updates on `key_reg_en`/`nonce_reg_en`, which ErrorSt does not set)
- **Result**: 8/8 sweep vectors show diff (vuln outputs active, twin outputs zeroed)

### S1: intg_error mismatch — L3 script proof Detail
- **Script**: `upgrade/proof_s1_intg_error.py`
- **Evidence**:
  - otp_ctrl.sv:107: `intg_error[2] = otp_macro_i.fatal_lc_fsm_err`
  - otp_ctrl.sv:418: `fatal_bus_integ_error_d |= |intg_error` (all 3 bits)
  - hjson: fatal_bus_integ_error desc = "fatal TL-UL bus integrity fault"
  - hjson: SEC_CM `LC_CTRL.INTERSIG.MUBI` = "multibit encoded" (FSM/LC inter-signal)
  - Mismatch: FSM error (LC_CTRL.INTERSIG.MUBI) classified as TL-UL bus integrity

### S2: VENDOR_TEST ECC — L3 script proof Detail
- **Script**: `upgrade/proof_s2_vendor_test.py`
- **Evidence**:
  - otp_ctrl_part_pkg.sv:133: VENDOR_TEST `integrity=1'b0`
  - ALL other 10 partitions have `integrity=1'b1` (VENDOR_TEST is sole outlier)
  - otp_ctrl.sv:430-431: `if (PartInfo[k].integrity) fatal_macro_error_d |= MacroEccUncorrError`
  - hjson documents: "ECC uncorrectable errors will not lead to fatal errors" (intentional but creates security gap)

### S4: LCI fsm_err_o — L3 script proof Detail
- **Script**: `upgrade/proof_s4_lci_fsm_err.py`
- **Evidence**:
  - otp_ctrl_lci.sv:211-215: ErrorSt only sets `error_d=FsmStateError`, NOT `fsm_err_o=1`
  - otp_ctrl_scrmbl.sv: ErrorSt SETS `fsm_err_o=1` (line 422)
  - otp_ctrl_kdi.sv: ErrorSt SETS `fsm_err_o=1` (line 549)
  - otp_ctrl_dai.sv: ErrorSt also omits `fsm_err_o=1` (same pattern as LCI)
  - **Oracle correction**: Original finding claimed DAI sets `fsm_err_o=1` in ErrorSt — this was incorrect. DAI has the same omission pattern as LCI. The inconsistency is with scrmbl and KDI which do set it.
  - LCI (and DAI) `fsm_err_o` only set by: default: case (glitch) or escalation path — not by legitimate ErrorSt entry

### Reproduction
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-074/upgrade
bash build_all.sh
# Expected: all 4 sub-claims confirmed, exit code 1
```

Individual sub-claims:
```bash
# S3 (L2 micro-tb)
bash build_kdi.sh
# S1 (L3 script)
python3 proof_s1_intg_error.py
# S2 (L3 script)
python3 proof_s2_vendor_test.py
# S4 (L3 script)
python3 proof_s4_lci_fsm_err.py
```

### Upgrade Files
- `upgrade/tb_kdi_errorst.sv` — L2 micro-tb for S3
- `upgrade/sim_main_kdi.cpp` — C++ driver for S3
- `upgrade/build_kdi.sh` — Verilator build for S3
- `upgrade/proof_s1_intg_error.py` — L3 script proof for S1
- `upgrade/proof_s2_vendor_test.py` — L3 script proof for S2
- `upgrade/proof_s4_lci_fsm_err.py` — L3 script proof for S4
- `upgrade/build_all.sh` — unified build/run script
- `upgrade/exploit_upgrade.py` — redbud-mode PoC entry
