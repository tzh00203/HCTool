# VULN-005 Dynamic Verification Result

## Verdict: [poc-success] CONFIRMED (re-characterized)

## Fidelity Level: L1 (execution-level evidence)

## Finding

aes.sv:180 hardcodes `.SecAllowForcingMasks(1)` into `u_aes_core`, discarding the
IP default parameter (0) and making the SW-writable `CTRL_AUX_SHADOWED.FORCE_MASKS`
bit live in every build. The lint error at aes_prng_masking.sv:68
(`AesSecAllowForcingMasksNonDefault`) fires by construction.

**Re-characterization**: The hardcode does NOT by itself freeze the masking PRNG.
Writing `FORCE_MASKS=1` while the PRNG is operating normally does NOT produce
constant masks (T1: 16/16 mask changes observed). Constant masks additionally
require an all-zero reseed of the 177-bit Bivium state (attacker-influenced
entropy or SCA bench infrastructure). With that combination, the forced build
locks at `mask=0` (unmasked) while the default build auto-restores
(`StrictLockupProtection`). Clearing the bit revives the PRNG (T3).

**Revised severity**: Medium (configuration hardening, live SCA-eval gate),
not Critical. The hardcode is a security misconfiguration that makes a
dangerous kill path reachable, but it requires additional attacker-controlled
entropy to exploit.

## Complete Reproduction Command

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-005
bash build_force_masks.sh
```

## Raw Output

```
T1 forced build, FORCE_MASKS=1, live operation:       mask changes=16/16
T2 forced build, FORCE_MASKS=1 + zero-entropy reseed: masks stuck at 0: yes
T2 default build, same stimulus:                      masks recovered: yes
T3 forced build, FORCE_MASKS cleared:                 masks recovered: yes
CONFIRMED: aes.sv:180 hardcodes SecAllowForcingMasks(1), making the
SW FORCE_MASKS bit live in the default build (top_earlgrey default 1'b0 discarded;
aes_prng_masking.sv:68 lint error fires by construction). BUT the bit does NOT by
itself block the PRNG - masks keep advancing under FORCE_MASKS=1 (T1), so the claimed
one-register-write masking kill is refuted. Constant masks additionally require an
all-zero reseed of the 177-bit Bivium state (attacker-influenced entropy or an SCA
bench): then the forced build locks at mask=0 (unmasked) while the default build
auto-restores (T2); clearing the bit revives the PRNG (T3). Severity: Medium
(configuration hardening, live SCA-eval gate), not High.
exit code: 1 (1 = finding confirmed)
```

## Twin Repair Diff Summary

- File: `aes.sv` → `aes_twin.sv`
- Line 180: `.SecAllowForcingMasks(1)` → `.SecAllowForcingMasks(SecAllowForcingMasks)`
- Repair basis: aes_prng_masking.sv:68 lint error `AesSecAllowForcingMasksNonDefault`
  asserts `SecAllowForcingMasks == 0` (the secure default). The IP-level parameter
  default in aes.sv is also 0. The hardcode discards both.

## Test Details

- TB type: sequential (negedge FSM) — behavioral verification at aes_prng_masking leaf
- DUT: `aes_prng_masking` instantiated with SecAllowForcingMasks=1 (vuln) vs =0 (twin)
- Three test phases:
  - T1: Normal operation under FORCE_MASKS=1 — PRNG keeps advancing (refutes "one write kills masking")
  - T2: All-zero entropy reseed + FORCE_MASKS=1 — forced build locks at mask=0, default build auto-restores
  - T3: Clear FORCE_MASKS bit — forced build recovers (effect is reversible)
- Success criteria: T1 changed AND T2 forced-zero-stuck AND T2 defauhct-recovered AND T3 recovers
