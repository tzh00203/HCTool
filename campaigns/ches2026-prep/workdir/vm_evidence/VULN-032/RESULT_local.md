# VULN-032 Result

## Verdict: [poc-success] CONFIRMED

KMAC hjson `countermeasures` list lacks `MSG.MASKING` SEC_CM declaration despite the `msg_mask` register field (line 559) and masking hardware existing.

## Fidelity: L4 (static conclusion)

Pure oracle comparison — hjson grep verification, no dynamic simulation.

## Evidence

### Check 1: msg_mask register field exists
```
$ grep -n 'name: msg_mask' kmac.hjson
559:          name: msg_mask
```

### Check 2: MSG.MASKING absent from vuln countermeasures
```
$ grep '"MSG.MASKING"' kmac.hjson
(no match — exit 1)
```

### Check 3: MSG.MASKING present in twin countermeasures
```
$ grep '"MSG.MASKING"' kmac_twin.hjson
    { name: "MSG.MASKING"
(1 match)
```

### Check 4: Diff minimal (3 lines — the added countermeasure entry)
```
$ diff kmac.hjson kmac_twin.hjson
<   (no MSG.MASKING entry)
>     { name: "MSG.MASKING"
>       desc: "Message masking with PRNG when cfg_shadowed.msg_mask is set."
>     }
```

## Reproduction Commands

```bash
# Full verification
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-032/build.sh

# Python PoC (redbud mode)
python3 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-032/exploit.py

# Quick manual check
grep '"MSG.MASKING"' /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/data/kmac.hjson
# Expected: no match (exit 1) = confirmed
```

## Twin Repair

- **File**: `kmac_twin.hjson`
- **Change**: Added `{ name: "MSG.MASKING", desc: "Message masking with PRNG when cfg_shadowed.msg_mask is set." }` to countermeasures list after `SW_KEY.KEY.MASKING`
- **Oracle**: `msg_mask` register field (line 559) with desc "Message Masking with PRNG" + VULN-012 confirmed masking hardware exists (g_msg_mask block) + SW_KEY.KEY.MASKING already declared in countermeasures (parallel masking feature)
- **Diff**: 3 lines added (the MSG.MASKING entry only)

## Vuln Countermeasures List (complete)

| # | Name | Present |
|---|---|---|
| 1 | BUS.INTEGRITY | yes |
| 2 | LC_ESCALATE_EN.INTERSIG.MUBI | yes |
| 3 | SW_KEY.KEY.MASKING | yes |
| 4 | KEY.SIDELOAD | yes |
| 5 | CFG_SHADOWED.CONFIG.SHADOW | yes |
| 6 | FSM.SPARSE | yes |
| 7 | CTR.REDUN | yes |
| 8 | PACKER.CTR.REDUN | yes |
| 9 | CFG_SHADOWED.CONFIG.REGWEN | yes |
| 10 | FSM.GLOBAL_ESC | yes |
| 11 | FSM.LOCAL_ESC | yes |
| 12 | LOGIC.INTEGRITY | yes |
| 13 | ABSORBED.CTRL.MUBI | yes |
| 14 | SW_CMD.CTRL.SPARSE | yes |
| **15** | **MSG.MASKING** | **MISSING** |

## Related Findings

- **VULN-012**: KMAC g_msg_mask uses static_mask (all-ones) instead of dynamic LFSR — the masking declared by msg_mask is functionally broken even when enabled. VULN-032 is the declaration gap; VULN-012 is the functional gap.

## Upgrade (2026-09-23)

### Verdict: [poc-success] CONFIRMED (upgraded L4 → L3)

### Sub-Claim Decomposition and Upgrade Results

| Claim | Description | Category | Upgrade | Evidence |
|---|---|---|---|---|
| C1 | msg_mask register field exists in kmac.hjson (bit 20) | attribute present | L4→L3 (script proof) | Python parser finds `name: msg_mask` at line 559, `bits: "20"` confirmed |
| C2 | MSG.MASKING absent from kmac.hjson countermeasures list | declaration missing | L4→L3 (script proof) | Python parser enumerates 14 countermeasures; MSG.MASKING not among them |
| C3 | RTL has msg_mask hardware but hjson+testplan lack declaration | declaration gap | L4→L3 (script proof) | 5 RTL anchors found (g_msg_mask:906, msg_mask_en:552, msg_mask_o:51, msg_mask_en_i, cfg_msg_mask:551); sec_cm_testplan has 14 testpoints, none for MSG.MASKING |

### Why L2 Not Achievable

MSG.MASKING is a countermeasures metadata declaration. Its absence/presence in hjson has no I/O behavioral effect on the KMAC hardware — the masking hardware operates regardless of whether hjson declares it. L2 micro-tb diff requires observable output difference, which declaration gaps cannot produce.

### Fidelity: L3 (script-level proof)

Machine-checkable Python script parses hjson registers + countermeasures + greps RTL hardware anchors + checks sec_cm_testplan. All 3 claims confirmed programmatically.

### Reproduction Commands

```bash
# L3 script proof (exit 1 = confirmed)
python3 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-032/upgrade/prove_vuln032.py

# Via build script
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-032/upgrade/build_upgrade.sh
```

### Script Output (verbatim)

```
--- C1: msg_mask register field in kmac.hjson ---
  msg_mask field: FOUND (line 559)
  bits assignment (20): CONFIRMED
  C1 VERDICT: PASS

--- C2: MSG.MASKING absent from countermeasures list ---
  Countermeasures entries (14):
    1. BUS.INTEGRITY
    2. LC_ESCALATE_EN.INTERSIG.MUBI
    3. SW_KEY.KEY.MASKING
    4. KEY.SIDELOAD
    5. CFG_SHADOWED.CONFIG.SHADOW
    6. FSM.SPARSE
    7. CTR.REDUN
    8. PACKER.CTR.REDUN
    9. CFG_SHADOWED.CONFIG.REGWEN
    10. FSM.GLOBAL_ESC
    11. FSM.LOCAL_ESC
    12. LOGIC.INTEGRITY
    13. ABSORBED.CTRL.MUBI
    14. SW_CMD.CTRL.SPARSE
  MSG.MASKING present: False
  C2 VERDICT: PASS (MSG.MASKING absent as claimed)

--- C3: RTL hardware anchors vs hjson/testplan declaration gap ---
  RTL hardware anchors:
    g_msg_mask: True (kmac.sv:906)
    msg_mask_en: True (kmac.sv:552)
    msg_mask_o: True (kmac_entropy.sv:51)
    msg_mask_en_i: True (kmac_entropy.sv:50)
    cfg_msg_mask: True (kmac.sv:551)
  All RTL anchors present: True
  sec_cm_testplan exists: True
  sec_cm_testplan has MSG.MASKING: False
  sec_cm_testplan testpoints: 14
  C3 VERDICT: PASS (RTL has hardware, hjson+testplan lack declaration)

OVERALL: CONFIRMED — All 3 claims proved
```
