# RESULT: VULN-029 — Ascon lc_escalate_en_i unused

## Verdict: [poc-success]

## Fidelity: L2 (data-flow evidence, combinational micro-tb)

## Finding

ascon_core.sv:146 assigns `lc_escalate_en_i` to `unused_lc_escalate_en_i` — lifecycle escalation
is completely disconnected from alert logic. `alert_fatal_o = duplex_fatal_error` (line 125) has
no lc_escalate_en_i term. When lc_escalate_en_i is asserted (On), the module produces no alert,
no FSM enters ErrorSt, and the cryptographic operation continues uninterrupted. The TODO comment
at line 145 ("TODO Add escalation Input") confirms this was intended but never implemented.

SEC_CM: ESCALATE_LOC.ESCALATE (from ascon.hjson) is violated — the security countermeasure
is a no-op.

## Twin Repair

Removed `assign unused_lc_escalate_en_i = lc_escalate_en_i;` dead sink.
Added `lc_escalate = lc_tx_test_true_strict(lc_escalate_en_i)` and changed
`alert_fatal_o = duplex_fatal_error | lc_escalate`.
Oracle: sibling modules (aes_core, kmac_core, entropy_src_core) all OR
lc_tx_test_true_strict(lc_escalate_en_i) into alert_fatal_o.
Also ascon_core.sv:145 TODO comment and SEC_CM: ESCALATE_LOC.ESCALATE.

## Test Method

Combinational micro-tb comparing alert_fatal_o expressions:
- **vuln**: `alert_fatal = duplex_fatal_error` (no lc escalation term)
- **twin**: `alert_fatal = duplex_fatal_error | lc_tx_test_true_strict(lc_escalate_en_i)`

With lc_escalate_en_i=On, duplex_fatal_error=0:
- vuln: alert_fatal = 0 (no response to lifecycle escalation)
- twin: alert_fatal = 1 (escalation correctly triggers fatal alert)

## Evidence

```
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: Ascon lc_escalate_en_i assigned to unused_lc_escalate_en_i,
  alert_fatal_o = duplex_fatal_error (no lc escalation term).
  With lc_escalate_en_i=On, alert_fatal_o stays 0 — no response to lifecycle escalation.
  Twin: alert_fatal_o = duplex_fatal_error | lc_tx_test_true_strict(lc_escalate_en_i)
  (oracle: sibling modules + ascon_core.sv:145 TODO + SEC_CM: ESCALATE_LOC.ESCALATE)
exit code: 1 (1 = finding confirmed)
```

## Build & Run

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-029
bash build_ascon_lc_escalate.sh
# exit code 1 = finding confirmed
```

## Deliverables

| File | Description |
|------|-------------|
| `tb_ascon_lc_escalate.sv` | Combinational micro-tb (vuln vs twin alert expression) |
| `lc_ctrl_pkg_stub.sv` | Minimal stub for lc_ctrl_pkg (lc_tx_t + test functions) |
| `sim_main.cpp` | C++ driver |
| `build_ascon_lc_escalate.sh` | Verilator build script |
| `exploit.py` | PoC entry (redbud mode) |
