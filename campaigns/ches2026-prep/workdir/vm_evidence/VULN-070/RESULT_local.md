# RESULT: VULN-070

## Verdict: `[poc-success]` — L2 fidelity

## Finding

lc_ctrl_fsm.sv: lc_check_byp_en unconditionally set to On in ClkMuxSt (line 368),
even for non-bypass-eligible states (PROD, PROD_END, DEV). Additionally:
- No SEC_CM declaration for lc_check_byp_en_o (CHECK_BYP.SIGNAL.REDUN missing)
- volatile_raw_unlock_i effectively unused when SecVolatileRawUnlockEn=0 (production default)
- No SEC_CM declaration for volatile unlock mechanism

## Evidence

### Behavioral difference (comb micro-tb)

| Condition | vuln lc_check_byp_en | twin lc_check_byp_en |
|---|---|---|
| ClkMuxSt + lc_state in bypass-eligible set | On | On |
| ClkMuxSt + lc_state NOT in bypass-eligible set (PROD/PROD_END/DEV) | **On** (incorrect) | **Off** (correct) |

### SEC_CM declaration audit

RTL SEC_CM declarations in lc_ctrl_fsm.sv (9 found):
- MAIN.CTRL_FLOW.CONSISTENCY (line 203)
- TOKEN.DIGEST (lines 447, 484, 674)
- MAIN.FSM.GLOBAL_ESC (line 570)
- MAIN.FSM.LOCAL_ESC (line 573)
- TOKEN_MUX.CTRL.REDUN (line 662)
- TOKEN_VALID.MUX.REDUN (line 710)
- STATE.CONFIG.SPARSE (line 733)

**Missing** (0 found):
- CHECK_BYP.SIGNAL.REDUN for lc_check_byp_en_o
- VOLATILE_UNLOCK.CONFIG.REDUN for volatile_raw_unlock_i

hjson sec_cm_testplan has 17 countermeasures — none cover CHECK_BYP or VOLATILE_UNLOCK.

### volatile_raw_unlock unused path

When SecVolatileRawUnlockEn=0 (production default):
- `volatile_raw_unlock_i` input (line 48): consumed only under `SecVolatileRawUnlockEn &&` guard (line 295) — always false
- `set_strap_en_override` (line 233): consumed only in gen_strap_delay_regs block (line 605) — not generated
- `volatile_raw_unlock_success_d` (line 234): consumed as unused_sigs XOR (line 627-628) — dead-end
- No SEC_CM: VOLATILE_UNLOCK.CONFIG.REDUN declaration

## Twin Repair

Only change: ClkMuxSt lc_check_byp_en assignment (line 368)

**Vuln (line 368):**
```systemverilog
lc_check_byp_en = On;  // unconditional
```

**Twin:**
```systemverilog
if (lc_state_q inside {LcStRaw, LcStTestLocked0-6,
                       LcStTestUnlocked0-7, LcStRma}) begin
  lc_check_byp_en = On;  // gated — only for bypass-eligible states
end
```

Plus added SEC_CM declarations:
- `// SEC_CM: CHECK_BYP.SIGNAL.REDUN` (for lc_check_byp_en_o)
- `// SEC_CM: VOLATILE_UNLOCK.CONFIG.REDUN` (for volatile_raw_unlock_i path)

Oracle: SVA NoClkBypInProdStates_A (line 860-863) constrains lc_clk_byp_req in PROD/PROD_END/DEV;
ClkMuxSt inside-set (lines 369-385) explicitly excludes PROD/PROD_END/DEV from clock bypass.

## Reproduction

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-070
export VERILATOR_ROOT=/data_hdd/tzh24/zgc4/projects/tools/logos/logo-workspace/contexts/targets/opentitan-ches2026/runtime-samples/verilator-4.210/v4.210
bash build_lc_check_byp_en.sh
```

## Raw Output

```
cycles=1
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: lc_check_byp_en unconditionally On in ClkMuxSt
  vuln: lc_check_byp_en=On even for non-bypass-eligible states (PROD/PROD_END/DEV)
  twin: lc_check_byp_en gated by bypass-eligible set; Off for PROD/PROD_END/DEV
  oracle: SVA NoClkBypInProdStates_A + ClkMuxSt inside-set (lines 369-385)
  SEC_CM gap: no CHECK_BYP.SIGNAL.REDUN declaration for lc_check_byp_en_o
exit code: 1 (1 = finding confirmed)
```

## Deliverables

| File | Description |
|---|---|
| tb_lc_check_byp_en.sv | Comb micro-tb (vuln vs twin expression comparison) |
| lc_ctrl_fsm_twin.sv | Twin module (lc_check_byp_en gated + SEC_CM declarations added) |
| sim_main.cpp | C++ simulation driver |
| build_lc_check_byp_en.sh | Verilator build script |
| exploit.py | PoC entry (redbud mode) |
| RESULT.md | This file |
