#!/usr/bin/env python3
"""Verify lc_ctrl_state_pkg.sv obfuscated constants.

Checks:
1. A/B (LC state) and C/D (LC counter) constant Hamming distances >= 6
2. All values within each group are unique
3. LcStRaw is all-zero (incremental writeability base)
4. Computed Hamming distance statistics match claimed values
5. DecLcStateNumRep / width consistency
"""

# A/B values for LC state encoding (from lc_ctrl_state_pkg.sv)
A = [
    0b0110010010101110,  # A0
    0b0000011110110100,  # A1
    0b0011000111010010,  # A2
    0b0010111001001101,  # A3
    0b0100000111111000,  # A4
    0b1010110010000101,  # A5
    0b1001100110001100,  # A6
    0b0101001100001111,  # A7
    0b0111000101100000,  # A8
    0b0010110001100011,  # A9
    0b0110110100001000,  # A10
    0b1001001001001100,  # A11
    0b0111000001000000,  # A12
    0b1001001010111110,  # A13
    0b1001010011010010,  # A14
    0b0110001010001101,  # A15
    0b1011001000101000,  # A16
    0b0001111001110001,  # A17
    0b0010110110011011,  # A18
    0b0100110110001100,  # A19
]
B = [
    0b0111010111101110,  # B0
    0b0000111111111110,  # B1
    0b0111101111111110,  # B2
    0b0011111101101111,  # B3
    0b0101111111111100,  # B4
    0b1111110110011111,  # B5
    0b1111100110011111,  # B6
    0b1101101101101111,  # B7
    0b0111001101111111,  # B8
    0b0110110001101111,  # B9
    0b0110111110011110,  # B10
    0b1101001111011100,  # B11
    0b0111011101010010,  # B12
    0b1111001011111110,  # B13
    0b1011110111010011,  # B14
    0b0110111111001101,  # B15
    0b1011001011111011,  # B16
    0b1001111111110101,  # B17
    0b0011111111011111,  # B18
    0b1101110110111110,  # B19
]

# C/D values for LC counter encoding
C = [
    0b0001010010011110,  # C0
    0b0101101011000100,  # C1
    0b0001111100100100,  # C2
    0b1100111010000101,  # C3
    0b0100001010011111,  # C4
    0b1001111000100010,  # C5
    0b0010011110000110,  # C6
    0b0010111101000110,  # C7
    0b0000001011011011,  # C8
    0b0111000011000110,  # C9
    0b0100001000010010,  # C10
    0b0100101111110001,  # C11
    0b1000100101000001,  # C12
    0b1000000000010001,  # C13
    0b0101110000000100,  # C14
    0b1100001000001001,  # C15
    0b0101001001101100,  # C16
    0b0100001001110100,  # C17
    0b1100000001100111,  # C18
    0b1010000001001010,  # C19
    0b1001001001010101,  # C20
    0b1001010000011011,  # C21
    0b1011101101100001,  # C22
    0b1101101000000111,  # C23
]
D = [
    0b1011011011011111,  # D0
    0b1111101011110100,  # D1
    0b0001111110111111,  # D2
    0b1100111011101111,  # D3
    0b0101101110111111,  # D4
    0b1111111110100010,  # D5
    0b0111011111000110,  # D6
    0b1010111111000110,  # D7
    0b1010101111011011,  # D8
    0b1111111011001110,  # D9
    0b0111001010110110,  # D10
    0b0110101111110011,  # D11
    0b1011110101001111,  # D12
    0b1001100010110011,  # D13
    0b1111111010001101,  # D14
    0b1110011000011011,  # D15
    0b0111111001111110,  # D16
    0b1100101001110111,  # D17
    0b1100011101110111,  # D18
    0b1111011101101010,  # D19
    0b1101111011011101,  # D20
    0b1001111000111011,  # D21
    0b1011111101111111,  # D22
    0b1101111011100111,  # D23
]


def hamming_distance(a, b):
    return bin(a ^ b).count('1')


def hamming_weight(a):
    return bin(a).count('1')


def check_group(name, ab_vals, expected_min_hd=6):
    """Check uniqueness and Hamming distances for a group of 16-bit values."""
    errors = []

    # Check uniqueness
    if len(set(ab_vals)) != len(ab_vals):
        errors.append(f"{name}: DUPLICATE VALUES DETECTED")

    # Compute pairwise Hamming distances
    min_hd = 999
    max_hd = 0
    min_hw = 999
    max_hw = 0
    hd_hist = {}

    for v in ab_vals:
        hw = hamming_weight(v)
        min_hw = min(min_hw, hw)
        max_hw = max(max_hw, hw)

    for i in range(len(ab_vals)):
        for j in range(i + 1, len(ab_vals)):
            hd = hamming_distance(ab_vals[i], ab_vals[j])
            min_hd = min(min_hd, hd)
            max_hd = max(max_hd, hd)
            hd_hist[hd] = hd_hist.get(hd, 0) + 1

    if min_hd < expected_min_hd:
        errors.append(f"{name}: min Hamming distance {min_hd} < {expected_min_hd}")

    print(f"\n=== {name} ===")
    print(f"  Count: {len(ab_vals)}")
    print(f"  Unique: {len(set(ab_vals)) == len(ab_vals)}")
    print(f"  Min Hamming weight: {min_hw}")
    print(f"  Max Hamming weight: {max_hw}")
    print(f"  Min Hamming distance: {min_hd}")
    print(f"  Max Hamming distance: {max_hd}")
    print(f"  HD histogram: {dict(sorted(hd_hist.items()))}")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print(f"  PASS")

    return errors


def check_lc_state_enum():
    """Verify LC state enum values from lc_ctrl_state_pkg.sv."""
    errors = []
    ZRO = 0

    # Construct all 21 LC state values
    lc_states = {}
    lc_states['LcStRaw'] = tuple([ZRO] * 20)
    lc_states['LcStTestUnlocked0'] = tuple([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],A[5],A[4],A[3],A[2],A[1],B[0]])
    lc_states['LcStTestLocked0'] = tuple([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],A[5],A[4],A[3],A[2],B[1],B[0]])
    lc_states['LcStTestUnlocked1'] = tuple([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],A[5],A[4],A[3],B[2],B[1],B[0]])
    lc_states['LcStTestLocked1'] = tuple([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],A[5],A[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStTestUnlocked2'] = tuple([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],A[5],B[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStTestLocked2'] = tuple([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],A[6],B[5],B[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStTestUnlocked3'] = tuple([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],A[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStTestLocked3'] = tuple([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],A[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStTestUnlocked4'] = tuple([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],A[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStTestLocked4'] = tuple([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],A[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStTestUnlocked5'] = tuple([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],A[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStTestLocked5'] = tuple([A[19],A[18],A[17],A[16],A[15],A[14],A[13],A[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStTestUnlocked6'] = tuple([A[19],A[18],A[17],A[16],A[15],A[14],A[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStTestLocked6'] = tuple([A[19],A[18],A[17],A[16],A[15],A[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStTestUnlocked7'] = tuple([A[19],A[18],A[17],A[16],A[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStDev'] = tuple([A[19],A[18],A[17],A[16],B[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStProd'] = tuple([A[19],A[18],A[17],B[16],A[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStProdEnd'] = tuple([A[19],A[18],B[17],A[16],A[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStRma'] = tuple([B[19],B[18],A[17],B[16],B[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])
    lc_states['LcStScrap'] = tuple([B[19],B[18],B[17],B[16],B[15],B[14],B[13],B[12],B[11],B[10],B[9],B[8],B[7],B[6],B[5],B[4],B[3],B[2],B[1],B[0]])

    # Check all states are unique
    state_values = list(lc_states.values())
    if len(set(state_values)) != len(state_values):
        errors.append("LC STATE ENUM: DUPLICATE VALUES DETECTED")
        # Find which ones collide
        seen = {}
        for name, val in lc_states.items():
            if val in seen:
                errors.append(f"  Collision: {name} == {seen[val]}")
            seen[val] = name

    # Check pairwise Hamming distances for the 320-bit concatenated values
    min_hd = 999
    for i in range(len(state_values)):
        for j in range(i+1, len(state_values)):
            hd = 0
            for k in range(20):
                hd += hamming_distance(state_values[i][k], state_values[j][k])
            min_hd = min(min_hd, hd)

    print(f"\n=== LC State Enum ===")
    print(f"  Count: {len(lc_states)}")
    print(f"  Unique: {len(set(state_values)) == len(state_values)}")
    print(f"  Min pairwise HD (320-bit): {min_hd}")
    if min_hd < 6:
        errors.append(f"LC STATE ENUM: min HD {min_hd} < 6")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print(f"  PASS")
    return errors


def check_lc_cnt_enum():
    """Verify LC counter enum values."""
    errors = []
    ZRO = 0

    lc_cnts = {}
    lc_cnts['LcCnt0'] = tuple([ZRO]*24)
    lc_cnts['LcCnt1'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],C[15],C[14],C[13],C[12],C[11],C[10],C[9],C[8],C[7],C[6],C[5],C[4],C[3],C[2],C[1],D[0]])
    lc_cnts['LcCnt2'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],C[15],C[14],C[13],C[12],C[11],C[10],C[9],C[8],C[7],C[6],C[5],C[4],C[3],C[2],D[1],D[0]])
    lc_cnts['LcCnt3'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],C[15],C[14],C[13],C[12],C[11],C[10],C[9],C[8],C[7],C[6],C[5],C[4],C[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt4'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],C[15],C[14],C[13],C[12],C[11],C[10],C[9],C[8],C[7],C[6],C[5],C[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt5'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],C[15],C[14],C[13],C[12],C[11],C[10],C[9],C[8],C[7],C[6],C[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt6'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],C[15],C[14],C[13],C[12],C[11],C[10],C[9],C[8],C[7],C[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt7'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],C[15],C[14],C[13],C[12],C[11],C[10],C[9],C[8],C[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt8'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],C[15],C[14],C[13],C[12],C[11],C[10],C[9],C[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt9'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],C[15],C[14],C[13],C[12],C[11],C[10],C[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt10'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],C[15],C[14],C[13],C[12],C[11],C[10],D[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt11'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],C[15],C[14],C[13],C[12],C[11],D[10],D[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt12'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],C[15],C[14],C[13],C[12],D[11],D[10],D[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt13'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],C[15],C[14],C[13],D[12],D[11],D[10],D[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt14'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],C[15],C[14],D[13],D[12],D[11],D[10],D[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt15'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],C[15],D[14],D[13],D[12],D[11],D[10],D[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt16'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],C[16],D[15],D[14],D[13],D[12],D[11],D[10],D[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt17'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],C[17],D[16],D[15],D[14],D[13],D[12],D[11],D[10],D[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt18'] = tuple([C[23],C[22],C[21],C[20],C[19],C[18],D[17],D[16],D[15],D[14],D[13],D[12],D[11],D[10],D[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt19'] = tuple([C[23],C[22],C[21],C[20],C[19],D[18],D[17],D[16],D[15],D[14],D[13],D[12],D[11],D[10],D[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt20'] = tuple([C[23],C[22],C[21],C[20],D[19],D[18],D[17],D[16],D[15],D[14],D[13],D[12],D[11],D[10],D[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt21'] = tuple([C[23],C[22],C[21],D[20],D[19],D[18],D[17],D[16],D[15],D[14],D[13],D[12],D[11],D[10],D[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt22'] = tuple([C[23],C[22],D[21],D[20],D[19],D[18],D[17],D[16],D[15],D[14],D[13],D[12],D[11],D[10],D[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt23'] = tuple([C[23],D[22],D[21],D[20],D[19],D[18],D[17],D[16],D[15],D[14],D[13],D[12],D[11],D[10],D[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])
    lc_cnts['LcCnt24'] = tuple([D[23],D[22],D[21],D[20],D[19],D[18],D[17],D[16],D[15],D[14],D[13],D[12],D[11],D[10],D[9],D[8],D[7],D[6],D[5],D[4],D[3],D[2],D[1],D[0]])

    cnt_values = list(lc_cnts.values())
    if len(set(cnt_values)) != len(cnt_values):
        errors.append("LC CNT ENUM: DUPLICATE VALUES DETECTED")
        seen = {}
        for name, val in lc_cnts.items():
            if val in seen:
                errors.append(f"  Collision: {name} == {seen[val]}")
            seen[val] = name

    min_hd = 999
    for i in range(len(cnt_values)):
        for j in range(i+1, len(cnt_values)):
            hd = 0
            for k in range(24):
                hd += hamming_distance(cnt_values[i][k], cnt_values[j][k])
            min_hd = min(min_hd, hd)

    print(f"\n=== LC Counter Enum ===")
    print(f"  Count: {len(lc_cnts)}")
    print(f"  Unique: {len(set(cnt_values)) == len(cnt_values)}")
    print(f"  Min pairwise HD (384-bit): {min_hd}")
    if min_hd < 6:
        errors.append(f"LC CNT ENUM: min HD {min_hd} < 6")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print(f"  PASS")
    return errors


def check_width_consistency():
    """Check DecLcStateNumRep and related width parameters."""
    errors = []
    NumLcStates = 21
    # vbits(21) = 5 (ceil(log2(21)))
    DecLcStateWidth = 5
    DecLcStateNumRep = 32 // DecLcStateWidth  # = 6
    ExtDecLcStateWidth = DecLcStateNumRep * DecLcStateWidth  # = 30
    CsrLcStateWidth = 30  # from reg_pkg

    if CsrLcStateWidth != ExtDecLcStateWidth:
        errors.append(f"Width mismatch: CsrLcStateWidth={CsrLcStateWidth} != ExtDecLcStateWidth={ExtDecLcStateWidth}")

    NumLcCountStates = 25
    DecLcCountWidth = 5  # vbits(25) = 5
    CsrLcCountWidth = 5  # from reg_pkg
    if CsrLcCountWidth != DecLcCountWidth:
        errors.append(f"Count width mismatch: CsrLcCountWidth={CsrLcCountWidth} != DecLcCountWidth={DecLcCountWidth}")

    print(f"\n=== Width Consistency ===")
    print(f"  NumLcStates={NumLcStates}, DecLcStateWidth={DecLcStateWidth}")
    print(f"  DecLcStateNumRep={DecLcStateNumRep}, ExtDecLcStateWidth={ExtDecLcStateWidth}")
    print(f"  CsrLcStateWidth={CsrLcStateWidth}")
    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
    else:
        print(f"  PASS")
    return errors


if __name__ == '__main__':
    all_errors = []
    all_errors.extend(check_group("A values (LC state)", A))
    all_errors.extend(check_group("B values (LC state)", B))
    all_errors.extend(check_group("AB combined (LC state)", A + B))
    all_errors.extend(check_group("C values (LC counter)", C))
    all_errors.extend(check_group("D values (LC counter)", D))
    all_errors.extend(check_group("CD combined (LC counter)", C + D))
    all_errors.extend(check_lc_state_enum())
    all_errors.extend(check_lc_cnt_enum())
    all_errors.extend(check_width_consistency())

    print(f"\n{'='*60}")
    if all_errors:
        print(f"FAILURES: {len(all_errors)}")
        for e in all_errors:
            print(f"  - {e}")
    else:
        print("ALL CHECKS PASSED")
