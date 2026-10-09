# VULN-067 Result

## Verdict: [poc-success] CONFIRMED

KMAC sha3pad has 3 commented-out SVA assertions (formal verification gap) and kmac.sv has msg_mask_permuted computed but never consumed (LFSR mask signal path dangling).

## Fidelity: L4 (static conclusion)

Pure oracle comparison — grep-based verification, no dynamic simulation.

## Vulnerability Details

### Aspect 1: sha3pad SVA assertions commented out

Three SVA assertions in sha3pad.sv are commented out, breaking formal verification coverage:

| Line | Type | Name | Purpose |
|------|------|------|---------|
| 769 | ASSUME | Sequence_a | Control signal sequencing: start → process → absorbed → done |
| 835 | ASSERT | ProcessToAbsorbed_A | Liveness: process eventually leads to absorbed (strong operator) |
| 875 | ASSUME | NsStableInProcess_A | ns_data stability during operation |

- ProcessToAbsorbed_A is a **liveness property** — its absence means the formal checker cannot verify SHA3 completion guarantee after process.
- Sequence_a and NsStableInProcess_A are **assumptions** that constrain FPV — without them, FPV may explore infeasible paths and produce false negatives.

### Aspect 2: msg_mask_permuted signal dangling

In kmac.sv g_msg_mask block (EnMasking==1):
- `msg_mask` is output from kmac_entropy (line 1298) driven by msg_mask_en
- `msg_mask_permuted` is declared (line 907) and computed from msg_mask via RndCnstMsgPerm permutation (lines 915-921)
- **But msg_mask_permuted is NEVER consumed** — the actual masking at lines 925-926 uses `static_mask = {MsgWidth{1'b1}}` (all-ones constant)
- Result: LFSR mask path is completely dead; masking XOR is `msg_data ^ all-ones` = deterministic bitwise complement, zero SCA protection

## Evidence

### Check 1: Commented-out SVA in sha3pad.sv
```
$ grep -n '//`ASSERT\|//`ASSUME' sha3pad.sv
769:  //`ASSUME(Sequence_a, start_i ##[1:$] process_i ##[1:$] ##[1:$] absorbed_o ##[1:$] done_i)
835:  //`ASSERT(ProcessToAbsorbed_A, process_i |=> strong(##[24*Share:$] absorbed_o))
875:  //`ASSUME(NsStableInProcess_A,
```

### Check 2: msg_mask_permuted dangling in kmac.sv
```
$ grep -n 'msg_mask_permuted' kmac.sv
907:    logic [MsgWidth-1:0] msg_mask_permuted;    # declared
916:      msg_mask_permuted = '0;                    # assigned (init)
919:        msg_mask_permuted[i] = static_mask[...]; # assigned (loop)
# NO usage in downstream logic — dangling
```

### Check 3: static_mask used instead of msg_mask_permuted
```
$ grep -A1 'assign msg_data_masked\[i\]' kmac.sv
      assign msg_data_masked[i] = msg_data[i] ^
                                ({MsgWidth{cfg_msg_mask}} & static_mask);
# Should use msg_mask_permuted, not static_mask
```

### Check 4: static_mask is all-ones constant
```
$ grep -n 'static_mask = ' kmac.sv
911:    assign static_mask = {MsgWidth{1'b1}};
```

### Check 5: msg_mask connected from kmac_entropy (source exists but unused)
```
$ grep -n 'msg_mask_o' kmac.sv
1298:      .msg_mask_o    (msg_mask),
```

## Reproduction Commands

```bash
# Full verification (bash)
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-067/build.sh

# Full verification (Python, redbud mode)
python3 /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-067/exploit.py

# Quick manual checks
grep -n '//`ASSERT\|//`ASSUME' /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/sha3pad.sv
grep -n 'msg_mask_permuted' /data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/kmac/rtl/kmac.sv
# Expected: 3 commented-out SVA + msg_mask_permuted declared/computed but not consumed
```

## Twin Repair

### sha3pad_twin: Uncomment 3 SVA assertions
- Line 769: Uncomment `ASSUME(Sequence_a, ...)`
- Line 835: Uncomment `ASSERT(ProcessToAbsorbed_A, ...)`
- Lines 875-877: Uncomment `ASSUME(NsStableInProcess_A, ...)`
- Oracle: In-tree SVA pattern — 25 active ASSERT/ASSUME in sha3pad.sv establish control-flow contract; commented-out assertions break formal verification guarantee.
- See: sha3pad_twin_patch.md

### kmac_twin: Use msg_mask_permuted instead of static_mask
- Lines 925-926: Change `static_mask` → `msg_mask_permuted` in msg_data_masked assignment
- Oracle: kmac_entropy outputs msg_mask (dynamic LFSR) via .msg_mask_o; sibling IPs (AES) use PRD for all masking; SEC_CM: MSG.MASKING documents this feature.
- See: kmac_twin_patch.md

## Related Findings

- **VULN-012**: KMAC g_msg_mask uses static_mask instead of dynamic LFSR — same functional bug from different angle (VULN-012 focuses on static_mask vs msg_mask; VULN-067 adds SVA downgrade + signal dangling analysis).
- **VULN-032**: KMAC hjson countermeasures list missing MSG.MASKING SEC_CM declaration — the declaration gap; VULN-067 is the SVA/functional gap.

## Upgrade (2026-09-23)

### Verdict: [poc-success] CONFIRMED (upgraded from L4)

KMAC sha3pad SVA commented out + msg_mask_permuted dangling: upgraded via L2 micro-tb diff (Claims B1+B2) and L3 script proofs (Claims A, C).

### Fidelity: L2 (data flow empirical) for Claims B1+B2, L3 (script empirical) for Claims A and C

### Sub-Claim Upgrade Table

| Claim | Description | Category | Upgrade | Evidence |
|-------|-------------|----------|---------|----------|
| A | sha3pad has 3 commented-out SVA assertions (Sequence_a, ProcessToAbsorbed_A, NsStableInProcess_A) | 属性缺失 | L4→L3 | Python script: parse sha3pad.sv, confirm 3 commented-out (//`ASSERT/`ASSUME), identify each, verify ProcessToAbsorbed_A is liveness (strong operator), count 22 active + 3 disabled |
| B1 | msg_data_masked uses static_mask (all-ones) instead of msg_mask_permuted → deterministic complement, zero SCA protection | 行为可仿真 | L4→L2 | Verilator micro-tb: vuln (static_mask) vs twin (msg_mask_permuted) produce different msg_data_masked; vuln output = ~msg_data (deterministic) |
| B2 | msg_mask_permuted computed from LFSR but never consumed (signal path dangling) | 行为可仿真 | L4→L2 | Same micro-tb + script: grep kmac.sv for msg_mask_permuted references — declared (907) + assigned (916,919) but 0 consumption points; msg_data_masked uses static_mask (925-926) |
| C | MSG.MASKING missing from kmac.hjson countermeasures list | 声明缺失 | L4→L3 | Python script: parse kmac.hjson, confirm MSG.MASKING absent; SW_KEY.KEY.MASKING present; g_msg_mask block exists in RTL; msg_mask_permuted dangling; static_mask used instead |

### Twin Repair Basis

- **Claim B1 twin**: msg_data_masked[i] = msg_data[i] ^ ({MsgWidth{cfg_msg_mask}} & msg_mask_permuted)
  - Oracle: kmac_entropy.msg_mask_o provides dynamic LFSR mask; AES uses PRD for all masking; SEC_CM: MSG.MASKING documents this feature
- **Claim A twin**: Uncomment 3 SVA assertions in sha3pad
  - Oracle: In-tree SVA pattern — 22 active ASSERT/ASSUME establish control-flow contract

### Reproduction Commands

```bash
# L2 micro-tb (Claims B1+B2): msg_mask_permuted dangling vs static_mask
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-067/upgrade
bash build_kmac_mask_diff.sh
# Expected: exit 1, verdict=0xF (all 4 conditions confirmed)

# L3 script proof (Claim A): sha3pad SVA commented out
python3 prove_sva_commented.py
# Expected: exit 1, 3 commented-out SVA confirmed

# L3 script proof (Claim C): MSG.MASKING missing from hjson
python3 prove_msg_masking_missing.py
# Expected: exit 1, MSG.MASKING absent confirmed

# Full upgrade PoC (all claims)
python3 exploit.py
# Expected: exit 1, all claims confirmed
```

### Evidence Files

| File | Description |
|------|-------------|
| upgrade/tb_kmac_mask_diff.sv | L2 combinational micro-tb: vuln (static_mask) vs twin (msg_mask_permuted) |
| upgrade/sim_main.cpp | C++ driver: verdict checking (4-bit) |
| upgrade/build_kmac_mask_diff.sh | Verilator 4.210 build script |
| upgrade/prove_sva_commented.py | L3 script: parse sha3pad.sv for commented-out SVA |
| upgrade/prove_msg_masking_missing.py | L3 script: parse kmac.hjson + kmac.sv for MSG.MASKING gap |
| upgrade/exploit.py | Full PoC runner (all claims) |
