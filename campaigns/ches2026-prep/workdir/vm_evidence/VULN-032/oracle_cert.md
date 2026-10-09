# Oracle Certification — VULN-032

Generated: 2026-10-09 18:32 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle**: `msg_mask` register field (line 559) with desc "Message Masking with PRNG" + VULN-012 confirmed masking hardware exists (g_msg_mask block) + SW_KEY.KEY.MASKING already declared in countermeasures (parallel masking feature)
- SEC_CM declaration

## Evidence Log (excerpt)

```
[Check 1] msg_mask register field: FOUND
[Check 2] MSG.MASKING in vuln countermeasures: NOT FOUND
[Check 3] MSG.MASKING in twin countermeasures: FOUND

VERDICT: CONFIRMED — vuln hjson missing MSG.MASKING SEC_CM declaration
msg_mask register field exists (line 559) but countermeasures list omits MSG.MASKING
```
