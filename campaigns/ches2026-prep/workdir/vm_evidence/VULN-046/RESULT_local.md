# RESULT: VULN-046

## Verdict
**[poc-success]** L2 fidelity

## Finding
ascon_core.sv:329-332 STATUS.stall and STATUS.wait_edn hardcoded to 1'b0 —
SW cannot detect backpressure (stall) or EDN starvation (wait_edn).

- Vuln: `hw2reg.status.stall.d = 1'b0; hw2reg.status.wait_edn.d = 1'b0;` (always zero)
- Twin: `stall = msg_out_valid & ~msg_out_ready; wait_edn = ~edn_fifo_ready;` (reflects real state)

## Oracle
- Lines 328-332: `// TODO STATUS` comment confirms stub implementation
- Sibling IPs (AES, KMAC) compute stall/wait_edn from real ready-valid handshaking signals
- hjson STATUS register declares stall/wait_edn as SW-readable status fields

## Reproduction
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-046
bash build_ascon_stall.sh
```

## Raw Output
```
Stall scenario (msg_out_valid=1, msg_out_ready=0):
  vuln stall=0 (hardcoded)  twin stall = msg_out_valid & ~msg_out_ready = 1
Wait_edn scenario (edn_fifo_ready=0):
  vuln wait_edn=0 (hardcoded)  twin wait_edn = ~edn_fifo_ready = 1
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: ascon_core.sv:329-332 STATUS.stall/wait_edn hardcoded to 1'b0
  vuln: stall=0, wait_edn=0 always — SW cannot detect backpressure or EDN starvation
  twin: stall=msg_out_valid&~msg_out_ready, wait_edn=~edn_fifo_ready
  Oracle: TODO comments on lines 328-332 + sibling IPs (AES/KMAC) + hjson STATUS spec
exit code: 1 (1 = finding confirmed)
```

## Twin Diff Summary
Changed lines 329-332 of ascon_core.sv:
- `assign hw2reg.status.stall.d = 1'b0;` → `assign hw2reg.status.stall.d = msg_out_valid & ~msg_out_ready;`
- `assign hw2reg.status.wait_edn.d = 1'b0;` → `assign hw2reg.status.wait_edn.d = ~edn_fifo_ready;`
Oracle: TODO comment + sibling IPs + hjson spec
