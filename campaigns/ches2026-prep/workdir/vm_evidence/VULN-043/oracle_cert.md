# Oracle Certification — VULN-043

Generated: 2026-10-09 18:33 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle**: Lines 16-17 of the vuln file: "A formal analysis using REBECCA (stable and transient mode) shows that this implementation is not secure. It's usage is thus discouraged." — the module itself should guard against its own use with a runtime assertion, not rely solely on a lint-only check in the wrapper.
- Oracle: lines 16-17: "A formal analysis using REBECCA (stable and transient mode) shows that this implementation is not secure."
- Oracle: line 234: "Formally analyzing the implementation with REBECCA reveals that: Fresh random bits are required for r, q and t."

## Evidence Log (excerpt)

```
[Check 1] REBECCA insecurity documented in vuln: YES
         Line 16: // A formal analysis using REBECCA (stable and transient mode) shows that this implementation is
         Line 17: // not secure. It's usage is thus discouraged. It's included here mainly for reference.
         Line 19: // For details on the REBECCA tool, see the following paper:
[Check 2] Proper runtime SVA SecSBoxImpl==SBoxImplDom: NOT FOUND
[Check 3] Inert lint-only checks (ASSERT_STATIC_LINT_ERROR): FOUND
         hw/ip/aes/rtl/aes_cipher_control_fsm.sv:493: `ASSERT_STATIC_LINT_ERROR(AesCipherControlFsmSecSBoxImplNonDefault, SecSBoxImpl == SBoxImplDom)
         hw/ip/aes/rtl/aes_sbox.sv:29: `ASSERT_STATIC_LINT_ERROR(AesSBoxSecSBoxImplNonDefault, SecSBoxImpl == SBoxImplDom)
[Check 4] ASSERT_STATIC_LINT_ERROR is inert (no runtime effect): YES
[Check 5] Twin has ASSERT_INIT(RebeccaInsecureSBox): YES

VERDICT: CONFIRMED — REBECCA-insecure canright_masked SBox has no proper SVA guard
Only ASSERT_STATIC_LINT_ERROR (lint-only, inert in simulation) exists at aes_sbox.sv:29
Twin adds ASSERT_INIT that fires at simulation start when insecure SBox is instantiated
```
