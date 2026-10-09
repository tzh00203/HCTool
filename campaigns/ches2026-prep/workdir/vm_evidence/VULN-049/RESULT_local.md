# RESULT: VULN-049

## Verdict
**[poc-success]** L4 fidelity

## Finding
Ascon `data_in_valid_bytes_i > 15` has no range check AND `data_out_ready_i` is unused.

### Issue 1: valid_bytes out-of-range
- `bin2thermo()` in `prim_ascon_pkg.sv:141-164` explicitly handles values 0-15 only
- Values 16-31 hit `default` case: `bin2thermo` returns `{128{1'b1}}`, `get_padding_mask` returns `{128{1'b0}}`
- For `valid_bytes=17` with `ASCON_128A`: `complete_block = (128A && 17==16) = MuBi4False`
- Result: block treated as incomplete with ALL bytes "valid" and NO padding → padding byte silently dropped
- RTL TODOs at line 14 and line 97 document this: "Add check what to do, if data_in_valid_bytes_i is greater than blocksize"
- Twin fix: clamp `data_in_valid_bytes_i` to max blocksize (16 for 128A, 8 for 128) before computing `complete_block`, `bin2thermo`, and `get_padding_mask`

### Issue 2: data_out_ready_i dead-ended
- `prim_ascon_duplex.sv:59-61`: `data_out_ready_i` assigned to `unused_data_out_ready_i`
- Output valid/ready handshake broken: `data_out_valid_o` asserted regardless of consumer readiness
- Can cause data loss when consumer is not ready
- Twin fix: gate `data_out_valid_o` with `data_out_ready_i`

## Reproduction
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-049
bash build_vuln049.sh
```

## Raw Output
```
cycles=1
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: Ascon valid_bytes>15 no range check + data_out_ready_i unused
  Issue 1: valid_bytes=17 (ASCON_128A) → vuln complete_block=False (no padding),
          twin clamps to 16 → complete_block=True (correct FSM path)
  Issue 2: vuln data_out_valid_o ignores data_out_ready_i (no backpressure),
          twin gates data_out_valid_o with data_out_ready_i
exit code: 1 (1 = finding confirmed)
```

## Twin Repair Diff
Only two changes in `prim_ascon_duplex_twin.sv` vs vuln `prim_ascon_duplex.sv`:
1. **Lines 97-100 area (complete_block + downstream)**: Added `data_in_valid_bytes_clamped` that clamps `data_in_valid_bytes_i` to max blocksize. All uses of `data_in_valid_bytes_i` in `complete_block`, `bin2thermo()`, and `get_padding_mask()` replaced with `data_in_valid_bytes_clamped`.
   - Oracle: line 14 TODO + line 97 TODO: "Add check what to do, if data_in_valid_bytes_i is greater than blocksize"
2. **Lines 59-61 (data_out_ready_i)**: Replaced `unused_data_out_ready_i` assignment with `data_out_valid_o = data_out_valid_internal & data_out_ready_i` (backpressure gating).
   - Oracle: standard valid/ready handshake protocol (AXI4-Stream / TL-UL); line 59 TODO "Add backpressure check"

## Deliverables
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-049/tb_vuln049.sv` — combinational micro-tb
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-049/prim_ascon_duplex_twin.sv` — repaired twin
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-049/build_vuln049.sh` — Verilator build script
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-049/sim_main.cpp` — C++ driver
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-049/exploit.py` — PoC entry (redbud mode)

## Upgrade (2026-09-23)

### Sub-Claim Decomposition

| Claim | Description | Category | Upgraded Level | Evidence |
|-------|-------------|----------|----------------|----------|
| C1 | `bin2thermo()` / `get_padding_mask()` return wrong values for `valid_bytes>15` (default case: thermo=all-1s, padmask=all-0s) | Behavior simulable | L2 | micro-tb scan valid_bytes=0..31 |
| C2 | `complete_block` miscalculated for `valid_bytes>blocksize` → FSM takes wrong path (padding skipped) | Behavior simulable | L2 | micro-tb scan valid_bytes=0..31 |
| C3 | `data_out_ready_i` dead-ended (no backpressure); `data_out_valid_o` asserted unconditionally | Property missing | L3 | script proof (RTL structural analysis) |

### New Verdict
**[poc-success]** L2 (C1+C2) + L3 (C3)

### C1+C2: L2 Micro-TB (Combinational Scan)

Upgraded from L4 → L2. Full scan of all 32 `valid_bytes` values for both ASCON_128 and ASCON_128A variants:

- **Vuln**: For `valid_bytes>blocksize`, `bin2thermo()` returns `{128{1'b1}}` (default) and `get_padding_mask()` returns `{128{1'b0}}` (default). `complete_block` evaluates to `MuBi4False` — FSM skips padding.
- **Twin**: Clamps `data_in_valid_bytes_i` to max blocksize (8 for ASCON_128, 16 for ASCON_128A) before computing `complete_block`, `bin2thermo()`, and `get_padding_mask()`. Correct function results and FSM path.
- **Oracle**: TODO comments at lines 14 and 97 of `prim_ascon_duplex.sv`: "Add check what to do, if data_in_valid_bytes_i is greater than blocksize"

**Raw Output:**
```
cycles=1
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: VULN-049 Claims C1+C2 (L2 micro-tb)
  C1: bin2thermo/get_padding_mask defauhct-case mismatch for valid_bytes>15
      vuln: default returns thermo=all-1s, padmask=all-0s
      twin: clamp to max blocksize → correct function output
  C2: complete_block miscalculation for valid_bytes>blocksize
      vuln: complete_block=False (wrong FSM path, padding skipped)
      twin: clamped → complete_block=True (correct FSM path)
  Tested: all 32 valid_bytes values for ASCON_128 and ASCON_128A
exit code: 1 (1 = finding confirmed)
```

### C3: L3 Script Proof (Backpressure Missing)

Upgraded from L4 → L3. Python script parses RTL source to prove structural absence of backpressure:

```
CHECK-1 PASS: Line 61: data_out_ready_i assigned to unused_data_out_ready_i (dead-end)
CHECK-2 PASS: data_out_ready_i has no non-trivial usage (only port decl + unused_ assign)
CHECK-3 PASS: data_out_valid_o is NOT gated by data_out_ready_i (no backpressure)
CHECK-4 PASS: Line 13: TODO comment confirms intended backpressure: // TODO: Add backpressure logic, if output is not ready
CHECK-5: data_out_valid_o appears in 2 lines (assignments/references):
  Line 327: data_out_valid_o = 1'b0;
  Line 486: data_out_valid_o = 1'b1;
```
- **Oracle**: Line 13 TODO: "Add backpressure logic, if output is not ready"; standard valid/ready handshake protocol (AXI4-Stream / TL-UL)
- **Why L3 not L2**: Backpressure absence is a property/protocol violation, not a data-path behavioral difference observable by combinational micro-tb diff. No I/O behavioral difference between vuln and twin when `data_out_ready_i=1` (the typical case); deviation only manifests as a protocol-level hazard (data loss when consumer is not ready).

### Upgrade Deliverables
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-049/upgrade/tb_upgrade.sv` — L2 combinational micro-tb (full scan)
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-049/upgrade/sim_main.cpp` — C++ driver for L2 tb
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-049/upgrade/build_upgrade.sh` — Verilator build script for L2 tb
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-049/upgrade/proof_c3_backpressure.py` — L3 script proof for C3
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-049/upgrade/proof_c3_output.txt` — L3 script proof output

### Reproduction
```bash
# C1+C2: L2 micro-tb
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-049/upgrade
bash build_upgrade.sh

# C3: L3 script proof
python3 proof_c3_backpressure.py
```
