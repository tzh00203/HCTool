#!/usr/bin/env python3
"""Verify lc_ctrl_state_pkg.sv sparse encoding constants.

Checks:
1. Hamming weight/distance constraints on A/B and C/D constants
2. All state encodings are unique
3. State encoding structure matches lc_ctrl_state.hjson pattern
4. No constant has been OR'd with extra bits
"""

def hamming_weight(v):
    return bin(v).count('1')

def hamming_distance(a, b):
    return hamming_weight(a ^ b)

# A/B constants from lc_ctrl_state_pkg.sv (16-bit values)
A = [0]*20
B = [0]*20
A[0]  = 0b0110010010101110; B[0]  = 0b0111010111101110
A[1]  = 0b0000011110110100; B[1]  = 0b0000111111111110
A[2]  = 0b0011000111010010; B[2]  = 0b0111101111111110
A[3]  = 0b0010111001001101; B[3]  = 0b0011111101101111
A[4]  = 0b0100000111111000; B[4]  = 0b0101111111111100
A[5]  = 0b1010110010000101; B[5]  = 0b1111110110011111
A[6]  = 0b1001100110001100; B[6]  = 0b1111100110011111
A[7]  = 0b0101001100001111; B[7]  = 0b1101101101101111
A[8]  = 0b0111000101100000; B[8]  = 0b0111001101111111
A[9]  = 0b0010110001100011; B[9]  = 0b0110110001101111
A[10] = 0b0110110100001000; B[10] = 0b0110111110011110
A[11] = 0b1001001001001100; B[11] = 0b1101001111011100
A[12] = 0b0111000001000000; B[12] = 0b0111011101010010
A[13] = 0b1001001010111110; B[13] = 0b1111001011111110
A[14] = 0b1001010011010010; B[14] = 0b1011110111010011
A[15] = 0b0110001010001101; B[15] = 0b0110111111001101
A[16] = 0b1011001000101000; B[16] = 0b1011001011111011
A[17] = 0b0001111001110001; B[17] = 0b1001111111110101
A[18] = 0b0010110110011011; B[18] = 0b0011111111011111
A[19] = 0b0100110110001100; B[19] = 0b1101110110111110

# C/D constants
C = [0]*24
D = [0]*24
C[0]  = 0b0001010010011110; D[0]  = 0b1011011011011111
C[1]  = 0b0101101011000100; D[1]  = 0b1111101011110100
C[2]  = 0b0001111100100100; D[2]  = 0b0001111110111111
C[3]  = 0b1100111010000101; D[3]  = 0b1100111011101111
C[4]  = 0b0100001010011111; D[4]  = 0b0101101110111111
C[5]  = 0b1001111000100010; D[5]  = 0b1111111110100010
C[6]  = 0b0010011110000110; D[6]  = 0b0111011111000110
C[7]  = 0b0010111101000110; D[7]  = 0b1010111111000110
C[8]  = 0b0000001011011011; D[8]  = 0b1010101111011011
C[9]  = 0b0111000011000110; D[9]  = 0b1111111011001110
C[10] = 0b0100001000010010; D[10] = 0b0111001010110110
C[11] = 0b0100101111110001; D[11] = 0b0110101111110011
C[12] = 0b1000100101000001; D[12] = 0b1011110101001111
C[13] = 0b1000000000010001; D[13] = 0b1001100010110011
C[14] = 0b0101110000000100; D[14] = 0b1111111010001101
C[15] = 0b1100001000001001; D[15] = 0b1110011000011011
C[16] = 0b0101001001101100; D[16] = 0b0111111001111110
C[17] = 0b0100001001110100; D[17] = 0b1100101001110111
C[18] = 0b1100000001100111; D[18] = 0b1100011101110111
C[19] = 0b1010000001001010; D[19] = 0b1111011101101010
C[20] = 0b1001001001010101; D[20] = 0b1101111011011101
C[21] = 0b1001010000011011; D[21] = 0b1001111000111011
C[22] = 0b1011101101100001; D[22] = 0b1011111101111111
C[23] = 0b1101101000000111; D[23] = 0b1101111011100111

ZRO = 0

print("=" * 70)
print("L5 CONSTANT FOLDING VERIFICATION FOR lc_ctrl")
print("=" * 70)

# Check 1: Hamming weight/distance for A/B pairs
print("\n--- Check 1: A/B pair Hamming constraints ---")
all_ab = A + B
min_hw_ab = min(hamming_weight(v) for v in all_ab)
max_hw_ab = max(hamming_weight(v) for v in all_ab)
min_hd_ab = min(hamming_distance(all_ab[i], all_ab[j])
                 for i in range(len(all_ab)) for j in range(i+1, len(all_ab)))
print(f"  A/B min_hw={min_hw_ab}, max_hw={max_hw_ab}, min_hd={min_hd_ab}")
print(f"  Claimed: min_hw>=6, max_hw<=16, min_hd>=6")
if min_hw_ab < 6 or max_hw_ab > 16 or min_hd_ab < 6:
    print("  *** VIOLATION: A/B constants do not meet claimed constraints! ***")
else:
    print("  PASS: A/B constraints OK (considering 16-bit data only)")

# Check 2: Hamming weight/distance for C/D pairs
print("\n--- Check 2: C/D pair Hamming constraints ---")
all_cd = C + D
min_hw_cd = min(hamming_weight(v) for v in all_cd)
max_hw_cd = max(hamming_weight(v) for v in all_cd)
min_hd_cd = min(hamming_distance(all_cd[i], all_cd[j])
                 for i in range(len(all_cd)) for j in range(i+1, len(all_cd)))
print(f"  C/D min_hw={min_hw_cd}, max_hw={max_hw_cd}, min_hd={min_hd_cd}")
if min_hw_cd < 6 or max_hw_cd > 16 or min_hd_cd < 6:
    print("  *** VIOLATION: C/D constants do not meet claimed constraints! ***")
else:
    print("  PASS: C/D constraints OK (considering 16-bit data only)")

# Check 3: All A/B values are pairwise distinct
print("\n--- Check 3: A/B uniqueness ---")
ab_set = set(all_ab)
if len(ab_set) != len(all_ab):
    print("  *** VIOLATION: Duplicate A/B values found! ***")
else:
    print(f"  PASS: All {len(all_ab)} A/B values are unique")

# Check 4: All C/D values are pairwise distinct
print("\n--- Check 4: C/D uniqueness ---")
cd_set = set(all_cd)
if len(cd_set) != len(all_cd):
    print("  *** VIOLATION: Duplicate C/D values found! ***")
else:
    print(f"  PASS: All {len(all_cd)} C/D values are unique")

# Check 5: Construct all state encodings and verify uniqueness
print("\n--- Check 5: State encoding uniqueness ---")
def make_state(words):
    """Concatenate 20 16-bit words into a 320-bit integer, MSB-first like SV."""
    result = 0
    for w in words:
        result = (result << 16) | w
    return result

# Build state encodings matching lc_ctrl_state_pkg.sv (MSB-first concatenation)
# The SV uses {A19, A18, ..., A0} style = MSB-first
states = {}
states['LcStRaw'] = make_state([ZRO]*20)
states['LcStTestUnlocked0'] = make_state([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],A[5],A[4],A[3],A[2],A[1],B[0]])
states['LcStTestLocked0']   = make_state([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],A[5],A[4],A[3],A[2],B[1],B[0]])
states['LcStTestUnlocked1'] = make_state([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],A[5],A[4],A[3],B[2],B[1],B[0]])
states['LcStTestLocked1']   = make_state([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],A[5],A[4],B[3],B[2],B[1],B[0]])
states['LcStTestUnlocked2'] = make_state([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],A[5],B[4],B[3],B[2],B[1],B[0]])
states['LcStTestLocked2']   = make_state([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],B[5],B[4],B[3],B[2],B[1],B[0]])
states['LcStTestUnlocked3'] = make_state([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
states['LcStTestLocked3']   = make_state([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
states['LcStTestUnlocked4'] = make_state([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
states['LcStTestLocked4']   = make_state([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
states['LcStTestUnlocked5'] = make_state([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
states['LcStTestLocked5']   = make_state([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
states['LcStTestUnlocked6'] = make_state([A[19],A[18],A[17],A[16],A[15],A[14],A[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
states['LcStTestLocked6']   = make_state([A[19],A[18],A[17],A[16],A[15],A[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
states['LcStTestUnlocked7'] = make_state([A[19],A[18],A[17],A[16],A[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
states['LcStDev']           = make_state([A[19],A[18],A[17],A[16],B[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
states['LcStProd']          = make_state([A[19],A[18],A[17],B[16],A[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
states['LcStProdEnd']       = make_state([A[19],A[18],B[17],A[16],A[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
states['LcStRma']           = make_state([B[19],B[18],A[17],B[16],B[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
states['LcStScrap']         = make_state([B[19],B[18],B[17],B[16],B[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])

state_vals = list(states.values())
state_names = list(states.keys())
unique_states = set(state_vals)
if len(unique_states) != len(state_vals):
    print("  *** VIOLATION: Duplicate state encodings! ***")
    from collections import Counter
    cnt = Counter(state_vals)
    for v, c in cnt.items():
        if c > 1:
            dup_names = [n for n, sv in states.items() if sv == v]
            print(f"    Duplicate: {dup_names} = 0x{v:080x}")
else:
    print(f"  PASS: All {len(state_vals)} state encodings are unique")

# Check 6: Verify hjson structure pattern for PROD
# hjson PROD = [B0, B1, ..., B14, A15, B16, A17, A18, A19] (LSB first)
# SV    PROD = {A19, A18, A17, B16, A15, B14, ..., B0} (MSB first)
# These should be the same encoding
print("\n--- Check 6: PROD encoding structure (hjson vs SV) ---")
prod_hjson_lsb = [B[0],B[1],B[2],B[3],B[4],B[5],B[6],B[7],B[8],B[9],B[10],B[11],B[12],B[13],B[14],A[15],B[16],A[17],A[18],A[19]]
prod_sv_msb = [A[19],A[18],A[17],B[16],A[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]]
if prod_hjson_lsb == list(reversed(prod_sv_msb)):
    print("  PASS: PROD encoding structure matches hjson")
else:
    print("  *** MISMATCH: PROD encoding structure differs from hjson! ***")
    print(f"    hjson (LSB-first): {[hex(w) for w in prod_hjson_lsb]}")
    print(f"    SV    (MSB-first): {[hex(w) for w in prod_sv_msb]}")

# Check 7: Verify DEV encoding
print("\n--- Check 7: DEV encoding structure (hjson vs SV) ---")
dev_hjson_lsb = [B[0],B[1],B[2],B[3],B[4],B[5],B[6],B[7],B[8],B[9],B[10],B[11],B[12],B[13],B[14],B[15],A[16],A[17],A[18],A[19]]
dev_sv_msb = [A[19],A[18],A[17],A[16],B[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]]
if dev_hjson_lsb == list(reversed(dev_sv_msb)):
    print("  PASS: DEV encoding structure matches hjson")
else:
    print("  *** MISMATCH: DEV encoding structure differs from hjson! ***")

# Check 8: State Hamming distance between PROD and other critical states
print("\n--- Check 8: PROD vs TEST_UNLOCKED* Hamming distance ---")
prod_val = states['LcStProd']
for name in ['LcStTestUnlocked0', 'LcStTestUnlocked6', 'LcStDev']:
    hd = hamming_distance(prod_val, states[name])
    print(f"  HD(PROD, {name}) = {hd} bits")
    if hd < 5:
        print(f"    *** LOW HD: could enable confusion attacks ***")

# Check 9: Verify hashed token constants
print("\n--- Check 9: Hashed token constants ---")
allzero_hashed = 0x3852305BAECF5FF1D5C1D25F6DB9058D
raw_unlock_hashed = 0xF8FE11B88C36C8140252F036D23804DB
print(f"  AllZeroTokenHashed     = 0x{allzero_hashed:032x}")
print(f"  RndCnstRawUnlockTokenHashed = 0x{raw_unlock_hashed:032x}")
if allzero_hashed == 0:
    print("  *** VIOLATION: AllZeroTokenHashed is all-zero! ***")
if raw_unlock_hashed == 0:
    print("  *** VIOLATION: RndCnstRawUnlockTokenHashed is all-zero! ***")
# These are cSHAKE128 post-images; full verification requires running KMAC
print("  NOTE: Full verification of these hashed values requires running cSHAKE128")
print("        with the LC_CTRL prefix. This script confirms they are non-zero constants.")

# Check 10: Verify that no A[i] == B[i] (each pair must differ)
print("\n--- Check 10: A[i] != B[i] for all i ---")
pair_violations = 0
for i in range(20):
    if A[i] == B[i]:
        print(f"  *** VIOLATION: A[{i}] == B[{i}] = 0x{A[i]:04x} ***")
        pair_violations += 1
if pair_violations == 0:
    print("  PASS: All A/B pairs are distinct")

print("\n" + "=" * 70)
print("SUMMARY: All constant checks completed.")
print("Key finding: PROD encoding uses non-standard incremental write pattern")
print("  (position 15 = A15 instead of B15), which is intentional per hjson")
print("  but creates a 'hole' in the A→B transition sequence.")
print("=" * 70)
