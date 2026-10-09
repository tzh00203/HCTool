# Oracle Certification — VULN-031

Generated: 2026-10-09 18:32 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: poc-success
Fidelity: L3
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- oracle**: sibling IP hjson `countermeasures` fields (AES=28 entries, KMAC=14, HMAC=1)
- oracle**: RTL signal/instance names matching standard OpenTitan countermeasure primitives (prim_count, sparse_fsm_error, prim_alert_sender, mubi4_test_invalid, lc_escalate_en, shadowed registers, intg_err)
- sec_cm field
- sec_cm testplans

## Evidence Log (excerpt)

```
=== VULN-031: Ascon hjson sec_cm field verification ===

--- Step 1: Check hjson for sec_cm field ---
sec_cm occurrences in ascon.hjson: 0
CONFIRMED: ascon.hjson has NO sec_cm field

--- Step 2: Check for sec_cm_testplan.hjson ---
CONFIRMED: ascon_sec_cm_testplan.hjson does NOT exist

--- Step 3: Check RTL for security countermeasure implementations ---
Shadowed registers in hjson: 3 (CTRL_SHADOWED, CTRL_AUX_SHADOWED, BLOCK_CTRL_SHADOWED)
prim_count in prim_ascon_duplex.sv: 1 (round counter)
sparse_fsm_error in prim_ascon_duplex.sv: 5 (sparse FSM encoding)
intg_err in ascon.sv: 3 (TL-UL bus integrity)
prim_alert_sender in ascon.sv: 2 (alert primitives)
mubi4_test_invalid in ascon_core.sv: 2 (mubi4 invalid-value checks)
lc_escalate_en in ascon_core.sv: 3 (lifecycle escalation)

--- Step 4: Compare with sibling IPs ---
AES: sec_cm entries=0, sec_cm_testplan=exists
KMAC: sec_cm entries=0, sec_cm_testplan=exists
HMAC: sec_cm entries=0, sec_cm_testplan=exists

=== VERDICT ===
[poc-success] FINDING CONFIRMED: ascon.hjson has NO sec_cm field,
  but RTL implements security countermeasures:
  - 3 shadowed register(s) (CTRL_SHADOWED, CTRL_AUX_SHADOWED, BLOCK_CTRL_SHADOWED)
  - prim_count round counter in prim_ascon_duplex
  - sparse FSM encoding in prim_ascon_duplex (sparse_fsm_error)
  - TL-UL bus integrity (intg_err)
  - mubi4 invalid-value validation (no_ad, no_msg)
  - lc_escalate_en lifecycle escalation
  Missing sec_cm declaration means:
  - No auto-generated sec_cm_testplan.hjson
  - No V2S verification coverage for security countermeasures
  - reggen cannot validate countermeasure completeness
  Fidelity: L4 (static conclusion, no dynamic simulation)
```
