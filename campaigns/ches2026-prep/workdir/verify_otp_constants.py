#!/usr/bin/env python3
"""
Verify all obfuscated constants in OpenTitan otp_ctrl package files.
L5 (constant folding) lens: NEVER do mental arithmetic on obfuscated constants.
"""

import sys

# ==============================================================================
# 1. lc_ctrl_state_pkg.sv: A/B values for life cycle state encoding
# ==============================================================================

A = {
    0:  0b0110010010101110,
    1:  0b0000011110110100,
    2:  0b0011000111010010,
    3:  0b0010111001001101,
    4:  0b0100000111111000,
    5:  0b1010110010000101,
    6:  0b1001100110001100,
    7:  0b0101001100001111,
    8:  0b0111000101100000,
    9:  0b0010110001100011,
    10: 0b0110110100001000,
    11: 0b1001001001001100,
    12: 0b0111000001000000,
    13: 0b1001001010111110,
    14: 0b1001010011010010,
    15: 0b0110001010001101,
    16: 0b1011001000101000,
    17: 0b0001111001110001,
    18: 0b0010110110011011,
    19: 0b0100110110001100,
}

B = {
    0:  0b0111010111101110,
    1:  0b0000111111111110,
    2:  0b0111101111111110,
    3:  0b0011111101101111,
    4:  0b0101111111111100,
    5:  0b1111110110011111,
    6:  0b1111100110011111,
    7:  0b1101101101101111,
    8:  0b0111001101111111,
    9:  0b0110110001101111,
    10: 0b0110111110011110,
    11: 0b1101001111011100,
    12: 0b0111011101010010,
    13: 0b1111001011111110,
    14: 0b1011110111010011,
    15: 0b0110111111001101,
    16: 0b1011001011111011,
    17: 0b1001111111110101,
    18: 0b0011111111011111,
    19: 0b1101110110111110,
}

ZRO = 0
LC_STATE_WIDTH = 320  # 20 * 16

def concat_16bit(parts):
    """Concatenate 16-bit values, MSB first."""
    result = 0
    for val in parts:
        result = (result << 16) | val
    return result

# ==============================================================================
# Compute LcStTestUnlocked0 and LcStRma
# ==============================================================================

LcStTestUnlocked0 = concat_16bit([
    A[19], A[18], A[17], A[16], A[15], A[14], A[13], A[12], A[11], A[10],
    A[9],  A[8],  A[7],  A[6],  A[5],  A[4],  A[3],  A[2],  A[1],  B[0]
])

LcStRma = concat_16bit([
    B[19], B[18], A[17], B[16], B[15], B[14], B[13], B[12], B[11], B[10],
    B[9],  B[8],  B[7],  B[6],  B[5],  B[4],  B[3],  B[2],  B[1],  B[0]
])

# ==============================================================================
# Evaluate obfuscated constant expressions
# ==============================================================================

print("=" * 80)
print("VERIFICATION OF OBFUSCATED CONSTANTS IN OpenTitan OTP_CTRL")
print("=" * 80)

issues_found = []

def check(name, computed, expected, description=""):
    match = computed == expected
    status = "PASS" if match else "*** FAIL ***"
    msg = f"  {name}: computed={computed}, expected={expected} -> {status}"
    if description:
        msg += f"  ({description})"
    print(msg)
    if not match:
        issues_found.append(f"{name}: computed={computed}, expected={expected}")
    return match

# --- OTP_LC_DATA_DEFAULT.valid ---
# (1'b1 && 1'b1) || (1'b0 && 1'b0) = 1 || 0 = 1
valid_computed = (1 and 1) or (0 and 0)
check("OTP_LC_DATA_DEFAULT.valid", valid_computed, 1)

# --- OTP_LC_DATA_DEFAULT.error ---
# (2'b01 != 2'b01) = false = 0
error_computed = 1 if (0b01 != 0b01) else 0
check("OTP_LC_DATA_DEFAULT.error", error_computed, 0)

# --- OTP_LC_DATA_DEFAULT.state (CRITICAL) ---
# LcStTestUnlocked0 | (LcStRma & {8{(&1'b1)}})
# (&1'b1) = 1, {8{1'b1}} = 0xFF (8 bits), zero-extended to 320 bits for bitwise AND
mask_8bit = 0xFF
rma_masked = LcStRma & mask_8bit
state_computed = LcStTestUnlocked0 | rma_masked

print()
print("  --- CRITICAL: OTP_LC_DATA_DEFAULT.state ---")
print(f"  LcStTestUnlocked0 = 0x{LcStTestUnlocked0:080x}")
print(f"  LcStRma            = 0x{LcStRma:080x}")
print(f"  {{8{{1'b1}}}} mask (zero-ext 320b) = 0x{mask_8bit:080x}")
print(f"  LcStRma & mask     = 0x{rma_masked:080x}")
print(f"  state_computed     = 0x{state_computed:080x}")
print(f"  Equal to LcStTestUnlocked0? {state_computed == LcStTestUnlocked0}")

diff = state_computed ^ LcStTestUnlocked0
if diff != 0:
    diff_bits = [i for i in range(LC_STATE_WIDTH) if diff & (1 << i)]
    print(f"  CHANGED BITS: {diff_bits}")
    print(f"  XOR difference: 0x{diff:080x}")
else:
    print(f"  No bits changed by the OR operation.")

# Bottom-8-bit analysis
b0_low8 = B[0] & 0xFF
testunlocked0_low8 = LcStTestUnlocked0 & 0xFF
rma_low8 = LcStRma & 0xFF
print(f"\n  Bottom 8 bits of B0:                0x{b0_low8:02x}")
print(f"  Bottom 8 bits of LcStTestUnlocked0: 0x{testunlocked0_low8:02x}")
print(f"  Bottom 8 bits of LcStRma:           0x{rma_low8:02x}")
print(f"  Are they the same? {testunlocked0_low8 == rma_low8}")

state_match = check("OTP_LC_DATA_DEFAULT.state",
                     state_computed, LcStTestUnlocked0,
                     "Should equal LcStTestUnlocked0")

# What if the mask were FULL width?
full_mask = (1 << LC_STATE_WIDTH) - 1
rma_full_masked = LcStRma & full_mask
state_if_full_mask = LcStTestUnlocked0 | rma_full_masked
print(f"\n  What if mask were full-width ({{320{{1'b1}}}})?")
print(f"  state would be = 0x{state_if_full_mask:080x}")
print(f"  Equals LcStTestUnlocked0? {state_if_full_mask == LcStTestUnlocked0}")
if state_if_full_mask != LcStTestUnlocked0:
    diff_full = state_if_full_mask ^ LcStTestUnlocked0
    n_changed = bin(diff_full).count('1')
    print(f"  Bits that would change: {n_changed}")
    print(f"  *** OBFUSCATION PATTERN: Using {{8{{...}}}} instead of full-width mask")
    print(f"  *** makes the expression evaluate correctly ONLY because the mask is narrow.")
    print(f"  *** With a full mask, {n_changed} bits would be ORed in from LcStRma.")

# Verify computed state matches a known valid LC state
lc_states = {}
lc_states['LcStRaw'] = concat_16bit([ZRO]*20)
lc_states['LcStTestUnlocked0'] = LcStTestUnlocked0
lc_states['LcStTestLocked0'] = concat_16bit([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],A[5],A[4],A[3],A[2],B[1],B[0]])
lc_states['LcStTestUnlocked1'] = concat_16bit([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],A[5],A[4],A[3],B[2],B[1],B[0]])
lc_states['LcStTestLocked1'] = concat_16bit([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],A[5],A[4],B[3],B[2],B[1],B[0]])
lc_states['LcStTestUnlocked2'] = concat_16bit([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],A[5],B[4],B[3],B[2],B[1],B[0]])
lc_states['LcStTestLocked2'] = concat_16bit([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],B[5],B[4],B[3],B[2],B[1],B[0]])
lc_states['LcStTestUnlocked3'] = concat_16bit([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
lc_states['LcStTestLocked3'] = concat_16bit([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
lc_states['LcStTestUnlocked4'] = concat_16bit([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
lc_states['LcStTestLocked4'] = concat_16bit([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
lc_states['LcStTestUnlocked5'] = concat_16bit([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
lc_states['LcStTestLocked5'] = concat_16bit([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
lc_states['LcStTestUnlocked6'] = concat_16bit([A[19],A[18],A[17],A[16],A[15],A[14],A[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
lc_states['LcStTestLocked6'] = concat_16bit([A[19],A[18],A[17],A[16],A[15],A[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
lc_states['LcStTestUnlocked7'] = concat_16bit([A[19],A[18],A[17],A[16],A[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
lc_states['LcStDev'] = concat_16bit([A[19],A[18],A[17],A[16],B[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
lc_states['LcStProd'] = concat_16bit([A[19],A[18],A[17],B[16],A[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
lc_states['LcStProdEnd'] = concat_16bit([A[19],A[18],B[17],A[16],A[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
lc_states['LcStRma'] = LcStRma
lc_states['LcStScrap'] = concat_16bit([B[19],B[18],B[17],B[16],B[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])

matched_state = None
for name, val in lc_states.items():
    if state_computed == val:
        matched_state = name
        break

print(f"\n  Computed state matches: {matched_state if matched_state else 'NO VALID STATE (INVALID!)'}")
if matched_state != 'LcStTestUnlocked0':
    issues_found.append(f"OTP_LC_DATA_DEFAULT.state resolves to {matched_state}, not LcStTestUnlocked0!")

matched_full = None
for name, val in lc_states.items():
    if state_if_full_mask == val:
        matched_full = name
        break
print(f"  Full-mask state would match: {matched_full if matched_full else 'NO VALID STATE (would be INVALID!)'}")

# --- FLASH_OTP_KEY_RSP_DEFAULT.data_ack ---
# (~(|4'h0)) || (&(~4'hF))
# |4'h0 = 0, ~0 = 1; ~4'hF = 0x0, &(0x0) = 0; 1 || 0 = 1
red_or_0 = 0  # |4'h0
not_red_or = 1 if red_or_0 == 0 else 0  # ~(|4'h0) = ~0 = 1
not_f = (~0xF) & 0xF  # ~4'hF in 4-bit = 0
red_and_not_f = 1 if not_f == 0xF else 0  # &(~4'hF) = 0
data_ack_computed = not_red_or | red_and_not_f
check("FLASH_OTP_KEY_RSP_DEFAULT.data_ack", data_ack_computed, 1)

# --- FLASH_OTP_KEY_RSP_DEFAULT.addr_ack ---
# ((1'b1 << 1) >> 1) !== 1'b0  =>  (2 >> 1) != 0  =>  1 != 0  =>  1
addr_ack_shift = (1 << 1) >> 1  # = 1
addr_ack_computed = 1 if addr_ack_shift != 0 else 0
check("FLASH_OTP_KEY_RSP_DEFAULT.addr_ack", addr_ack_computed, 1)

# --- FLASH_OTP_KEY_RSP_DEFAULT.seed_valid ---
# (|(~0)) && (!(&0))  =>  1 && 1  =>  1
seed_valid_p1 = 1  # |(~0) = |(all 1s) = 1
seed_valid_p2 = 1  # !(&0) = !(0) = 1
seed_valid_computed = seed_valid_p1 & seed_valid_p2
check("FLASH_OTP_KEY_RSP_DEFAULT.seed_valid", seed_valid_computed, 1)

# ==============================================================================
# 2. RndCnst values in otp_ctrl_part_pkg.sv
# ==============================================================================
print()
print("=" * 80)
print("RndCnst CONSTANTS IN otp_ctrl_part_pkg.sv")
print("=" * 80)

RndCnstKey = [
    0x85A9E830BC059BA9286D6E2856A05CC3,
    0xEFFA6D736C5EFF49AE7B70F9C46E5A62,
    0x3BA121C5E097DDEB7768B4C666E9C3DA,
]

RndCnstDigestConst = [
    0x4A22D4B78FE0266FBEE3958332F2939B,
    0xD60822E1FAEC5C7290C7F21F6224F027,
    0x277195FC471E4B26B6641214B61D1B43,
    0xE95F517CB98955B4D5A89AA9109294A,  # NOTE: only 31 hex digits = 124 bits
]

RndCnstDigestIV = [
    0xF98C48B1F9377284,
    0xB7474D640F8A7F5,    # NOTE: only 15 hex digits = 60 bits
    0xE048B657396B4B83,
    0xBEAD91D5FA4E0915,
]

def hamming_weight(n):
    return bin(n).count('1')

def check_const(name, val, expected_width):
    actual_width = val.bit_length()
    hw = hamming_weight(val)
    anomalies = []
    if actual_width > expected_width:
        anomalies.append(f"EXCEEDS {expected_width}-bit width ({actual_width} bits)")
    if val == 0:
        anomalies.append("ALL ZEROS - suspicious for a random constant")
    if val == (1 << expected_width) - 1:
        anomalies.append("ALL ONES - suspicious for a random constant")
    expected_hw = expected_width / 2
    std_dev = (expected_width * 0.25) ** 0.5
    sigma = abs(hw - expected_hw) / std_dev
    if sigma > 4:
        anomalies.append(f"Hamming weight {hw} is {sigma:.1f} sigma from expected (suspicious)")

    hex_width = expected_width // 4
    status = "OK" if not anomalies else "ANOMALY: " + "; ".join(anomalies)
    print(f"  {name}: 0x{val:0{hex_width}x}  width={actual_width}  HW={hw}  {status}")
    if anomalies:
        issues_found.append(f"{name}: {'; '.join(anomalies)}")
    return anomalies

print("\n  RndCnstKey (3 x 128-bit):")
for i, val in enumerate(RndCnstKey):
    check_const(f"RndCnstKey[{i}]", val, 128)

print("\n  RndCnstDigestConst (4 x 128-bit):")
for i, val in enumerate(RndCnstDigestConst):
    check_const(f"RndCnstDigestConst[{i}]", val, 128)

print("\n  RndCnstDigestIV (4 x 64-bit):")
for i, val in enumerate(RndCnstDigestIV):
    check_const(f"RndCnstDigestIV[{i}]", val, 64)

# ==============================================================================
# 3. RndCnst values in otp_ctrl_top_specific_pkg.sv
# ==============================================================================
print()
print("=" * 80)
print("RndCnst CONSTANTS IN otp_ctrl_top_specific_pkg.sv")
print("=" * 80)

RndCnstLfsrSeedDefault = 0x453d28ea98
RndCnstLfsrPermDefault = 0x4235171482c225f79289b32181a0163a760355d3447063d16661e44c12a5
RndCnstScrmblKeyInitDefault = 0xcebeb96ffe0eced795f8b2cfe23c1e519e4fa08047a6bcfb811b04f0a479006e

print(f"\n  RndCnstLfsrSeedDefault:")
print(f"    Value: 0x{RndCnstLfsrSeedDefault:010x}")
print(f"    Bit width: {RndCnstLfsrSeedDefault.bit_length()} (expected 40)")
print(f"    Hamming weight: {hamming_weight(RndCnstLfsrSeedDefault)}")
if RndCnstLfsrSeedDefault.bit_length() > 40:
    issues_found.append("RndCnstLfsrSeedDefault: exceeds 40-bit width")

print(f"\n  RndCnstLfsrPermDefault:")
print(f"    Value: 0x{RndCnstLfsrPermDefault:060x}")
print(f"    Bit width: {RndCnstLfsrPermDefault.bit_length()} (expected 240)")
print(f"    Hamming weight: {hamming_weight(RndCnstLfsrPermDefault)}")
if RndCnstLfsrPermDefault.bit_length() > 240:
    issues_found.append("RndCnstLfsrPermDefault: exceeds 240-bit width")

print(f"\n  RndCnstScrmblKeyInitDefault:")
print(f"    Value: 0x{RndCnstScrmblKeyInitDefault:064x}")
print(f"    Bit width: {RndCnstScrmblKeyInitDefault.bit_length()} (expected 256)")
print(f"    Hamming weight: {hamming_weight(RndCnstScrmblKeyInitDefault)}")
if RndCnstScrmblKeyInitDefault.bit_length() > 256:
    issues_found.append("RndCnstScrmblKeyInitDefault: exceeds 256-bit width")

# ==============================================================================
# 4. Structural analysis of the state expression
# ==============================================================================
print()
print("=" * 80)
print("STRUCTURAL ANALYSIS OF THE STATE EXPRESSION")
print("=" * 80)

rma_xor_testunlocked = LcStRma ^ LcStTestUnlocked0
n_differing_bits = bin(rma_xor_testunlocked).count('1')
print(f"  LcStRma and LcStTestUnlocked0 differ in {n_differing_bits} bits out of {LC_STATE_WIDTH}")
print(f"  XOR of bottom 8 bits: 0x{rma_xor_testunlocked & 0xFF:02x}")

print(f"\n  Per-chunk (16-bit) analysis of XOR:")
for chunk_idx in range(20):
    chunk_val = (rma_xor_testunlocked >> (chunk_idx * 16)) & 0xFFFF
    bit_pos = chunk_idx * 16
    if chunk_val != 0:
        print(f"    Chunk {chunk_idx:2d} (bits {bit_pos:3d}-{bit_pos+15:3d}): 0x{chunk_val:04x}  HW={hamming_weight(chunk_val)}  *** DIFFERS ***")
    else:
        print(f"    Chunk {chunk_idx:2d} (bits {bit_pos:3d}-{bit_pos+15:3d}): 0x0000  (same)")

# ==============================================================================
# 5. Check if any RndCnst values look like they were tampered with
#    (e.g., all zero, all ones, or simple patterns)
# ==============================================================================
print()
print("=" * 80)
print("TAMPERING PATTERN CHECKS ON RndCnst VALUES")
print("=" * 80)

all_rndcnst = {
    'RndCnstKey[0]': (RndCnstKey[0], 128),
    'RndCnstKey[1]': (RndCnstKey[1], 128),
    'RndCnstKey[2]': (RndCnstKey[2], 128),
    'RndCnstDigestConst[0]': (RndCnstDigestConst[0], 128),
    'RndCnstDigestConst[1]': (RndCnstDigestConst[1], 128),
    'RndCnstDigestConst[2]': (RndCnstDigestConst[2], 128),
    'RndCnstDigestConst[3]': (RndCnstDigestConst[3], 128),
    'RndCnstDigestIV[0]': (RndCnstDigestIV[0], 64),
    'RndCnstDigestIV[1]': (RndCnstDigestIV[1], 64),
    'RndCnstDigestIV[2]': (RndCnstDigestIV[2], 64),
    'RndCnstDigestIV[3]': (RndCnstDigestIV[3], 64),
    'RndCnstLfsrSeedDefault': (RndCnstLfsrSeedDefault, 40),
    'RndCnstLfsrPermDefault': (RndCnstLfsrPermDefault, 240),
    'RndCnstScrmblKeyInitDefault': (RndCnstScrmblKeyInitDefault, 256),
}

# Check for pairwise equality (duplicates would be suspicious)
print("\n  Pairwise duplicate check:")
names = list(all_rndcnst.keys())
for i in range(len(names)):
    for j in range(i+1, len(names)):
        if all_rndcnst[names[i]][0] == all_rndcnst[names[j]][0]:
            msg = f"  *** DUPLICATE: {names[i]} == {names[j]}"
            print(msg)
            issues_found.append(msg)

# Check for simple arithmetic patterns
print("\n  Simple pattern check (powers of 2, etc.):")
for name, (val, width) in all_rndcnst.items():
    # Power of 2?
    if val > 0 and (val & (val - 1)) == 0:
        msg = f"  *** {name} is a power of 2 (suspicious)"
        print(msg)
        issues_found.append(msg)
    # All same nibble?
    hex_width = width // 4
    hex_str = f"{val:0{hex_width}x}"
    if len(set(hex_str)) == 1 and val != 0:
        msg = f"  *** {name} has all same hex digits (suspicious)"
        print(msg)
        issues_found.append(msg)

# ==============================================================================
# SUMMARY
# ==============================================================================
print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)

if issues_found:
    print(f"\n  *** {len(issues_found)} ISSUE(S) FOUND ***\n")
    for issue in issues_found:
        print(f"    - {issue}")
else:
    print("\n  All checks PASSED. No anomalies detected.")

print()
print("  Key findings:")
print(f"  1. OTP_LC_DATA_DEFAULT.state: LcStTestUnlocked0 | (LcStRma & {{8{{1'b1}}}})")
print(f"     evaluates to LcStTestUnlocked0 because the 8-bit mask only affects bits 0-7,")
print(f"     which are identical in both states (both end with B0 = 0x{B[0]:04x}).")
if state_computed == LcStTestUnlocked0:
    print(f"  2. The OR does NOT change the state value. No vulnerability from value change.")
    print(f"     However, the obfuscation is structurally suspicious: the OR-with-Rma")
    print(f"     pattern is unnecessary and makes code review harder.")
else:
    print(f"  2. *** VULNERABILITY: The OR CHANGES the state value! ***")
    print(f"     This is an obfuscated-constant-mismatch (OT-017/018 type).")
print(f"  3. If the mask were full-width, {n_differing_bits} bits from LcStRma")
print(f"     would be ORed in, producing an INVALID state encoding.")
print(f"  4. All other obfuscated boolean expressions evaluate to their expected values.")

sys.exit(1 if issues_found else 0)
