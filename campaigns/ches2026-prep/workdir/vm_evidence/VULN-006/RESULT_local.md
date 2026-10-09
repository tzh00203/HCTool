# RESULT: VULN-006

## Verdict: [poc-success] — L2 Data-Flow Evidence

## Vulnerability

AES cipher core key clearing uses `key_expand_out` (key derivation material) instead of `prd_clearing_key_i` (pseudo-random data) in two mux branches:

1. **`aes_cipher_core.sv:443`** — `KEY_FULL_CLEAR: key_full_d = key_expand_out;`
   Should be: `KEY_FULL_CLEAR: key_full_d = prd_clearing_key_i;`

2. **`aes_cipher_core.sv:462`** — `KEY_DEC_CLEAR: key_dec_d = key_expand_out;`
   Should be: `KEY_DEC_CLEAR: key_dec_d = prd_clearing_key_i;`

**Impact:** Key registers are "cleared" by overwriting with deterministic key-derived material instead of pseudo-random data. Key remnants survive the "secure wipe" operation, violating SEC_CM: KEY.SEC_WIPE.

## Twin Repair

| Line | Vuln | Twin | Oracle |
|------|------|------|--------|
| 443 | `KEY_FULL_CLEAR: key_full_d = key_expand_out;` | `KEY_FULL_CLEAR: key_full_d = prd_clearing_key_i;` | default branch in same mux uses `prd_clearing_key_i`; `KEY_FULL_DEC_INIT` with `CiphOpFwdOnly=1` also uses `prd_clearing_key_i` |
| 462 | `KEY_DEC_CLEAR: key_dec_d = key_expand_out;` | `KEY_DEC_CLEAR: key_dec_d = prd_clearing_key_i;` | default branch in same mux uses `prd_clearing_key_i` |

## Fidelity Level

**L2 — Data-Flow Evidence**: Combinational micro-tb directly compares mux branch outputs. The expressions are copied verbatim from the RTL mux logic.

## Reproduction Command

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-006
bash build_aes_key_clear.sh
```

## Raw Output

```
KEY_FULL_CLEAR: vuln outputs key_expand_out: YES  twin outputs PRD: YES
CONFIRMED: aes_cipher_core.sv:443,462 KEY_FULL_CLEAR/KEY_DEC_CLEAR
branches use key_expand_out (key derivation material) instead of
prd_clearing_key_i (pseudo-random data). Key registers are
"cleared" with deterministic key-derived material, leaking key
remnants. Twin fixes both branches to prd_clearing_key_i per
default branch pattern and SEC_CM:KEY.SEC_WIPE oracle.
exit code: 1 (1 = finding confirmed)
```

## Deliverables

| File | Path |
|------|------|
| Testbench | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-006/tb_aes_key_clear.sv` |
| C++ Driver | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-006/sim_main.cpp` |
| Build Script | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-006/build_aes_key_clear.sh` |
| PoC Entry | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-006/exploit.py` |
