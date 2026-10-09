# VULN-012 Dynamic Verification Result

## Verdict
**[poc-success]** Finding confirmed. L2 fidelity.

## Vulnerability
kmac.sv:906-927 `g_msg_mask` block replaces dynamic LFSR-based `msg_mask` with static constant `static_mask = {MsgWidth{1'b1}}`.

When `EnMasking=1` and `cfg_msg_mask=1` (SW enables message masking), the buggy code:
- Computes `msg_mask_permuted` from `static_mask` (all-ones) instead of `msg_mask` from kmac_entropy LFSR
- XORs message data with `static_mask` directly: `msg_data_masked[i] = msg_data[i] ^ ({MsgWidth{cfg_msg_mask}} & static_mask)`
- Result: message is always XORed with all-ones = bitwise complement (completely deterministic, zero randomness)
- Side-channel masking is defeated entirely — the "mask" provides no statistical independence

The twin fix uses `msg_mask_permuted` (permutation of the LFSR-derived `msg_mask` from kmac_entropy), providing actual random masking as specified by the KMAC IP design.

## Oracle (Twin Repair Basis)
- kmac_entropy module's `msg_mask_o` port drives the `msg_mask` signal
- The original code should permute `msg_mask` through `RndCnstMsgPerm` for DOM-dep masking
- kmac_pkg defines `msg_perm_t` and `RndCnstMsgPermDefault` specifically for this purpose
- The vulnerability comment says "Performance enhancement: Use static mask instead of dynamic LFSR" — this is the exact injection point

## Evidence
```
cfg_msg_mask=1: vuln mask is static all-ones: YES  twin uses dynamic LFSR mask: YES
CONFIRMED: kmac.sv:906-927 g_msg_mask uses static_mask={MsgWidth{1'b1}}
instead of dynamic msg_mask from kmac_entropy LFSR.
With cfg_msg_mask=1, vuln always XORs message with all-ones
(bitwise complement — deterministic, no SCA protection).
Twin uses LFSR-derived msg_mask_permuted (actual random masking).
exit code: 1 (1 = finding confirmed)
```

## Build & Run Command
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-012
bash build.sh
# exit 1 = finding confirmed
```

## Fidelity Level
L2 (data-flow empirical) — combinational micro-tb directly evaluates the masking expressions for vuln vs twin.
