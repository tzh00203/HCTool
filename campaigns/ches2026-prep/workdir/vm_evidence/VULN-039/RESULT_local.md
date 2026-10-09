# RESULT: VULN-039

## Verdict: [poc-success]

## Fidelity: L2 (组合 micro-tb，数据流实证)

## Finding

hmac.sv:846-876 err_code priority case has two bugs:
1. **Duplicate case item**: `hash_start_sha_disabled` branch appears twice (lines 851-853 and 856-858), which is redundant but masks the structural omission.
2. **Missing `invalid_config_atstart` branch**: When `invalid_config_atstart=1` and all other error conditions=0, the priority case falls to `default: err_code = NoError` instead of `err_code = SwInvalidConfig`.

The `err_valid` signal (line 842-844) already includes `invalid_config_atstart` as a legitimate error condition, but the `err_code` priority case never assigns the corresponding `SwInvalidConfig` value. This means SW sees `err_valid=1` (interrupt fires) but `err_code=NoError` — a contradictory and confusing error report that prevents proper error handling.

## Twin Repair

- Remove duplicate `hash_start_sha_disabled` case item (lines 856-858)
- Add `invalid_config_atstart: err_code = SwInvalidConfig` branch
- Oracle: `err_valid` already includes `invalid_config_atstart` (line 842-844); `prim_sha2_pkg` defines `SwInvalidConfig=6`; all other error conditions in the priority case have corresponding `err_code` branches.

## Reproduction

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-039
bash build.sh
```

## Raw Output

```
invalid_config_atstart=1, all others=0:
  vuln err_code: 0 (expect NoError=0)
  vuln_deviation: YES  twin_secure: YES
CONFIRMED: hmac.sv:846-876 err_code priority case has duplicate
hash_start_sha_disabled item (lines 851-858) and missing
invalid_config_atstart branch — when invalid_config_atstart=1
and all other error conditions=0, err_code stays NoError instead
of SwInvalidConfig. err_valid signal (line 842-844) already
includes invalid_config_atstart, confirming it is a real error.
Twin: remove duplicate, add invalid_config_atstart -> SwInvalidConfig.
exit code: 1 (1 = finding confirmed)
```

## Twin Diff Summary

- Line 856-858 (duplicate `hash_start_sha_disabled` branch): **removed**
- After `update_seckey_inprocess` branch (line 869-871): **added** `invalid_config_atstart: err_code = SwInvalidConfig;`
- Oracle: `err_valid` signal definition (line 842-844) and `prim_sha2_pkg::SwInvalidConfig` enum value
