# RESULT: VULN-057

## Verdict
**[poc-success]** — finding confirmed

## Fidelity
L4 (static conclusion — SEC_CM mismatch + wipe value source analysis)

## Finding
HMAC `wipe_v = reg2hw.wipe_secret.q` (hmac.sv:211) is **SW-controlled**, not PRD.
When `wipe_secret` is triggered, `secret_key_d = {32{wipe_v}}` uses a software-specified
value, making the "secure wipe" **deterministic** — zero SCA protection.

The `countermeasures` list in hmac.hjson (line 166) only declares `BUS.INTEGRITY`.
No `KEY.SEC_WIPE` or `DIGEST.SEC_WIPE` declaration exists, even though the RTL implements
key and digest wipe logic. The `HMAC.SECURE_WIPE` feature entry (hjson line 162-164)
describes "Wipe ... with constant value provided by software" — confirming non-PRD design.

AES sibling IP declares `KEY.SEC_WIPE`, `IV.CONFIG.SEC_WIPE`, `DATA_REG.SEC_WIPE` in
its `countermeasures` list, all using PRD (`prd_clearing_key_i` / `prd_clearing_data_i`
from EDN/CSRNG).

## Twin Repair
- hmac.sv:211: `assign wipe_v = reg2hw.wipe_secret.q;` → `assign wipe_v = prd_wipe_v_i;`
- Added `prd_wipe_v_i` input port (32-bit, from entropy/CSRNG)
- Added SEC_CM comments: `KEY.SEC_WIPE`, `DIGEST.SEC_WIPE`
- Oracle: AES KEY.SEC_WIPE / DATA_REG.SEC_WIPE pattern (PRD from EDN)

## Reproduce
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-057
bash build_hmac_wipe_v.sh
# exit code 1 = finding confirmed
```

## Raw Output
```
VULN-057: HMAC wipe_v from SW (not PRD) + SEC_CM only BUS.INTEGRITY
=============================================================
Vuln: wipe_v = reg2hw.wipe_secret.q (SW-controlled, deterministic)
Twin: wipe_v = prd_wipe_v_i (PRD from entropy, random)
-------------------------------------------------------------
Vuln uses SW wipe value:  YES
Twin uses PRD wipe value: YES
SEC_CM mismatch (missing KEY.SEC_WIPE, DIGEST.SEC_WIPE): YES

CONFIRMED: hmac.sv:211 wipe_v = reg2hw.wipe_secret.q — SW-controlled
wipe value, not PRD. secret_key_d = {32{wipe_v}} is deterministic,
providing zero SCA protection. SEC_CM countermeasures list has only
BUS.INTEGRITY — missing KEY.SEC_WIPE and DIGEST.SEC_WIPE declarations.
exit code: 1 (1 = finding confirmed)
```

## Static Evidence
- hmac.sv:211 — `assign wipe_v = reg2hw.wipe_secret.q;` (SW register, not PRD)
- hmac.sv:777 — `// SEC_CM: BUS.INTEGRITY` (only SEC_CM declaration)
- hmac.hjson:166-170 — `countermeasures: [{ name: "BUS.INTEGRITY" }]` (no SEC_WIPE)
- hmac.hjson:162-164 — `HMAC.SECURE_WIPE` feature: "constant value provided by software"
- aes.hjson:353-359 — `KEY.SEC_WIPE`, `IV.CONFIG.SEC_WIPE`, `DATA_REG.SEC_WIPE` (sibling with PRD)

## Deliverables
- `tb_hmac_wipe_v_source.sv` — combinational micro-tb
- `hmac_twin.sv` — repaired twin (wipe_v from PRD, SEC_CM declarations added)
- `build_hmac_wipe_v.sh` — Verilator build script
- `sim_main.cpp` — C++ simulation driver
- `exploit.py` — PoC entry (redbud mode)

## Upgrade (2026-09-23)

### Verdict
**[poc-success]** — finding confirmed at upgraded fidelity

### Fidelity
L2 (data-flow empirical — combinational micro-tb vuln-vs-twin diff) for C1+C2;
L3 (script-level empirical — hjson parsing + sibling comparison) for C3

### Sub-claim Upgrade Results

| Claim | Description | Type | Original | Upgraded | Evidence |
|-------|-------------|------|----------|----------|----------|
| C1 | `wipe_v = reg2hw.wipe_secret.q` is SW-controlled, not PRD; `secret_key_d = {32{wipe_v}}` deterministic | behavior-simulatable | L4 | **L2** | Verilator micro-tb diff: vuln wipe_v=SW, twin wipe_v=PRD, key_wipe_differs=YES |
| C2 | Same SW `wipe_v` propagates to `prim_sha2_32.wipe_v_i` → digest wipe also deterministic | behavior-simulatable | L4 | **L2** | Same micro-tb (C1); `wipe_v_i` port chain hmac→prim_sha2_32 traced at hmac.sv:741-742 |
| C3 | `countermeasures` list missing `KEY.SEC_WIPE` and `DIGEST.SEC_WIPE` | declaration-missing | L'4 | **%20**L3** | Python script parses hmac.hjson: only `BUS.INTEGRITY`; AES sibling has 3 SEC_WIPE; HMAC.SECURE_WIPE confirms "software" |

### Oracle References
- AES sibling IP: `aes.hjson:353-359` declares `KEY.SEC_WIPE`, `IV.CONFIG.SEC_WIPE`, `DATA_REG.SEC_WIPE`
- AES RTL: `prd_clearing_key_i` / `prd_clearing_data_i` from EDN/CSRNG (PRD source)
- HMAC hjson: `HMAC.SECURE_WIPE` feature (line 162-164) says "constant value provided by software"

### Reproduce

L2 micro-tb (C1+C2):
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-057/upgrade
bash build_hmac_wipe_v_diff.sh
# exit code 1 = finding confirmed
```

L3 script proof (C3):
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-057/upgrade
python3 prove_seccm_missing.py
# exit code 1 = finding confirmed
```

### Raw Output (L2)
```
VULN-057 Upgrade: HMAC wipe_v from SW (not PRD) — L2 micro-tb diff
================================================================
Claim C1: wipe_v = reg2hw.wipe_secret.q (SW, not PRD)
Claim C2: same SW wipe_v propagates to prim_sha2_32 digest wipe
Twin: wipe_v = prd_wipe_v_i (PRD from entropy)
Oracle: AES KEY.SEC_WIPE uses prd_clearing_key_i from EDN/CSRNG
----------------------------------------------------------------
vuln_is_sw (wipe_v = SW reg):           YES
twin_is_prd (wipe_v = PRD, != SW):      YES
key_wipe_differs (vuln != twin):         YES
vuln_key_deterministic (all words=SW):   YES

CONFIRMED [L2]: hmac.sv:211 wipe_v = reg2hw.wipe_secret.q — SW-controlled
wipe value, not PRD. secret_key_d = {32{wipe_v}} is deterministic
(all 32 words = SW-written value), providing zero SCA protection.
Twin: wipe_v = prd_wipe_v_i (PRD from entropy), key_wipe differs.
Same SW wipe_v propagates to prim_sha2_32 via wipe_v_i (C2).
exit code: 1 (1 = finding confirmed)
```

### Raw Output (L3)
```
VULN-057 Claim C3: SEC_CM declaration mismatch — L3 script proof
=================================================================

1. HMAC countermeasures: ['BUS.INTEGRITY']
   Only BUS.INTEGRITY? True

2. Missing in HMAC: ['KEY.SEC_WIPE', 'DIGEST.SEC_WIPE']

3. AES countermeasures: ['BUS.INTEGRITY', 'LC_ESCALATE_EN.INTERSIG.MUBI', ...]
   AES has SEC_WIPE? True

4. HMAC feature: HMAC.SECURE_WIPE
   Desc: Wipe of internal state and secret key with constant value provided by software.
   Confirms SW-controlled (non-PRD)? True

=================================================================
CONFIRMED [L3]: HMAC countermeasures list has only BUS.INTEGRITY.
Missing: ['KEY.SEC_WIPE', 'DIGEST.SEC_WIPE']. AES sibling declares SEC_WIPE countermeasures.
HMAC.SECURE_WIPE feature confirms 'constant value provided by software'
— non-PRD design violates OT convention for SEC_WIPE.
```

### Upgrade Deliverables
- `upgrade/tb_hmac_wipe_v_diff.sv` — L2 combinational micro-tb (4-bit verdict)
- `upgrade/sim_main.cpp` — C++ simulation driver
- `upgrade/build_hmac_wipe_v_diff.sh` — Verilator build script
- `upgrade/exploit.py` — PoC entry (redbud mode)
- `upgrade/prove_seccm_missing.py` — L3 script proof (hjson parse + sibling compare)
