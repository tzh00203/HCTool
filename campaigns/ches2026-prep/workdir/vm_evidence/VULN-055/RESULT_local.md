# RESULT: VULN-055

## Verdict: [poc-success]

alert_threshold_fail dual-path boundary asymmetry — at threshold=0, the INV path guard (`~alert_threshold_inv != '0`) can pass while the direct path guard (`alert_threshold != '0`) fails, breaking SEC_CM: CONFIG.REDUN symmetry.

## Fidelity: L2 (combinational micro-tb)

## Vulnerability Detail

**File**: `entropy_src_core.sv:2184-2186`

**Vuln expression**:
```systemverilog
assign alert_threshold_fail =
       ((any_fail_count >= ~alert_threshold_inv) && (~alert_threshold_inv != '0)) ||
       (any_fail_count >= alert_threshold) && (alert_threshold != '0);
```

**Problem**: The two redundant paths use **different guards**:
- INV path guard: `~alert_threshold_inv != '0`
- Direct path guard: `alert_threshold != '0`

When `alert_threshold = 0` and `alert_threshold_inv` is inconsistent (e.g., `inv = 0`):
- `~alert_threshold_inv = 0xFFFF` → INV guard passes → INV path **can fire**
- `alert_threshold = 0` → Direct guard fails → Direct path **disabled**

This creates an asymmetric behavior at the threshold=0 boundary: one path fires an alert while the other doesn't, defeating the redundancy countermeasure.

**Twin fix**: Use `alert_threshold != '0` as the consistent guard for both paths:
```systemverilog
assign alert_threshold_fail =
       ((any_fail_count >= ~alert_threshold_inv) && (alert_threshold != '0)) ||
       ((any_fail_count >= alert_threshold) && (alert_threshold != '0));
```

**Oracle**: SEC_CM: CONFIG.REDUN comment at line 2179. When `alert_threshold = 0`, alerting is disabled, so BOTH paths must be off. The guard should be consistent across both paths.

## Test Vector

| any_fail_count | alert_threshold | alert_threshold_inv | vuln | twin | expected |
|---|---|---|---|---|---|
| 0xFFFF | 0x0000 | 0x0000 | 1 (INV fires) | 0 (both off) | 0 |

## Build & Run

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-055
bash build.sh
# exit code: 1 = finding confirmed
```

## Raw Output

```
cycles=1
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: alert_threshold_fail dual-path boundary asymmetry
  vuln: with threshold=0, inv=0 (inconsistent), INV path fires (guard: ~inv!=0 passes)
        but direct path disabled (guard: thresh!=0 fails) → alert_threshold_fail=1
  twin: both paths gated by alert_threshold!=0 → consistently 0 when threshold=0
  oracle: SEC_CM: CONFIG.REDUN requires symmetric dual-path; threshold=0 means disabled
exit code: 1 (1 = finding confirmed)
```

## Deliverables

- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-055/tb_alert_thresh.sv` — combinational micro-tb
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-055/sim_main.cpp` — C++ driver
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-055/build.sh` — Verilator build script
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-055/exploit.py` — PoC entry (redbud mode)
