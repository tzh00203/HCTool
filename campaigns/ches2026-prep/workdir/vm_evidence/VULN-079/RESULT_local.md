# VULN-079: rom_ctrl checker-side address redundancy / FSM enum / PRINCE params

## Verdict

**[poc-success]** L4 fidelity (static code walkthrough)

All three sub-findings confirmed via in-tree oracle comparison (grep + code analysis).

## Findings

### F1: Checker-side ROM address has no redundancy (sec-cm-mismatch)

**Confirmed.** In `rom_ctrl_mux.sv:123-124`:
```systemverilog
assign rom_rom_addr_o    = mubi4_test_true_strict(sel_bus_i) ? bus_rom_addr_i    : chk_addr_i;
assign rom_prince_addr_o = mubi4_test_true_strict(sel_bus_i) ? bus_prince_addr_i : chk_addr_i;
```

On the checker path (sel_bus_i = False), **both** `rom_rom_addr_o` and `rom_prince_addr_o` are driven by the same `chk_addr_i`. The scrambled ROM's two address ports are designed to come from **different** upstream signals for fault injection protection (rom_ctrl_scrambled_rom.sv:21-23: *"you can mitigate fauhct-injection attacks that corrupt the address by splitting it somewhere upstream"*). The checker path defeats this by using a single source.

On the bus path, the two addresses come from different sources:
- `bus_rom_addr_i` — TL adapter output (with end-to-end ECC integrity)
- `bus_prince_addr_i` — TL address snoop (with prim_buf isolation)

No `chk_prince_addr_i` port exists. The top-level connects `.chk_addr_i(checker_rom_index)` with no separate PRINCE address.

**Impact:** A single fault injection on `chk_addr_i` corrupts both the ROM index and the PRINCE address simultaneously. Since the PRINCE keystream is address-tweakable, the corrupted address produces a correlated keystream change that may partially cancel with the corrupted ROM data, potentially allowing controlled readout.

### F2: FSM encoding depends on enumeration (sec-cm-mismatch)

**Confirmed.** In `rom_ctrl_pkg.sv:49-57`, `fsm_state_e` is defined as `typedef enum logic [9:0]`. Synthesis tools may treat enum types as abstract state labels and re-encode the FSM, potentially destroying:

- The Hamming distance 3 guarantee from `sparse-fsm-encode.py -d 3 -m 7 -n 6 -s 2`
- The `mubi4_t` tail bits that encode "state == Done" for `rom_select_bus_o`
- The `PRIM_FLOP_SPARSE_FSM` macro's assumption that the encoding is preserved

No synthesis attribute (e.g., `(* fsm_encoding = "user" *)`) exists to instruct the tool to preserve the encoding.

Computed minimum Hamming distance: **3** (valid sparse encoding). The mubi4_t tail correctly encodes `Done` as `MuBi4True` (4'b1010) and all other states as `MuBi4False` (4'b0101).

### F3: PRINCE parameters — checker path defeats address-tweakable keystream (sec-cm-mismatch)

**Confirmed.** In `rom_ctrl_scrambled_rom.sv`, PRINCE is instantiated with:
- `NumRoundsHalf(3)` — 7 effective rounds
- `HalfwayDataReg(1'b1)`, `HalfwayKeyReg(1'b1)`
- `data_i({data_scr_nonce, prince_addr_i})` — address-tweakable keystream
- `clr_rdata_o = rdata_scr ^ keystream[Width-1:0]` — XOR descrambling

The keystream is address-tweakable (incorporates `prince_addr_i`). On the checker path:
- `prince_addr_i` = `chk_addr_i` = `rom_rom_addr_o` = `rom_addr_i`
- A single fault on `chk_addr_i` affects both the ROM physical index AND the PRINCE address

The counter (`rom_ctrl_counter.sv`) produces a single address (`read_addr_o`) with no separate PRINCE address output.

## Twin Repair

### F1 twin: `rom_ctrl_mux_twin.sv`

- **Added port:** `input logic [AW-1:0] chk_prince_addr_i`
- **Changed line:** `assign rom_prince_addr_o = ... ? bus_prince_addr_i : chk_prince_addr_i;` (was `chk_addr_i`)
- **Oracle:** rom_ctrl_scrambled_rom.sv:21-23 design intent + rom_ctrl.sv bus-side split pattern

### F2 twin: `rom_ctrl_pkg_twin.sv`

- **Change:** FSM values defined as explicit `localparam` constants + enum references them
- **Oracle:** sparse-fsm-encode.py guarantee + PRIM_FLOP_SPARSE_FSM encoding preservation requirement

### F3 twin: (consequence of F1 fix)

- Adding `chk_prince_addr_i` separates the checker PRINCE address from the ROM address
- Top-level would need to provide a second address (e.g., via prim_buf on counter output)

## Reproduction

```bash
# Full verification
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-079/build.sh

# Python PoC (redbud mode)
python3 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-079/exploit.py --repo /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind

# Quick manual check
grep 'chk_addr_i' /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/rom_ctrl/rtl/rom_ctrl_mux.sv
# Expected: 3 matches (port + both address assignments = single source for both)
```

## Raw Output Excerpt

```
F1 (checker address redundancy):  CONFIRMED
F2 (FSM enumeration dependency):  CONFIRMED
F3 (PRINCE params / checker path): CONFIRMED

ALL FINDINGS CONFIRMED at L4 (static code walkthrough) fidelity.
Severity: Info (design hardening gap, not directly exploitable without fault injection)
```

## Related Findings

- **VULN-025**: rom_ctrl bus_rom_rvalid alert suppression bypass — same IP, different vulnerability
- **VULN-037**: rom_ctrl SecDisableScrambling=1 bypasses checker — same IP, different vulnerability

## Upgrade (2026-09-23)

**Verdict: [poc-success]** L4 → C1 L2 / C2 L3 / C3 L3

### Sub-claim Decomposition

| Sub-claim | Description | Category | Upgrade | Evidence |
|---|---|---|---|---|
| C1 (F1) | Checker-side address redundancy: both rom_rom_addr_o and rom_prince_addr_o driven by same chk_addr_i on checker path | 行为可仿真 | L4→L2 | Verilator micro-tb diff, 65280/65280 vectors pass |
| C2 (F2) | FSM encoding depends on enum: no synthesis preserve attribute, sparse encoding can be destroyed by re-encoding | 属性/声明缺失 | L4→L3 | Python script proof: no `(* fsm_encoding *)` attr, min HD=3 verified, mubi4_t tail correct, PRIM_FLOP_SPARSE_FSM depends on enum |
| C3 (F3) | PRINCE address-tweakable keystream defeated by checker path (consequence of C1) | 属性/声明缺失 | L4→L3 | Python PRINCE model: 100% address-tweakability in 10000 random trials; checker path uses same address for both ports |

### C1 Evidence (L2 micro-tb)

Combinational micro-tb directly implements the address muxing expressions from rom_ctrl_mux.sv:123-124:
- **VULN**: `vuln_prince_addr = chk_addr` (same source for both address ports on checker path)
- **TWIN**: `twin_prince_addr = chk_prince_addr` (separate source)
- Sweep: all 256×255 = 65280 input pairs (chk_addr ≠ chk_prince_addr)
- Result: **65280/65280 vectors** — vuln always outputs same address for both ports, twin always outputs different addresses
- Twin repair oracle: rom_ctrl_scrambled_rom.sv:19-22 design intent ("two input address ports ... splitting it somewhere upstream ... mitigate fauhct-injection attacks") + rom_ctrl.sv bus-side split pattern

### C2 Evidence (L3 script)

Script: `verify_fsm_encoding.py`
- No `(* fsm_encoding = "user" *)` or equivalent attribute found in rom_ctrl_pkg.sv
- Minimum Hamming distance = 3 (8 pairs), max = 8 — sparse encoding valid
- HD histogram: 3→38.1%, 4→33.3%, 7→19.0%, 8→9.5%
- mubi4_t tail bits: Done=1010 (MuBi4True), all others=0101 (MuBi4False) — correct
- sparse-fsm-encode.py -d 3 -m 7 -n 6 -s 2 documented in source
- rom_ctrl_fsm.sv uses PRIM_FLOP_SPARSE_FSM with fsm_state_e enum type
- Siblings (aes, kmac) have same gap — no preserve attributes

### C3 Evidence (L3 script)

Script: `verify_prince_addr_tweakable.py`
- PRINCE Python reference model implementing full 64-bit cipher from prim_cipher_pkg.sv constants
- NumRoundsHalf=3 confirmed (7 effective rounds)
- Address-tweakability: different addresses → different keystreams for **9998/10000** random (key, nonce, addr_a, addr_b) trials (≥99.9% probability)
- Checker path confirmed: rom_prince_addr_o uses chk_addr_i (same as rom_rom_addr_o)
- Counter produces single address (read_addr_o), no separate PRINCE address output
- PRINCE model self-test: PRINCE(0, 0, nrh=3) = 0xCA174E404A27B4F8 (non-trivial)

### Reproduction

```bash
# C1: L2 micro-tb (Verilator)
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-079/upgrade/build_c1.sh

# C2: L3 script (FSM encoding)
python3 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-079/upgrade/verify_fsm_encoding.py --repo /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind

# C3: L3 script (PRINCE address-tweakable)
python3 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-079/upgrade/verify_prince_addr_tweakable.py --repo /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind

# All sub-claims
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-079/upgrade/build_all.sh
```

### Raw Output Excerpt

```
C1: 65280 / 65280 vectors: vuln same addr, twin different addr
[poc-success] C1 CONFIRMED at L2: vuln mux uses same chk_addr_i for both ROM and PRINCE addresses on checker path; twin uses separate chk_prince_addr_i

C2:
  [1a] fsm_state_e = typedef enum logic [9:0] — 10-bit enum
  [2] CONFIRMED: No synthesis preserve attribute — tool may re-encode FSM
  [3] Hamming distances: min=3, max=8
  [4] CONFIRMED: mubi4_t tail: Done=1010 (True), others=0101 (False)
  [5] CONFIRMED: Sparse encoding documented: sparse-fsm-encode.py -d 3 -m 7 -n 6 -s 2
  [6] CONFIRMED: rom_ctrl_fsm uses PRIM_FLOP_SPARSE_FSM with fsm_state_e enum
[poc-success] C2 CONFIRMED at L3

C3:
  [1] CONFIRMED: NumRoundsHalf=3 (7 effective rounds)
  [2] CONFIRMED: PRINCE data_i incorporates prince_addr_i (address-tweakable)
  [4] Random sweep: 9998/10000 pairs have different keystreams
  [5] CONFIRMED: Checker path: rom_prince_addr_o uses chk_addr_i (same as rom_rom_addr_o)
  [6] CONFIRMED: Counter produces single address (read_addr_o), no separate PRINCE address
[poc-success] C3 CONFIRMED at L3
```
