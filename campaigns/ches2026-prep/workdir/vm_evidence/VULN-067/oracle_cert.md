# Oracle Certification — VULN-067

Generated: 2026-10-09 18:33 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle: In-tree SVA pattern — 25 active ASSERT/ASSUME in sha3pad.sv establish control-flow contract; commented-out assertions break formal verification guarantee.
- Oracle: kmac_entropy outputs msg_mask (dynamic LFSR) via .msg_mask_o; sibling IPs (AES) use PRD for all masking; SEC_CM: MSG.MASKING documents this feature.
- Oracle: kmac_entropy.msg_mask_o provides dynamic LFSR mask; AES uses PRD for all masking; SEC_CM: MSG.MASKING documents this feature
- Oracle: In-tree SVA pattern — 22 active ASSERT/ASSUME establish control-flow contract
- SEC_CM declaration

## Evidence Log (excerpt)

```
[Part 1] Commented-out SVA in sha3pad.sv: 3 found
  Line 769: ASSUME Sequence_a commented out
  Line 835: ASSERT ProcessToAbsorbed_A commented out
  Line 875: ASSUME NsStableInProcess_A commented out

[Part 2] msg_mask signal dangling in kmac.sv:
  msg_mask_permuted declared: True
  msg_mask_permuted computed: True
  msg_data_masked uses static_mask: True
  static_mask = all-ones: True
  msg_mask from kmac_entropy: True

VERDICT: CONFIRMED — 3 SVA commented out in sha3pad + msg_mask_permuted dangling in kmac (static_mask used instead)
```
