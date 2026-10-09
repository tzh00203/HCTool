# VULN-030 Verification Result

## Verdict
**[poc-success]** L2 fidelity

## Finding
Ascon SEC_WIPE clears KEY/NONCE shares to `'0` instead of PRD (edn_data).
Lines: ascon_core.sv:163,172,213,222 — `hw2reg.key_share0[i].d = '0`,
`hw2reg.key_share1[i].d = '0`, `hw2reg.nonce_share0[i].d = '0`,
`hw2reg.nonce_share1[i].d = '0`.
Deterministic zero clearing provides zero SCA protection.

## Twin Repair
Replace `'0` with `edn_data[i]` (PRD from entropy/EDN).
Oracle: sibling module aes_core uses `prd_clearing_key`/`prd_clearing_data`
for SEC_WIPE; ascon.hjson specifies "secure wipe of sensitive data".

## Reproduction Command
```bash
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-030/build_ascon_secwipe_prd.sh
```

## Raw Output
```
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: Ascon SEC_WIPE clears KEY/NONCE shares to '0 instead of PRD.
  hw2reg.key_share0[i].d = '0 (line 163), key_share1[i].d = '0 (line 172),
  hw2reg.nonce_share0[i].d = '0 (line 213), nonce_share1[i].d = '0 (line 222).
  Deterministic zero clearing provides no SCA protection.
  Twin uses edn_data (PRD) per sibling module pattern (aes_core prd_clearing_*).
exit code: 1 (1 = finding confirmed)
```

## Twin Diff Summary
- ascon_core.sv:163: `assign hw2reg.key_share0[i].d = '0` → `= edn_data[i]`
- ascon_core.sv:172: `assign hw2reg.key_share1[i].d = '0` → `= edn_data[i]`
- ascon_core.sv:213: `assign hw2reg.nonce_share0[i].d = '0` → `= edn_data[i]`
- ascon_core.sv:222: `assign hw2reg.nonce_share1[i].d = '0` → `= edn_data[i]`
- Oracle: sibling module aes_core prd_clearing_* pattern + ascon.hjson "secure wipe"
