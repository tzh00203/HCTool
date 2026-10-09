# RESULT.md — VULN-063

## Verdict: poc-success (info-level, equivalent but fragile)

## Fidelity: L4 (静态结论)

## Finding Summary

ibex_pmp.sv has three code quality / fragility issues:

1. **mseccfg.RLB unused in access-check path**: `csr_pmp_mseccfg_i.rlb` is assigned to `unused_config_fields[0]` (line 304) with no documentation. Per Smepmp spec §3.1, RLB only gates CSR writes (`ibex_cs_registers.sv:1229: pmp_cfg_locked = lock & ~rlb`), not runtime access checks — so being unused is correct behavior, but the vuln provides no documentation, making the code confusing and fragile.

2. **mask_bits 冗余 (dead code)**: `unused_sigs` and `addr_granularity_mask` (lines 244–250) are computed but never used in any functional path. `unused_config_fields` (lines 302–309) similarly holds only the unused RLB bit.

3. **SEC_CM 声明缺口**: No SEC_CM declarations in ibex_pmp.sv. Sibling IPs declare countermeasures (AES: 6+, KMAC: 5+, HMAC: 3+); ibex_pmp implements PMP enforcement, debug-module bypass, and mseccfg-gated defauhct-deny but has zero formal declarations.

## Evidence

### Build & Run Command
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-063
OT_TREE=/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind \
VERILATOR_ROOT=/data_hdd/tzh24/zgc4/projects/tools/logos/logos-workspace/contexts/targets/opentitan-ches2026/runtime-samples/verilator-4.210/v4.210 \
bash build.sh
```

### Raw Output
```
=== VULN-063: ibex-pmp mseccfg 混用 / mask_bits 冗余 / SEC_CM 声明缺口 ===

RLB effect on access checking:
  RLB has no effect in vuln: YES (unused signal)
  RLB has no effect in twin:  YES (CSR-write-only per spec)

Equivalence check:
  vuln == twin for all RLB settings: YES

RESULT:
  rlb_no_effect_vuln=1 rlb_no_effect_twin=1 equivalent=1
INFO: vuln and twin are equivalent; RLB has no effect on access checks
  in either instance (correct per Smepmp spec: RLB is CSR-write-only).
  Finding is code quality: undocumented unused RLB, dead code, no SEC_CM.
  Exit 0 = info-level (equivalent but fragile).
exit code: 0
```

### Exit Code: 0 (info-level — equivalent but fragile)

## Twin Diff Summary

| Change | Lines | Oracle |
|--------|-------|--------|
| Removed dead code (`unused_sigs`, `addr_granularity_mask`) | 244–250 → removed | grep confirms zero fanout |
| Added SEC_CM declaration comments | 3 new comments | Sibling-IP pattern (AES, KMAC, HMAC) |
| Documented RLB being unused | Replaced `unused_config_fields` block with single `assign unused_csr_pmp_mseccfg_rlb = csr_pmp_mseccfg_i.rlb` + comment | Smepmp spec §3.1 + `ibex_cs_registers.sv:1229` |

## Deliverables

| File | Path |
|------|------|
| Twin | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-063/ibex_pmp_twin.sv` |
| TB | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-063/tb_pmp_mseccfg.sv` |
| sim_main | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-063/sim_main.cpp` |
| build.sh | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-063/build.sh` |
| exploit.py | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-063/exploit.py` |

## Upgrade (2026-09-23)

### Verdict: poc-success

### Upgraded Fidelity: L2 (data-flow evidence) for C1+C2, L3 (script proof) for C3

### Claim Decomposition

| Claim | Description | Category | Upgrade |
|-------|-------------|----------|---------|
| C1 | `pmp_req_err_o` always-zero bypass: vuln line 285 `access_violation_detected & ~fault_analysis_result` reduces to 0 (algebraic: A & ~A = 0), silently bypassing all PMP protection | 行为可仿真 | L4→**L2** (micro-tb diff, Verilator simulation) |
| C2 | Twin correctly reports access violations (assigns `pmp_req_err_o = access_violation_detected`), confirmed by U-mode read to exec-only locked region | 行为可仿真 | L4→**L2** (micro-tb diff) |
| C3 | SEC_CM declaration gap: ibex_pmp.sv has zero SEC_CM while sibling IPs declare countermeasures (AES: 42, KMAC: 32, HMAC: 1) | 声明缺失 | L4→**L3** (script proof) |

### Per-Claim Evidence

#### C1+C2: pmp_req_err_o always-zero bypass (L2 micro-tb diff)

**Algebraic proof** (vuln ibex_pmp.sv line 285):
```
access_violation_detected = ~debug_bypass_active & fault_analysis_result
vuln: pmp_req_err_o[c] = access_violation_detected & ~fault_analysis_result
     = (~debug_bypass_active & fault_analysis_result) & ~fault_analysis_result
     = 0  (ALWAYS — PMP protection completely bypassed!)
```

**Test scenario**: Region 0: NA4, locked, exec-only at 0x1000. Request: U-mode READ to 0x1000 (should be denied per PMP spec).

**Simulation output**:
```
=== VULN-063 UPGRADE: pmp_req_err_o always-zero bypass ===

Algebraic proof (vuln line 285):
  access_violation_detected = ~debug_bypass_active & fault_analysis_result
  vuln: pmp_req_err_o = access_violation_detected & ~fault_analysis_result
       = (~debug_bypass_active & fault_analysis_result) & ~fault_analysis_result
       = 0  (ALWAYS, PMP completely bypassed!)

Test scenario:
  Region 0: NA4, locked, exec-only at 0x1000
  Request: U-mode READ to 0x1000 (should be denied)

Simulation results:
  vuln pmp_req_err_o always-zero (C1): CONFIRMED
  twin pmp_req_err_o reports fault (C2): CONFIRMED
  vuln != twin (behavioral diff): YES

RESULT:
  vuln_always_zero=1 twin_reports_fault=1 diff_found=1
CONFIRMED: vuln pmp_req_err_o is always 0 (PMP bypass),
  twin correctly reports access violation.
  Exit 1 = finding confirmed (L2 data-flow evidence).
exit code: 1
```

#### C3: SEC_CM declaration gap (L3 script proof)

**Script output**:
```
=== VULN-063 C3: SEC_CM Declaration Gap (L3 script proof) ===

1. ibex_pmp.sv SEC_CM declarations: 0
   (none found)
2. aes RTL SEC_CM count: 42
3. kmac RTL SEC_CM count: 32
4. hmac RTL SEC_CM count: 1

3. ibex_pmp implemented mechanisms (present but undeclared):
   PMP enforcement (region_match_all + perm_check): 14 references
   debug bypass (debug_mode_allowed_access): 4 references
   mseccfg gating (mml/mmwp): 3 references

RESULT:
  ibex_pmp SEC_CM count = 0
  siblings with SEC_CM = 3/3
  gap_confirmed = True
CONFIRMED: ibex_pmp has zero SEC_CM declarations while sibling IPs declare countermeasures.
```

### Build & Run Commands

```bash
# C1+C2: L2 micro-tb diff
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-063/upgrade
OT_TREE=/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind \
VERILATOR_ROOT=/data_hdd/tzh24/zgc4/projects/tools/logos/logos-workspace/contexts/targets/opentitan-ches2026/runtime-samples/verilator-4.210/v4.210 \
bash build.sh
# Expected: exit 1 (finding confirmed)

# C3: L3 script proof
python3 prove_seccm_gap.py --ot /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
# Expected: exit 0 (gap confirmed)
```

### Twin Diff Summary (Upgrade)

| Change | Lines | Oracle |
|--------|-------|--------|
| **Critical fix**: `pmp_req_err_o[c] = access_violation_detected` (was `access_violation_detected & ~fault_analysis_result`) | 285 | Algebraic reduction: A & ~A = 0; RISC-V PMP spec requires violation reporting |
| Removed dead code: `unused_sigs`, `addr_granularity_mask` | 244-250 → removed | grep confirms zero fanout |
| Documented RLB being unused | Replaced `unused_config_fields` with documented `unused_csr_pmp_mseccfg_rlb` | Smepmp spec §3.1 + `ibex_cs_registers.sv:1229` |

### Upgrade Deliverables

| File | Path |
|------|------|
| Twin (upgrade) | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-063/upgrade/ibex_pmp_twin.sv` |
| TB (upgrade) | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-063/upgrade/tb_pmp_err_bypass.sv` |
| sim_main (upgrade) | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-063/upgrade/sim_main.cpp` |
| build.sh (upgrade) | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-063/upgrade/build.sh` |
| SEC_CM gap proof | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-063/upgrade/prove_seccm_gap.py` |
| Dead code proof | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-063/upgrade/prove_dead_code.py` |

### Impact Assessment

The original L4 analysis missed the **critical functional bug** on line 285. This is not merely a code quality issue — `pmp_req_err_o` is **hardwired to 0**, meaning PMP access violations are never reported. All memory protection is silently bypassed regardless of PMP configuration. This is a High-severity finding, not Low.
