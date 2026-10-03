#!/usr/bin/env python3
"""Correct ECC computation for lc_ctrl_state_pkg.sv with extended Hamming code.

The parity bit (ECC bit 5) covers all data bits AND all other ECC bits.
"""

def hamming_weight(v):
    return bin(v).count('1')

def hamming_distance(a, b):
    return hamming_weight(a ^ b)

def compute_ecc(data16):
    """Compute 6-bit ECC for 16-bit data using extended Hamming code from hjson."""
    # ECC matrix rows 0-4 define which data bits each ECC bit covers
    ecc_matrix = [
        [0, 1, 3, 4, 6, 8, 10, 11, 13, 15],  # ECC bit 0
        [0, 2, 3, 5, 6, 9, 10, 12, 13],       # ECC bit 1
        [1, 2, 3, 7, 8, 9, 10, 14, 15],       # ECC bit 2
        [4, 5, 6, 7, 8, 9, 10],               # ECC bit 3
        [11, 12, 13, 14, 15],                  # ECC bit 4
    ]
    ecc = 0
    ecc_bits = []
    for i, positions in enumerate(ecc_matrix):
        bit = 0
        for p in positions:
            bit ^= (data16 >> p) & 1
        ecc_bits.append(bit)
        ecc |= (bit << i)
    # Parity bit (ECC bit 5) = XOR of all data bits AND all other ECC bits
    parity = 0
    for i in range(16):
        parity ^= (data16 >> i) & 1
    for b in ecc_bits:
        parity ^= b
    ecc |= (parity << 5)
    return ecc

def full_word(data16):
    """Return 22-bit word = data16 | (ecc << 16)."""
    return data16 | (compute_ecc(data16) << 16)

# Constants
A=[0]*20; B=[0]*20
A[0]=0b0110010010101110; B[0]=0b0111010111101110
A[1]=0b0000011110110100; B[1]=0b0000111111111110
A[2]=0b0011000111010010; B[2]=0b0111101111111110
A[3]=0b0010111001001101; B[3]=0b0011111101101111
A[4]=0b0100000111111000; B[4]=0b0101111111111100
A[5]=0b1010110010000101; B[5]=0b1111110110011111
A[6]=0b1001100110001100; B[6]=0b1111100110011111
A[7]=0b0101001100001111; B[7]=0b1101101101101111
A[8]=0b0111000101100000; B[8]=0b0111001101111111
A[9]=0b0010110001100011; B[9]=0b0110110001101111
A[10]=0b0110110100001000; B[10]=0b0110111110011110
A[11]=0b1001001001001100; B[11]=0b1101001111011100
A[12]=0b0111000001000000; B[12]=0b0111011101010010
A[13]=0b1001001010111110; B[13]=0b1111001011111110
A[14]=0b1001010011010010; B[14]=0b1011110111010011
A[15]=0b0110001010001101; B[15]=0b0110111111001101
A[16]=0b1011001000101000; B[16]=0b1011001011111011
A[17]=0b0001111001110001; B[17]=0b1001111111110101
A[18]=0b0010110110011011; B[18]=0b0011111111011111
A[19]=0b0100110110001100; B[19]=0b1101110110111110
C=[0]*24; D=[0]*24
C[0]=0b0001010010011110; D[0]=0b1011011011011111
C[1]=0b0101101011000100; D[1]=0b1111101011110100
C[2]=0b0001111100100100; D[2]=0b0001111110111111
C[3]=0b1100111010000101; D[3]=0b1100111011101111
C[4]=0b0100001010011111; D[4]=0b0101101110111111
C[5]=0b1001111000100010; D[5]=0b1111111110100010
C[6]=0b0010011110000110; D[6]=0b0111011111000110
C[7]=0b0010111101000110; D[7]=0b1010111111000110
C[8]=0b0000001011011011; D[8]=0b1010101111011011
C[9]=0b0111000011000110; D[9]=0b1111111011001110
C[10]=0b0100001000010010; D[10]=0b0111001010110110
C[11]=0b0100101111110001; D[11]=0b0110101111110011
C[12]=0b1000100101000001; D[12]=0b1011110101001111
C[13]=0b1000000000010001; D[13]=0b1001100010110011
C[14]=0b0101110000000100; D[14]=0b1111111010001101
C[15]=0b1100001000001001; D[15]=0b1110011000011011
C[16]=0b0101001001101100; D[16]=0b0111111001111110
C[17]=0b0100001001110100; D[17]=0b1100101001110111
C[18]=0b1100000001100111; D[18]=0b1100011101110111
C[19]=0b1010000001001010; D[19]=0b1111011101101010
C[20]=0b1001001001010101; D[20]=0b1101111011011101
C[21]=0b1001010000011011; D[21]=0b1001111000111011
C[22]=0b1011101101100001; D[22]=0b1011111101111111
C[23]=0b1101101000000111; D[23]=0b1101111011100111

print("="*70)
print("CORRECTED ECC VERIFICATION FOR lc_ctrl")
print("="*70)

# Verify ECC
ecc_comments_A = [0b001010,0b100101,0b000111,0b001010,0b011010,0b110001,0b010110,0b100010,
                  0b111001,0b101010,0b110011,0b000011,0b011110,0b000010,0b100011,0b000111,
                  0b010111,0b001001,0b000100,0b101010]
ecc_comments_B = [0b111110,0b111101,0b000111,0b111010,0b011110,0b110001,0b011110,0b100111,
                  0b111001,0b111111,0b111011,0b111111,0b111110,0b101110,0b101111,0b011111,
                  0b011111,0b011011,0b010101,0b101011]
mismatches = 0
for i in range(20):
    ca, cb = compute_ecc(A[i]), compute_ecc(B[i])
    if ca != ecc_comments_A[i]:
        print(f"  A[{i:2d}] ECC mismatch: computed=0b{ca:06b} comment=0b{ecc_comments_A[i]:06b}")
        mismatches += 1
    if cb != ecc_comments_B[i]:
        print(f"  B[{i:2d}] ECC mismatch: computed=0b{cb:06b} comment=0b{ecc_comments_B[i]:06b}")
        mismatches += 1
ecc_comments_C = [0b011100,0b111000,0b100011,0b011000,0b011000,0b111000,0b010000,0b000110,
                  0b000001,0b110001,0b110110,0b000001,0b000001,0b011111,0b111110,0b001011,
                  0b001000,0b010100,0b100000,0b101111,0b001110,0b100000,0b000100,0b001100]
ecc_comments_D = [0b111100,0b111101,0b100111,0b011011,0b111100,0b111110,0b011101,0b111111,
                  0b111011,0b110011,0b110111,0b110111,0b001011,0b111111,0b111110,0b011011,
                  0b001001,0b110110,0b100101,0b101111,0b001111,0b110101,0b000110,0b101110]
for i in range(24):
    cc, cd = compute_ecc(C[i]), compute_ecc(D[i])
    if cc != ecc_comments_C[i]:
        print(f"  C[{i:2d}] ECC mismatch: computed=0b{cc:06b} comment=0b{ecc_comments_C[i]:06b}")
        mismatches += 1
    if cd != ecc_comments_D[i]:
        print(f"  D[{i:2d}] ECC mismatch: computed=0b{cd:06b} comment=0b{ecc_comments_D[i]:06b}")
        mismatches += 1
if mismatches == 0:
    print("  PASS: All ECC bits match SV comments")
else:
    print(f"  TOTAL ECC MISMATCHES: {mismatches}")

# Full 22-bit HW/HD
AB_full = [full_word(A[i]) for i in range(20)] + [full_word(B[i]) for i in range(20)]
CD_full = [full_word(C[i]) for i in range(24)] + [full_word(D[i]) for i in range(24)]
print("\n--- Full 22-bit Hamming constraints ---")
ab_hw = [hamming_weight(v) for v in AB_full]
ab_hd = [hamming_distance(AB_full[i],AB_full[j]) for i in range(40) for j in range(i+1,40)]
print(f"  A/B: min_hw={min(ab_hw)}, max_hw={max(ab_hw)}, min_hd={min(ab_hd)}")
print(f"  SV claims: min_hw=6, max_hw=16, min_hd=6")
cd_hw = [hamming_weight(v) for v in CD_full]
cd_hd = [hamming_distance(CD_full[i],CD_full[j]) for i in range(48) for j in range(i+1,48)]
print(f"  C/D: min_hw={min(cd_hw)}, max_hw={max(cd_hw)}, min_hd={min(cd_hd)}")

# Find the pairs with min_hd
if min(ab_hd) < 6:
    print(f"\n  *** A/B min_hd={min(ab_hd)} < 6, finding closest pairs: ***")
    for i in range(40):
        for j in range(i+1,40):
            hd = hamming_distance(AB_full[i], AB_full[j])
            if hd == min(ab_hd):
                names = []
                if i < 20: names.append(f"A[{i}]")
                else: names.append(f"B[{i-20}]")
                if j < 20: names.append(f"A[{j}]")
                else: names.append(f"B[{j-20}]")
                print(f"    {names[0]} vs {names[1]}: hd={hd}")

if min(cd_hd) < 6:
    print(f"\n  *** C/D min_hd={min(cd_hd)} < 6, finding closest pairs: ***")
    for i in range(48):
        for j in range(i+1,48):
            hd = hamming_distance(CD_full[i], CD_full[j])
            if hd == min(cd_hd):
                names = []
                if i < 24: names.append(f"C[{i}]")
                else: names.append(f"D[{i-24}]")
                if j < 24: names.append(f"C[{j}]")
                else: names.append(f"D[{j-24}]")
                print(f"    {names[0]} vs {names[1]}: hd={hd}")

print(f"\n  hjson requires: min_hw>=5, max_hw<=17, min_hd>=5")
print(f"  A/B meets hjson: {'PASS' if min(ab_hw)>=5 and max(ab_hw)<=17 and min(ab_hd)>=5 else 'FAIL'}")
print(f"  C/D meets hjson: {'PASS' if min(cd_hw)>=5 and max(cd_hw)<=17 and min(cd_hd)>=5 else 'FAIL'}")
print(f"  A/B meets SV claim (min_hd>=6): {'PASS' if min(ab_hd)>=6 else 'FAIL'}")
print(f"  C/D meets SV claim (min_hd>=6): {'PASS' if min(cd_hd)>=6 else 'FAIL'}")
print("="*70)
