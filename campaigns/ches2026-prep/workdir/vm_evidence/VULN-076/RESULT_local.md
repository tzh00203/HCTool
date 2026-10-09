# RESULT: VULN-076

## Verdict: [poc-success] L4 fidelity

## Finding

otp_ctrl_part_buf.sv:601-606: `ecc_err` block transitions FSM to ErrorSt and sets `error_d = CheckFailError`, but does **not** set `fsm_err_o = 1'b1`. In contrast, the `escalate_en_i / cnt_err` block (lines 608-614) also transitions to ErrorSt and **does** set `fsm_err_o = 1'b1`. Both blocks carry the same `SEC_CM: PART.FSM.LOCAL_ESC` annotation, creating a behavioral inconsistency: the ECC error path's LOCAL_ESC countermeasure is incomplete.

The in-tree SVA `EccErrorState_A` (line 812-815) only checks `ecc_err |=> state_q == ErrorSt` — it does not verify `fsm_err_o`, leaving the fsm_err_o gap undetected (assertion 漏检).

## Twin Repair

Diff (only the ecc_err override block):
```diff
     // SEC_CM: PART.FSM.LOCAL_ESC
     if (ecc_err) begin
       state_d = ErrorSt;
+      fsm_err_o = 1'b1;  // oracle: cnt_err/escalate paths set fsm_err_o=1
       if (state_q != ErrorSt) begin
         error_d = CheckFailError;
       end
     end
```
Oracle:
- `cnt_err` path (line 610): counter integrity error sets `fsm_err_o = 1'b1` — not an FSM glitch, same category as ecc_err
- `escalate_en_i` path (line 610): external escalation sets `fsm_err_o = 1'b1`
- Both carry `SEC_CM: PART.FSM.LOCAL_ESC` — same annotation should imply same behavior
- SVA `EccErrorState_A` only checks `state_q == ErrorSt`, not `fsm_err_o` → assertion gap

## Evidence
- Fidelity: L4 (static oracle comparison — code consistency analysis, no full module dynamic simulation)
- Test: ecc_err=1 with escalate_en=Off and cnt_err=0
- vuln: state_d=ErrorSt, fsm_err_o=0 (ecc_err block doesn't set it)
- twin: state_d=ErrorSt, fsm_err_o=1 (consistent with cnt_err/escalate paths)
- Reference: cnt_err path fsm_err_o=1, escalate path fsm_err_o=1 (both confirmed in vuln)
- Differential output: confirmed

## Commands
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-076
bash build_part_buf_ecc_fsm_err.sh
```

## Raw Output
```
ecc_err=1: vuln fsm_err_o=0  twin fsm_err_o=1
reference: vuln escalate fsm_err_o=1  vuln cnt_err_fsm_err_o=1
CONFIRMED: otp_ctrl_part_buf.sv:601-606 ecc_err->ErrorSt doesn't set fsm_err_o
  vuln: ecc_err block fsm_err_o=0 (inconsistent with cnt_err/escalate paths)
  twin: ecc_err block fsm_err_o=1 (oracle: cnt_err/escalate set fsm_err_o=1
        under same SEC_CM: PART.FSM.LOCAL_ESC; SVA EccErrorState_A only checks
        state_q==ErrorSt, not fsm_err_o — assertion gap (漏检))
exit code: 1 (1 = finding confirmed)
```

## Deliverables

| File | Description |
|---|---|
| tb_part_buf_ecc_fsm_err.sv | Combinational micro-tb: injects ecc_err=1, checks fsm_err_o differential |
| otp_ctrl_part_buf_twin.sv | Twin with fsm_err_o=1 in ecc_err block |
| sim_main.cpp | C++ driver |
| build_part_buf_ecc_fsm_err.sh | Verilator 4.210 build script |
| exploit.py | PoC entry (redbud mode) |

---

## Upgrade (2026-09-23)

### Verdict: [poc-success] L2 (Claim A+B) + L3 (Claim C)

### Claim Decomposition

| Claim | Type | Upgraded Level | Description |
|---|---|---|---|
| A | 行为可仿真 | L2 | ecc_err=1 → fsm_err_o=0 (vuln) vs fsm_err_o=1 (twin) — micro-tb differential, 8-combo exhaustive scan |
| B | 行为可仿真 | L2 | escalate_en_i / cnt_err paths correctly set fsm_err_o=1 in both vuln and twin — reference check |
| C | 声明缺失 | L3 | EccErrorState_A only checks state_q==ErrorSt, not fsm_err_o (assertion 漏检); no SVA in part_buf checks fsm_err_o; hjson PART.FSM.LOCAL_ESC incomplete; sibling part_unbuf has same gap |

### Evidence

**Claim A + B (L2 micro-tb differential):**
- Fidelity: L2 (组合 micro-tb, Verilator 仿真确认)
- Oracle: cnt_err path (line 610) sets fsm_err_o=1; escalate_en_i path (line 610) sets fsm_err_o=1; both under SEC_CM: PART.FSM.LOCAL_ESC
- Scan: all 8 combinations of {ecc_err, escalate_en(On/Off), cnt_err} verified
- Key result: ecc_err=1, escalate=Off, cnt_err=0 → vuln fsm_err_o=0, twin fsm_err_o=1 (CONFIRMED)

**Claim C (L3 script proof):**
- C.1: EccErrorState_A = `ecc_err |=> state_q == ErrorSt` — no fsm_err_o check (PASS)
- C.2: None of 35 SVAs in otp_ctrl_part_buf reference fsm_err_o (PASS)
- C.3: hjson PART.FSM.LOCAL_ESC declares "FSMs moved into invalid state" but doesn't specify fsm_err_o requirement; ecc_err path omits fsm_err_o → incomplete LOCAL_ESC (PASS)
- C.4: Sibling otp_ctrl_part_unbuf has identical gap: ecc_err block (line 320-324) doesn't set fsm_err_o, EccErrorState_A same pattern (PASS)

### Commands
```bash
# L2 micro-tb (Claim A + B):
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-076/upgrade
bash build_upgrade.sh

# L3 script proof (Claim C):
python3 claim_c_assertion_gap.py
```

### Raw Output (L2 micro-tb)
```
=== VULN-076 Upgrade: Claim A + Claim B + 8-combo scan ===
Claim A (ecc_err differential): PASS
Claim B (escalate/cnt_err reference): PASS
CONFIRMED: all claims pass
  Claim A: ecc_err=1 → vuln fsm_err_o=0, twin fsm_err_o=1 (L2 micro-tb diff)
  Claim B: escalate/cnt_err → both vuln and twin fsm_err_o=1 (L2 reference)
  Full scan: all 8 combos verified
exit code: 1 (1 = finding confirmed)
```

### Raw Output (L3 script proof)
```
============================================================
VULN-076 Claim C: Assertion gap + SEC_CM declaration analysis
============================================================

--- C.1: EccErrorState_A does not check fsm_err_o ---
  EccErrorState_A text:
    `ASSERT(EccErrorState_A,
      ecc_err
      |=>
      state_q == ErrorSt)
  References fsm_err_o: False
  References state_q==ErrorSt: True

--- C.2: No SVA in otp_ctrl_part_buf checks fsm_err_o ---
  Total SVAs in otp_ctrl_part_buf: 35
  Any SVA references fsm_err_o: False

--- C.3: hjson PART.FSM.LOCAL_ESC declaration gap ---
  PART.FSM.LOCAL_ESC in hjson: True
  Description says 'invalid state' but doesn't specify fsm_err_o

--- C.4: Sibling otp_ctrl_part_unbuf has same gap ---
  ecc_err block sets fsm_err_o: False
  escalate block sets fsm_err_o: True
  EccErrorState_A checks fsm_err_o: False

============================================================
Claim C verdict: CONFIRMED
  C.1 EccErrorState_A lacks fsm_err_o check: PASS
  C.2 No SVA in part_buf checks fsm_err_o:   PASS
  C.3 hjson SEC_CM declaration gap:           PASS
  C.4 Sibling part_unbuf same gap:            PASS
============================================================
exit code: 1 (1 = confirmed)
```

### Upgrade Deliverables

| File | Description |
|---|---|
| upgrade/tb_ecc_fsm_err_upgrade.sv | L2 micro-tb: Claim A (ecc_err diff) + Claim B (escalate/cnt_err ref) + 8-combo scan |
| upgrade/otp_ctrl_part_buf_twin.sv | Twin with fsm_err_o=1 in ecc_err block |
| upgrade/sim_main.cpp | C++ driver for upgrade tb |
| upgrade/build_upgrade.sh | Verilator 4.210 build script (perl invocation) |
| upgrade/claim_c_assertion_gap.py | L3 script proof: EccErrorState_A gap + hjson SEC_CM gap + sibling pattern |
| upgrade/exploit.py | PoC entry (redbud mode) |
