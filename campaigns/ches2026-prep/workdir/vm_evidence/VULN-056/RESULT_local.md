# RESULT: VULN-056

## Verdict: [poc-success] L2 fidelity

## Finding

hmac.sv:941 `ValidHashStartAssert` SVA commented out. The assertion
`hash_start_or_continue |-> !initiated` is a protocol invariant check that
prevents issuing hash_start or hash_continue while a hash operation is already
initiated. With the SVA removed, there is no formal guarantee that this
invariant holds — the violation condition `hash_start_or_continue && initiated`
goes completely undetected in the vuln.

The design's `~cfg_block` gating currently prevents `hash_start_or_continue`
from firing when `initiated=1` (since `cfg_block` is set when hash runs and
`hash_start`/`hash_continue` are gated by `~cfg_block`). However, the SVA
provides defense-in-depth: without it, future modifications could break the
invariant without any assertion catching it. The designer's comment "Below
condition is covered by the design (2020-02-19)" acknowledges the redundancy
but removing the formal check eliminates the safety net.

## Twin Fix

Uncomment `ValidHashStartAssert` on line 941:
```
// vuln (line 941):
  //`ASSERT(ValidHashStartAssert, hash_start_or_continue |-> !initiated)
// twin (line 941):
  `ASSERT(ValidHashStartAssert, hash_start_or_continue |-> !initiated)
```
Also move `initiated` and `in_process` logic outside `ifndef VERILATOR` for
Verilator visibility, and add functional violation output signal
`valid_hash_start_violation_o = hash_start_or_continue & initiated`.

Oracle: line 937 comment + `ValidHashProcessAssert` (line 943, still active)
+ `ValidHmacEnConditionAssert` (line 946, uses `initiated`) + SEC_CM intent.

## Reproduction

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-056
bash build.sh
```

## Raw Output

```
SVA ValidHashStartAssert condition (hash_start_or_continue=1, initiated=1):
  vuln: SVA absent (commented out) → violation undetected: YES
  twin: SVA present (restored)    → violation detected:   YES
CONFIRMED: hmac.sv:941 ValidHashStartAssert SVA commented out
  vuln: SVA removed → no formal check for hash_start_or_continue |-> !initiated
        Protocol violation (hash_start while already initiated) goes undetected.
        Design's ~cfg_block gating currently prevents the condition,
        but without the SVA there is no formal guarantee the invariant holds.
  twin: SVA restored → formal check present, catches protocol violation.
        Oracle: hmac.sv line 937 comment "Below condition is covered by the design"
        + ValidHashProcessAssert (line 943) still active + SEC_CM intent.
exit code: 1 (1 = finding confirmed)
```

## Files

| File | Description |
|---|---|
| `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-056/tb_vuln056.sv` | L2 combinatorial micro-tb |
| `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-056/hmac_twin.sv` | Twin module (SVA uncommented + functional check) |
| `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-056/sim_main.cpp` | C++ driver |
| `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-056/build.sh` | Verilator build script |
| `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-056/exploit.py` | PoC entry (redbud mode) |
