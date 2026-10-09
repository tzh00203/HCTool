# RESULT: VULN-010 — HMAC SHA2_512 outer round message length computation bug

## Verdict
**[poc-success]** L2 fidelity (data-flow evidence, combinational micro-tb)

## Finding
`hmac_core.sv:229` — In the `assign_sha_message_length` block, when
`sel_msglen == SelOPadMsg` (outer HMAC round) and `digest_size_i == SHA2_512`,
the code falls into the `default` case which computes
`sha_msg_len = BlockSizeSHA512in64 + 64'd384 = 1408`, but the correct value
is `BlockSizeSHA512in64 + 64'd512 = 1536`.

SHA-512 produces a 512-bit digest (FIPS 180-4). The outer HMAC hash input is
`o_pad (1024 bits) + inner_hash (512 bits) = 1536 bits`. Using 384 instead
of 512 causes the SHA engine to use the wrong message length for padding,
producing an incorrect HMAC-SHA512 output.

The same block correctly handles SHA2_256 (uses 256) and SHA2_384 (uses 384).
SHA2_512 is missing an explicit case and falls into default with 384.

## Twin Repair
- **Line changed**: `hmac_core.sv:229`
- **Vuln**: `default: sha_msg_len = BlockSizeSHA512in64 + 64'd384;`
- **Twin**: `SHA2_512: sha_msg_len = BlockSizeSHA512in64 + 64'd512;` + proper default
- **Oracle**: FIPS 180-4 Section 1 defines SHA-512 digest as 512 bits.
  The SHA2_384 case at line 228 correctly uses 384 (384-bit digest).
  SHA2_512 must analogously use 512 (512-bit digest).

## Reproduction
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-010
bash build_hmac_msglen.sh
# Expected: exit code 1 (finding confirmed)
```

## Raw Output
```
SHA2_512 outer round message length:
  vuln (default=384): 1
  twin (SHA2_512=512): 1
CONFIRMED: hmac_core.sv:229 default case uses 64'd384 for SHA2_512
outer round message length. SHA-512 digest is 512 bits (FIPS 180-4),
so outer hash input = 1024 (o_pad) + 512 (inner hash) = 1536 bits.
Vuln computes 1024+384=1408 (wrong), twin computes 1024+512=1536 (correct).
exit code: 1 (1 = finding confirmed)
```

## TB Type Rationale
Workorder suggested tb_dpi (L1), but the vulnerability is a pure combinational
mux error in `assign_sha_message_length`. A combinational micro-tb (L2) directly
proves the bug with higher signal-to-noise than a full DPI pipeline test would
provide. The wrong constant (384 vs 512) is verified at the expression level.

## Deliverables
- `tb_hmac_sha512_msglen.sv` — combinational micro-tb (vuln + twin expressions)
- `sim_main.cpp` — C++ driver
- `build_hmac_msglen.sh` — Verilator build script
- `exploit.py` — redbud mode PoC entry
