# VULN-031: Ascon hjson missing sec_cm field

## Verdict: **poc-success** (finding confirmed)

## Fidelity: L4 (static conclusion)

## Summary

ascon.hjson has NO `sec_cm` field and no `ascon_sec_cm_testplan.hjson` exists,
but the RTL implements multiple security countermeasures. This mismatch means
the IP's security countermeasures are undeclared and unverified at the V2S level.

## Evidence

### Step 1: hjson sec_cm field check
```
$ grep -c 'sec_cm' ascon.hjson
0
```
ascon.hjson has zero `sec_cm` occurrences. No `ascon_sec_cm_testplan.hjson` file exists.

### Step 2: RTL security countermeasure inventory

| Countermeasure | Location | Evidence |
|---|---|---|
| 3x shadowed registers | ascon.hjson (CTRL_SHADOWED, CTRL_AUX_SHADOWED, BLOCK_CTRL_SHADOWED) | `shadowed: "true"` declarations |
| prim_count round counter | prim_ascon_duplex.sv:172 | `prim_count #(...)` instantiation |
| Sparse FSM encoding | prim_ascon_duplex.sv | `sparse_fsm_error` signal, 5 references |
| TL-UL bus integrity | ascon.sv:67,122 | `intg_err_o(intg_err_alert)`, 3 references |
| prim_alert_sender | ascon.sv:134-147 | 2 instances (fatal + recoverable) |
| mubi4 invalid-value checks | ascon_core.sv:277,285 | `mubi4_test_invalid` on no_ad, no_msg |
| lc_escalate_en | ascon_core.sv:15,146 | lifecycle escalation input (note: currently unused) |

### Step 3: Sibling IP comparison

| IP | sec_cm_testplan.hjson |
|---|---|
| AES | exists |
| KMAC | exists |
| HMAC | exists |
| **Ascon** | **MISSING** |

All sibling cryptographic IPs (AES, KMAC, HMAC) have sec_cm testplans. Ascon is the outlier.

## Impact

Missing `sec_cm` declaration means:
- No auto-generated `ascon_sec_cm_testplan.hjson` by reggen
- No V2S verification coverage for security countermeasures
- reggen cannot validate countermeasure completeness against RTL
- Verification gap: sparse FSM, prim_count, shadowed reg, TL-UL integrity, mubi4, lc_escalate are all unverified at V2S

## Execution

```
Command: bash verify_sec_cm.sh /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
Exit code: 1 (finding confirmed)
```

## Files

- `verify_sec_cm.sh` — static verification script (grep-based, L4)
- `exploit.py` — redbud-mode PoC wrapper

## Upgrade (2026-09-23)

### Verdict: **poc-success** (finding confirmed, upgraded L4→L3)

### Fidelity: L3 (script-level proof)

### Sub-claim decomposition & upgrade results

| Claim | Category | Description | Upgraded | Evidence |
|---|---|---|---|---|
| C1 | 声明缺失 | ascon.hjson has NO `countermeasures` field + no `ascon_sec_cm_testplan.hjson` | L4→L3 | Python script parses hjson, proves 0 entries programmatically |
| C2 | 属性缺失 | RTL implements 19 countermeasure anchors across 7 categories but hjson declares 0 | L4→L3 | Python script greps RTL anchors (shadowed=3, prim_count=1, sparse_fsm=5, intg_err=3, alert_sender=2, mubi4_invalid=2, lc_escalate=3) vs hjson countermeasures=0 |
| C3 | 声明缺失 | All sibling crypto IPs declare countermeasures (AES=28, KMAC=14, HMAC=1); Ascon=0 sole outlier | L4→L3 | Python script parses all 4 sibling hjson files, proves Ascon is unique missing |

L2 not achievable: `countermeasures`/`sec_cm` is hjson metadata for reggen testplan generation; it has no I/O behavioral effect on RTL simulation.

### Oracle basis

- **C1/C3 oracle**: sibling IP hjson `countermeasures` fields (AES=28 entries, KMAC=14, HMAC=1)
- **C2 oracle**: RTL signal/instance names matching standard OpenTitan countermeasure primitives (prim_count, sparse_fsm_error, prim_alert_sender, mubi4_test_invalid, lc_escalate_en, shadowed registers, intg_err)

### Reproduction

```bash
python3 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-031/upgrade/prove_sec_cm_gap.py
# Expected: exit 1 (finding confirmed)
```

### Script output (verbatim)

```
── Claim C1: ascon.hjson lacks countermeasures field ──
  countermeasures entries in ascon.hjson: 0
  ascon_sec_cm_testplan.hjson exists: False
  C1 verdict: CONFIRMED

── Claim C2: RTL has countermeasures, hjson declares 0 ──
  RTL countermeasure anchors found: 19 across 7 categories
    shadowed_regs: 3 shadowed register(s) in ascon.hjson
    prim_count: prim_count in prim_ascon_duplex.sv: 1
    sparse_fsm: sparse_fsm_error in prim_ascon_duplex.sv: 5
    intg_err: intg_err in ascon.sv: 3
    alert_sender: prim_alert_sender in ascon.sv: 2
    mubi4_invalid: mubi4_test_invalid in ascon_core.sv: 2
    lc_escalate: lc_escalate_en in ascon_core.sv: 3
  hjson countermeasures declared: 0
  C2 verdict: CONFIRMED

── Claim C3: Ascon is sole outlier — siblings declare countermeasures ──
  aes: countermeasures=28, sec_cm_testplan=exists
  kmac: countermeasures=14, sec_cm_testplan=exists
  hmac: countermeasures=1, sec_cm_testplan=exists
  ascon: countermeasures=0, sec_cm_testplan=MISSING
  C3 verdict: CONFIRMED
```

### Files (upgrade)

- `upgrade/prove_sec_cm_gap.py` — L3 script proof (all 3 claims, exit 1 = confirmed)
