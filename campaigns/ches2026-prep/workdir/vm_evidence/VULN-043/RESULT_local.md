# VULN-043 Result

## Verdict: [poc-success] CONFIRMED

AES `aes_sbox_canright_masked.sv` is documented as REBECCA-insecure (lines 16-17), yet the only protection against its use is `ASSERT_STATIC_LINT_ERROR` which is inert during simulation. No proper runtime SVA `SecSBoxImpl==SBoxImplDom` exists.

## Fidelity: L4 (static conclusion)

Pure oracle comparison — source code grep verification, no dynamic simulation.

## Evidence

### Check 1: REBECCA insecurity documented in vuln
```
$ grep -n 'REBECCA\|not secure' aes_sbox_canright_masked.sv
16: // A formal analysis using REBECCA (stable and transient mode) shows that this implementation is
17: // not secure. It's usage is thus discouraged. It's included here mainly for reference.
```

### Check 2: No proper runtime SVA SecSBoxImpl==SBoxImplDom
```
$ grep -rn 'ASSERT_INIT.*SecSBoxImpl.*SBoxImplDom\|assert property.*SecSBoxImpl.*SBoxImplDom' hw/ip/aes/rtl/
(no match — exit 1)
```

### Check 3: Only inert lint-time checks exist
```
$ grep -rn 'ASSERT_STATIC_LINT_ERROR.*SecSBoxImpl' hw/ip/aes/rtl/
hw/ip/aes/rtl/aes_sbox.sv:29:  `ASSERT_STATIC_LINT_ERROR(AesSBoxSecSBoxImplNonDefault, SecSBoxImpl == SBoxImplDom)
hw/ip/aes/rtl/aes_cipher_control_fsm.sv:493:  `ASSERT_STATIC_LINT_ERROR(AesCipherControlFsmSecSBoxImplNonDefault, SecSBoxImpl == SBoxImplDom)
```

### Check 4: ASSERT_STATIC_LINT_ERROR macro is inert
The macro at `hw/ip/prim/rtl/prim_assert.sv:39-44` expands to:
```systemverilog
`define ASSERT_STATIC_LINT_ERROR(__name, __prop)     \
  localparam int __name = (__prop) ? 1 : 2;          \
  always_comb begin                                  \
    logic unused_assert_static_lint_error;           \
    unused_assert_static_lint_error = __name'(1'b1); \
  end
```
No `$error`, no `assert` statement — complete no-op during simulation. Only triggers lint warning via width mismatch.

### Check 5: Twin adds proper runtime assertion
Twin `aes_sbox_canright_masked_twin.sv` adds:
```systemverilog
`ASSERT_INIT(RebeccaInsecureSBox, 1'b0)
```
This fires at simulation start, catching use of the REBECCA-insecure SBox.

## Reproduction Commands

```bash
# Full verification
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-043/build.sh

# Python PoC (redbud mode)
python3 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-043/exploit.py

# Quick manual checks
grep -n 'REBECCA' /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_sbox_canright_masked.sv
# Lines 16-17: "not secure. It's usage is thus discouraged."

grep -rn 'ASSERT_STATIC_LINT_ERROR.*SecSBoxImpl' /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/
# Only lint-time, inert checks — no runtime SVA
```

## Twin Repair

- **File**: `aes_sbox_canright_masked_twin.sv`
- **Change**: Renamed module to `aes_sbox_canright_masked_twin`. Added `` `include "prim_assert.sv"`` and `` `ASSERT_INIT(RebeccaInsecureSBox, 1'b0)`` inside the module body (after imports).
- **Oracle**: Lines 16-17 of the vuln file: "A formal analysis using REBECCA (stable and transient mode) shows that this implementation is not secure. It's usage is thus discouraged." — the module itself should guard against its own use with a runtime assertion, not rely solely on a lint-only check in the wrapper.
- **Diff**: Module name change + 5 lines added (include + ASSERT_INIT + 3 comment lines explaining the fix)

## Vulnerability Summary

| Aspect | Detail |
|---|---|
| REBECCA finding | Stable and transient mode both show insecurity |
| Documentation | Lines 16-17: "not secure. It's usage is thus discouraged." |
| Current guard | `ASSERT_STATIC_LINT_ERROR` at aes_sbox.sv:29 — lint-only, inert in simulation |
| Missing guard | No `ASSERT_INIT` or `assert property` checking `SecSBoxImpl==SBoxImplDom` |
| Impact | REBECCA-insecure SBox can be used without any runtime warning; mask re-use makes implementation vulnerable to higher-order DPA despite first-order security claim |

## Upgrade (2026-09-23)

### New Verdict: [poc-success] CONFIRMED (upgraded from L4 to L3)

### New Fidelity: L3 (script-level实证)

L4 static conclusion upgraded to L3 via three script proofs:
- Claim A (behavior simulable): SBox functional correctness exhaustively verified
- Claim B (property absence): Mask re-use structural vulnerability proven by RTL comparison
- Claim C (declaration absence): ASSERT_STATIC_LINT_ERROR inertness proven; no runtime SVA guard

L2 (Verilator micro-tb) was not achievable because the REBECCA insecurity is a side-channel
property (higher-order DPA leakage via mask re-use) that cannot be demonstrated by functional
simulation. No behavioral difference between vuln and twin exists at the I/O level — the
vulnerability is structural (intermediate mask derivation) not functional.

### Sub-claim Upgrade Results

| Sub-claim | Category | Upgraded Level | Result | Evidence |
|---|---|---|---|---|
| A: SBox functional correctness | 行为可仿真 | L3 (script) | PASS | 256 fwd + 256 inv + 32768 fwd masked + 32768 inv masked = 65536 tests, all correct vs FIPS-197 |
| B: Mask re-use vulnerability | 属性缺失 | L3 (script) | CONFIRMED | RTL parse: vuln r=m1[3:2], q=n[7:4] (re-used); noreuse r=prd[1:0], q=prd[5:2], t=prd[9:6] (fresh) |
| C: No runtime SVA guard | 声明缺失 | L3 (script) | CONFIRMED | Macro parse: ASSERT_STATIC_LINT_ERROR = localparam + unused signal (no $error/assert); 0 proper runtime SVA found |

### Claim A: SBox Functional Correctness (L3)

The Canright masked SBox is **functionally correct** for all tested cases:
- CIPH_FWD mask=0: all 256 inputs produce correct FIPS-197 SBox output
- CIPH_INV mask=0: all 256 inputs produce correct FIPS-197 inverse SBox output
- CIPH_FWD masked decomposition: 256 × 16 × 8 = 32768 tests — data_o ^ mask_o == sbox(data_i ^ mask_i)
- CIPH_INV masked decomposition: 256 × 16 × 8 = 32768 tests — same property for inverse

This confirms the SBox function is correct. The REBECCA insecurity is a **side-channel** property
(mask re-use creates higher-order DPA leakage), not a functional error.

### Claim B: Mask Re-use Structural Vulnerability (L3)

**VULN** (aes_masked_inverse_gf2p8 in aes_sbox_canright_masked.sv):
- `r = m1[3:2]` — intermediate mask derived from input mask bits (RE-USED)
- `q = n[7:4]` — intermediate mask derived from output mask bits (RE-USED)
- Oracle: lines 16-17: "A formal analysis using REBECCA (stable and transient mode) shows that this implementation is not secure."

**NOREUSE sibling** (aes_masked_inverse_gf2p8_noreuse in aes_sbox_canright_masked_noreuse.sv):
- `r = prd[1:0]` — fresh pseudo-random data (INDEPENDENT)
- `q = prd[5:2]` — fresh pseudo-random data (INDEPENDENT)
- `t = prd[9:6]` — fresh pseudo-random data (INDEPENDENT)
- Oracle: line 234: "Formally analyzing the implementation with REBECCA reveals that: Fresh random bits are required for r, q and t."

The structural difference (mask re-use vs fresh PRD) is the root cause of REBECCA insecurity.

### Claim C: ASSERT_STATIC_LINT_ERROR Inertness (L3)

Macro definition at `hw/ip/prim/rtl/prim_assert.sv:39-44`:
```systemverilog
`define ASSERT_STATIC_LINT_ERROR(__name, __prop)     \
  localparam int __name = (__prop) ? 1 : 2;          \
  always_comb begin                                  \
    logic unused_assert_static_lint_error;           \
    unused_assert_static_lint_error = __name'(1'b1); \
  end
```
- No `$error`, `$fatal`, or `assert` statement — zero runtime effect
- Only mechanism: lint-time width mismatch warning (int vs 1-bit)
- Proper runtime SVA search: 0 ASSERT_INIT, 0 ASSERT_FINAL, 0 concurrent SVA for SecSBoxImpl
- Inert lint-only checks: 2 instances (aes_sbox.sv:29, aes_cipher_control_fsm.sv:493)

### Reproduction Commands

```bash
# Full upgrade verification (exit 1 = confirmed)
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-043/upgrade/build_upgrade.sh

# Individual scripts:
python3 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-043/upgrade/verify_sbox_functional.py
python3 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-043/upgrade/verify_mask_reuse.py
python3 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-043/upgrade/verify_assert_inert.py
```
