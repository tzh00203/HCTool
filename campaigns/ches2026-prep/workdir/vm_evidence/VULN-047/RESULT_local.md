# RESULT: VULN-047

## Verdict: [poc-success]

Ascon `ascon_operation` unused in duplex FSM AbsorbMSG state — ASCON_HASH falls through to DEC branch.

## Fidelity: L2 (data-flow evidence, combinational micro-tb)

## Vulnerability

`prim_ascon_duplex.sv:487` in the AbsorbMSG state checks only `if (ascon_operation == ASCON_ENC)`.
The else branch treats ASCON_HASH as ASCON_DEC, causing:
1. **Wrong padding**: HASH uses `DATA_OUT_PAD` (ciphertext-feedback padding) instead of `DATA_IN_PAD` (direct input absorption)
2. **Wrong key mux (128A)**: HASH sets `sel_mux_key_word1 = WORD` instead of staying at default `KEY`

Per the Ascon specification, Hash absorbs input directly into the state (same path as encryption).
Only decryption uses `DATA_OUT_PAD` because it feeds ciphertext back.

## Twin Repair

Line 487 changed from:
```sv
if (ascon_operation == ASCON_ENC) begin
```
to:
```sv
if (ascon_operation == ASCON_ENC || ascon_operation == ASCON_HASH) begin
```

Oracle: Ascon spec (Hash absorbs input directly = same as ENC), hjson ASCON_HASH operation definition, only DEC uses DATA_OUT_PAD.

Diff = 1 line.

## Reproduction

```bash
export OT_TREE=/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind
export VERILATOR_ROOT=/data_hdd/tzh24/zgc4/projects/tools/logos/logos-workspace/contexts/targets/opentitan-ches2026/runtime-samples/verilator-4.210/v4.210
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-047/build_ascon_operation.sh
```

## Raw Output

```
operation=ASCON_HASH:
  vuln_deviation: YES
  twin_secure:    YES
CONFIRMED: prim_ascon_duplex.sv:487 ascon_operation unused in AbsorbMSG
  vuln: if(op==ASCON_ENC) — HASH falls to else (DEC) branch,
        uses DATA_OUT_PAD and sel_mux_key_word1=WORD (128A)
  twin: if(op==ASCON_ENC || op==ASCON_HASH) — HASH uses DATA_IN_PAD
        and default KEY like ENC per Ascon spec
exit code: 1 (1 = finding confirmed)
```

## Deliverables

| File | Path |
|---|---|
| tb | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-047/tb_ascon_operation.sv` |
| twin | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-047/prim_ascon_duplex_twin.sv` |
| build | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-047/build_ascon_operation.sh` |
| sim_main | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-047/sim_main.cpp` |
| exploit | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-047/exploit.py` |
