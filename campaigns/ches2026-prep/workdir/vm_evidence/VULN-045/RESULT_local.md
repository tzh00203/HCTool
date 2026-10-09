# VULN-045 Verification Result

## Verdict: **[poc-success]** — finding confirmed

## Summary
Ascon ascon_core.sv has 4 register fields completely dead-ended to `unused_` variables — SW can write these bits but they have zero functional effect:

1. **sideload_key** (line 134-135): `assign unused_sideload_key = sideload_key;` — key always comes from register shares, keymgr key input completely ignored. Comment: "TODO Add sideload interface". Also `unused_keymgr_key_i = keymgr_key_i` (entire keymgr interface dead).
2. **masked_msg_input / masked_ad_input** (line 140-143): `assign unused_masked_msg_input = masked_msg_input;` and `assign unused_masked_ad_input = masked_ad_input;` — always requires both shares regardless of masking setting. Comment: "TODO Add logic to provide inputs unmasked".
3. **manual_start_trigger** (line 312-313): `assign unused_manual_start_trigger = manual_start_trigger;` — manual start trigger has no effect on operation start. Comment: "TODO Add manual mode for SCA".
4. **force_data_overwrite** (line 315-317): `assign unused_force_data_overwrite = force_data_overwrite;` — output overwrite has no effect. Comment: "TODO Add output overwrite".

## Verification Method
- **TB type**: combinational micro-tb (tb_comb)
- **Fidelity**: L2 (data-flow evidence)
- **Approach**: Copy the 4 vuln expressions (signal dead-ended) and 4 twin expressions (signal consumed per sibling-module pattern) into tb, drive non-default input values, compare vuln vs twin output.

### Twin repair basis (per signal):
| Signal | Twin behavior | Oracle |
|--------|--------------|--------|
| sideload_key | `sideload_key ? key_from_keymgr : key_from_regs` | AES aes_core.sv sideload_key gates key mux |
| masked_msg_input | `masked ? (s0_new & s1_new) : s0_new` | KMAC masked_input gates share requirement |
| manual_start_trigger | `(start \| manual_start_trigger) & ~key_error` | KMAC manual_start_trigger extends start condition |
| force_data_overwrite | `valid & (ready \| force_data_overwrite)` | AES FORCE_MASKS pattern overrides ready gate |

## Execution Evidence

### Build command
```bash
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-045/build_ascon_unused_signals.sh
```

### Raw output
```
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: ascon_core.sv 4 register fields dead-ended to unused_ variables:
  (1) sideload_key (line 134-135): key always from registers, keymgr key ignored
  (2) masked_msg_input/masked_ad_input (line 140-143): always requires both shares
  (3) manual_start_trigger (line 312-313): manual start has no effect
  (4) force_data_overwrite (line 315-317): output overwrite has no effect
  Twin consumes each signal into observable output per sibling-module pattern.
exit code: 1 (1 = finding confirmed)
```

### Exit code: 1 = finding confirmed

## Deliverables
| File | Path |
|------|------|
| tb | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-045/tb_ascon_unused_signals.sv` |
| sim_main.cpp | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-045/sim_main.cpp` |
| build.sh | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-045/build_ascon_unused_signals.sh` |
| exploit.py | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-045/exploit.py` |
