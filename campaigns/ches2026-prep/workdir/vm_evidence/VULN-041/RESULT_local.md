# RESULT: VULN-041 — AES CTR FSM 100-cycle alert delay

## Verdict
**[poc-success]** Finding confirmed. L1 fidelity.

## Vulnerability
aes_ctr_fsm.sv CTR_ERROR state (lines 84-90) counts `alert_counter_q` from 0 to 99 before asserting `alert_o`. During these 100 cycles, the FSM is in CTR_ERROR with `alert_o=0`, violating the in-tree SVA `AesCtrStateValid` (`!alert_o |-> aes_ctr_cs inside {CTR_IDLE, CTR_INCR}`) 100 times. The SEC_CM CTR.FSM.LOCAL_ESC fatal alert is suppressed for ~100 cycles, meaning a fatal fault goes unreported to the alert handler during that window.

## Twin Repair
Removed the 100-cycle alert_counter delay from CTR_ERROR. Twin asserts `alert_o = 1'b1` immediately upon entering the terminal error state. This matches:
- The SVA AesCtrStateValid intent (no CTR_ERROR state with alert_o=0)
- The default case (line 95-98) which already alerts immediately
- The SEC_CM CTR.FSM.LOCAL_ESC security countermeasure intent

## Evidence (simulation output)
```
sanity walk:              walk_ok=1 we_seen=1
after incr_err_i pulse:   err_entered=1
vuln: silent(SVA-viol)=100 cycles, alert latency=100, alert=1
twin: silent(SVA-viol)=0 cycles, alert latency=0, alert=1
CONFIRMED: after a counter-increment error the FSM sits in the terminal CTR_ERROR state for 100 cycles with alert_o suppressed (in-tree SVA AesCtrStateValid violated 100 times) before the fatal alert asserts; the fixed twin alerts immediately (0 silent cycles). A fatal fault thus goes unreported to the alert handler for ~100 cycles.
exit code: 1 (1 = finding confirmed)
```

## Commands
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-041
bash build.sh
```

## Fidelity Level
L1 (execution-level evidence: full-module Verilator vuln-vs-twin simulation)

## Deliverables
| File | Absolute Path |
|---|---|
| twin | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-041/aes_ctr_fsm_twin.sv |
| tb | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-041/tb_ctr.sv |
| sim_main | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-041/sim_main.cpp |
| build.sh | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-041/build.sh |
| exploit.py | /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-041/exploit.py |
