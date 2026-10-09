# RESULT: VULN-015

## Verdict: [poc-success] L2 fidelity

**Ascon EDN completely disconnected — PRD/random masking unavailable**

ascon.sv:117 hardcodes `edn_req = 1'b0` and assigns `edn_data` to `unused_edn_data`.
The Entropy Distribution Network is never requested, and any entropy data that could
arrive is discarded unused. This means the Ascon cipher operates without any
PRD (Pseudo-Random Data) for masking — zero SCA protection.

## Twin Repair

- **Vuln** (ascon.sv:117): `assign edn_req = 1'b0;` + `assign unused_edn_data = edn_data;`
- **Twin**: `assign edn_req = entropy_masking_req | entropy_clearing_req;` per AES sibling
  oracle (aes.sv:130 `edn_req_int = entropy_clearing_req | entropy_masking_req`,
  aes.sv:139 `edn_req = edn_req_int | edn_req_hold_q`). edn_data feeds into masking
  data path instead of unused signal.
- **Oracle**: AES sibling module aes.sv:130,139 — same EDN interface, same
  prim_sync_reqack_data synchronizer, but AES properly drives edn_req from internal
  entropy needs.

## Reproduction

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-015
bash build.sh
# exit code 1 = finding confirmed
```

## Raw Output

```
When entropy is needed (entropy_masking_req=1):
  vuln edn_req=0 (no request): YES
  twin edn_req=1 (fires):      YES
  vuln edn_data unused:        YES
CONFIRMED: ascon.sv:117 edn_req hardcoded to 1'b0 — EDN completely disconnected.
  vuln: edn_req=1'b0 always, edn_data assigned to unused_edn_data (never consumed).
        PRD/random masking unavailable, no SCA protection.
  twin: edn_req=entropy_masking_req|entropy_clearing_req per AES sibling aes.sv:130,139.
        edn_data feeds into masking data path.
exit code: 1 (1 = finding confirmed)
```

## Deliverables

| File | Description |
|---|---|
| tb_ascon_edn.sv | Combinational micro-tb: vuln vs twin edn_req expression |
| sim_main.cpp | C++ driver: prints evidence, exit 1 on confirmed |
| build.sh | Verilator build script |
| exploit.py | redbud-mode PoC entry (path-parameterized) |
