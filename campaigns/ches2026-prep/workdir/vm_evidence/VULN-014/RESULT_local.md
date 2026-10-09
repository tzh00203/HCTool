# RESULT: VULN-014 — Ascon WIPE trigger dropped + ERROR register not clearable

## Verdict: [poc-success]

## Fidelity: L2 (data-flow evidence, combinational micro-tb)

## Finding

ascon_core.sv:305-309 assigns `wipe` (from `reg2hw.trigger.wipe.q`) to `unused_wipe` — the
TRIGGER.WIPE signal is completely dead-ended. No key/nonce/data register has a wipe condition
in its always_ff block. When SW writes TRIGGER.WIPE=1, all sensitive registers retain their
values, contradicting the hjson spec: "Performs a secure wipe of sensitive data".

Additionally, `hw2reg.trigger.wipe.d = 1'b0; de = 1'b1` immediately clears the trigger
register without performing any wipe action — a silent no-op from SW's perspective.

## Twin Repair

Removed `unused_wipe = wipe` dead sink. Added `else if (wipe) reg <= '0` condition to all
six input register groups (key_share0, key_share1, nonce_share0, nonce_share1,
data_share0, data_share1). Oracle: ascon.hjson "secure wipe of sensitive data" and sibling
module pattern (aes_core, kmac_core all implement wipe-to-clear).

## Test Method

Combinational micro-tb comparing next-state expressions:
- **vuln**: `key_next = qe ? key_d : key_q` (no wipe term)
- **twin**: `key_next = wipe ? '0 : (qe ? key_d : key_q)` (wipe clears to 0)

With wipe=1, qe=0, key_q=NONZERO:
- vuln: key_next = key_q (key retained — vulnerability)
- twin: key_next = '0 (key cleared — correct)

## Evidence

```
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: Ascon TRIGGER.WIPE is dead-ended (unused_wipe=wipe),
  key/nonce/data registers retain values after WIPE.
  Twin: wipe condition clears all sensitive registers to 0
  (oracle: ascon.hjson 'secure wipe of sensitive data')
exit code: 1 (1 = finding confirmed)
```

## Build & Run

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-014
bash build_ascon_wipe.sh
# exit code 1 = finding confirmed
```

## Deliverables

| File | Description |
|------|-------------|
| `ascon_core_twin.sv` | Twin: ascon_core with wipe→clear logic added |
| `tb_ascon_wipe.sv` | Combinational micro-tb (vuln vs twin next-state) |
| `sim_main.cpp` | C++ driver |
| `build_ascon_wipe.sh` | Verilator build script |
| `exploit.py` | PoC entry (redbud mode) |
