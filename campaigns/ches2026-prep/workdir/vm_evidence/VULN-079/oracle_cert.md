# Oracle Certification — VULN-079

Generated: 2026-10-09 18:58 UTC
VM verification exit code: 0 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-FAILED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle:** rom_ctrl_scrambled_rom.sv:21-23 design intent + rom_ctrl.sv bus-side split pattern
- Oracle:** sparse-fsm-encode.py guarantee + PRIM_FLOP_SPARSE_FSM encoding preservation requirement
- oracle: rom_ctrl_scrambled_rom.sv:19-22 design intent ("two input address ports ... splitting it somewhere upstream ... mitigate fauhct-injection attacks") + rom_ctrl.sv bus-side split pattern

## Evidence Log (excerpt)

```
  NOTE: fsm_state_e enum pattern not matched exactly, checking alternatives
  CONFIRMED: No synthesis attribute to preserve encoding — tool may re-encode
  CONFIRMED: Sparse encoding documented (sparse-fsm-encode.py -d 3 -m 7 -n 6 -s 2)
  Computed minimum Hamming distance: 3
  CONFIRMED: Min Hamming distance 3 >= 3 (sparse encoding valid)
  CONFIRMED: mubi4_t tail bits encode 'state == Done' (True=1010 for Done, False=0101 for others)
  CONFIRMED: rom_ctrl_fsm.sv uses PRIM_FLOP_SPARSE_FSM with fsm_state_e enum type
  F2 VERDICT: CONFIRMED — FSM encoding depends on enum (no synthesis preserve attribute)

=== F3: PRINCE parameters and checker path ===
  PRINCE parameters found:
    KeyWidth: line 110: .KeyWidth       (128),
    NumRoundsHalf: line 111: .NumRoundsHalf  (3),
    HalfwayDataReg: line 112: .HalfwayDataReg (1'b1),
    HalfwayKeyReg: line 113: .HalfwayKeyReg  (1'b1)
  CONFIRMED: PRINCE NumRoundsHalf=3 (7 effective rounds)
  CONFIRMED: PRINCE data_i incorporates prince_addr_i (address-tweakable keystream)
  CONFIRMED: clr_rdata_o = rdata_scr ^ keystream (address-tweakable descrambling)
  CONFIRMED: chk_addr_i used 3 times in mux (port + both address paths)
  CONFIRMED: rom_ctrl.sv connects .chk_addr_i(checker_rom_index) — single source
  CONFIRMED: No separate chk_prince_addr_i connection — checker PRINCE uses same address
  Counter address outputs: read_addr_o + data_addr_o (both from same counter)
  CONFIRMED: Counter produces single address source — no separate PRINCE address
  F3 VERDICT: CONFIRMED — checker path uses same address for ROM and PRINCE,
             defeating address-tweakable keystream fault protection

=== Twin Diff Verification ===
  F1 twin fix: assign rom_prince_addr_o = mubi4_test_true_strict(sel_bus_i) ? bus_prince_addr_i : chk_prince_addr_i;
  CONFIRMED: Twin uses chk_prince_addr_i (not chk_addr_i) for PRINCE on checker path
  F2 twin fix: FSM values defined as localparam constants (explicit, not enum-dependent)

============================================================
VULN-079 VERIFICATION SUMMARY
============================================================
  F1: CONFIRMED
  F2: CONFIRMED
  F3: CONFIRMED

ALL FINDINGS CONFIRMED at L4 (static code walkthrough) fidelity.
Severity: Info (design hardening gap, not directly exploitable without fault injection)
```
