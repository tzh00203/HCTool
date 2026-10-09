# RESULT: VULN-016

## Verdict: poc-success (L2 fidelity)

## Finding

Ascon `start_ok` gate on line 478 of `ascon_core.sv` only checks `key_error` but not `nonce_error`:

```
assign start_ok = start & ~key_error;    // line 478 — VULN
assign start_ok = start & ~key_error & ~nonce_error;  // TWIN (correct)
```

When `nonce_error=1` (nonce not loaded) and `key_error=0` (key valid), the vuln allows `start_ok=1`, permitting the AEAD operation to start without a nonce. This enables nonce reuse, which breaks AEAD confidentiality and integrity guarantees.

The twin adds `& ~nonce_error` to the gate. Oracle evidence:
- Line 471: `nonce_error = lack_nonce_inputs` — defined as a real error condition
- Lines 493-494: `hw2reg.error.no_nonce` — reported to SW as an error
- Line 526: `ascon_error = key_error | nonce_error | flag_error | order_error` — nonce_error is treated as a real error in the aggregated status

## Reproduction

```bash
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-016/build_ascon_nonce_gate.sh
```

## Raw Output

```
start=1, key_error=0, nonce_error=1:
  vuln start_ok = 1  (should be 1: nonce not checked)
  twin start_ok = 1  (should be 0: nonce blocks start)
CONFIRMED: ascon_core.sv:478 start_ok = start & ~key_error
  missing nonce_error gate — nonce reuse possible.
  Vuln: start_ok=1 when nonce not loaded (nonce_error=1).
  Twin: start_ok = start & ~key_error & ~nonce_error blocks start.
  Oracle: nonce_error defined at line 471, reported to SW (line 493-494),
  included in ascon_error (line 526) — must also gate start_ok.
exit code: 1 (1 = finding confirmed)
```

## Twin Repair Diff

Only line 478 changed:
```
- assign start_ok = start & ~key_error;
+ assign start_ok = start & ~key_error & ~nonce_error;  // Oracle: nonce_error defined L471, reported L493-494, in ascon_error L526
```

Oracle basis: in-tree — nonce_error is defined as a real error condition (line 471), reported to software (lines 493-494), and included in the aggregated ascon_error (line 526). It must also gate start_ok for security.

## Deliverables

- `tb_ascon_nonce_gate.sv` — combinational micro-tb
- `sim_main.cpp` — C++ driver
- `build_ascon_nonce_gate.sh` — Verilator build script
- `exploit.py` — redbud-mode PoC entry
