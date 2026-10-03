#!/usr/bin/env python3
"""AES RndCnst constant folding verification.

Parses the 5 RndCnst constants from aes_pkg.sv, verifies:
1. Permutation bijectivity (matching SVA PermutationCheck_A / SharePermutationCheck_A)
2. Seeds are non-zero
3. Reports parsed values for manual comparison against gen-lfsr-seed.py output

This script does NOT verify correctness against upstream — that requires
running gen-lfsr-seed.py with seed 31468618 and comparing bit-exact.
"""

import re
import sys

PKG_PATH = "/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_pkg.sv"

def parse_sv_hex_chunks(text, var_name):
    """Extract hex chunks from a multi-line SV parameter assignment."""
    # Find the assignment
    pattern = rf'{var_name}\s*=\s*{{([^;]+)}}'
    m = re.search(pattern, text, re.DOTALL)
    if m:
        chunks = re.findall(r"(\d+)'h([0-9a-fA-F]+)", m.group(1))
        return [(int(bits), hex_str.lower()) for bits, hex_str in chunks]
    # Try single-line assignment
    pattern2 = rf'{var_name}\s*=\s*(\d+)\'h([0-9a-fA-F]+);'
    m2 = re.search(pattern2, text)
    if m2:
        return [(int(m2.group(1)), m2.group(2).lower())]
    return []

def concat_hex(chunks, total_bits):
    """Concatenate hex chunks into a single integer."""
    result = 0
    for bits, hex_str in chunks:
        val = int(hex_str, 16)
        result = (result << bits) | val
    return result

def verify_permutation(perm_val, width, name):
    """Verify a permutation is bijective."""
    entry_bits = (width - 1).bit_length()  # $clog2(width)
    num_entries = width
    mask = (1 << entry_bits) - 1

    seen = set()
    for i in range(num_entries):
        entry = (perm_val >> (i * entry_bits)) & mask
        if entry in seen:
            print(f"  FAIL: {name} entry {i} = {entry} is duplicate")
            return False
        if entry >= width:
            print(f"  FAIL: {name} entry {i} = {entry} >= width {width}")
            return False
        seen.add(entry)

    if len(seen) != width:
        print(f"  FAIL: {name} not all values 0..{width-1} present")
        return False

    print(f"  PASS: {name} is a valid bijective permutation on [0, {width-1}]")
    return True

def main():
    with open(PKG_PATH) as f:
        text = f.read()

    results = {}

    # 1. ClearingLfsrSeed (64-bit data)
    chunks = parse_sv_hex_chunks(text, "RndCnstClearingLfsrSeedDefault")
    if chunks:
        val = concat_hex(chunks, 64)
        results["ClearingLfsrSeed"] = val
        print(f"ClearingLfsrSeed = 0x{val:016x} ({64} bits)")
        print(f"  Non-zero: {val != 0}")
    else:
        print("FAIL: Could not parse ClearingLfsrSeedDefault")

    # 2. ClearingLfsrPerm (64-entry permutation, each entry 6 bits, total 384 bits)
    chunks = parse_sv_hex_chunks(text, "RndCnstClearingLfsrPermDefault")
    if chunks:
        total_bits = sum(bits for bits, _ in chunks)
        val = concat_hex(chunks, total_bits)
        results["ClearingLfsrPerm"] = val
        print(f"ClearingLfsrPerm parsed from {len(chunks)} chunks, {total_bits} bits")
        verify_permutation(val, 64, "ClearingLfsrPerm")
    else:
        print("FAIL: Could not parse ClearingLfsrPermDefault")

    # 3. ClearingSharePerm (64-entry permutation)
    chunks = parse_sv_hex_chunks(text, "RndCnstClearingSharePermDefault")
    if chunks:
        total_bits = sum(bits for bits, _ in chunks)
        val = concat_hex(chunks, total_bits)
        results["ClearingSharePerm"] = val
        print(f"ClearingSharePerm parsed from {len(chunks)} chunks, {total_bits} bits")
        verify_permutation(val, 64, "ClearingSharePerm")
    else:
        print("FAIL: Could not parse ClearingSharePermDefault")

    # 4. MaskingLfsrPerm (160-entry permutation, each entry 8 bits, total 1280 bits)
    chunks = parse_sv_hex_chunks(text, "RndCnstMaskingLfsrPermDefault")
    if chunks:
        total_bits = sum(bits for bits, _ in chunks)
        val = concat_hex(chunks, total_bits)
        results["MaskingLfsrPerm"] = val
        print(f"MaskingLfsrPerm parsed from {len(chunks)} chunks, {total_bits} bits")
        verify_permutation(val, 160, "MaskingLfsrPerm")
    else:
        print("FAIL: Could not parse MaskingLfsrPermDefault")

    # 5. MaskingLfsrSeed (288-bit data)
    chunks = parse_sv_hex_chunks(text, "RndCnstMaskingLfsrSeedDefault")
    if chunks:
        total_bits = sum(bits for bits, _ in chunks)
        val = concat_hex(chunks, total_bits)
        results["MaskingLfsrSeed"] = val
        print(f"MaskingLfsrSeed parsed from {len(chunks)} chunks, {total_bits} bits")
        print(f"  Non-zero: {val != 0}")
        print(f"  Value (hex): 0x{val:0{total_bits//4}x}")
    else:
        print("FAIL: Could not parse MaskingLfsrSeedDefault")

    print("\n--- REMINDER ---")
    print("This script verifies permutation bijectivity (matching SVA).")
    print("It does NOT verify correctness against upstream.")
    print("To verify correctness, run:")
    print("  $ util/design/gen-lfsr-seed.py --width 64  --seed 31468618 --prefix Clearing")
    print("  $ util/design/gen-lfsr-seed.py --width 160 --seed 31468618 --prefix Masking")
    print("  $ util/design/gen-lfsr-seed.py --width 288 --seed 31468618 --prefix Masking")
    print("and compare bit-exact against the values parsed above.")

if __name__ == "__main__":
    main()
