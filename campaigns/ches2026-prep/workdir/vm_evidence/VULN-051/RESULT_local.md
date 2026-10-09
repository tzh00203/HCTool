# RESULT: VULN-051

## Verdict
**[poc-success]** L2 fidelity

## Finding
Ascon TRIGGER.START hardcoded d=0/de=1: `ascon_core.sv:302` assigns `hw2reg.trigger.start.d = 1'b0` with `de = 1'b1`. After SW writes START=1, the register is immediately overwritten to 0 (de=1, d=0). SW can never read back START=1 — trigger feedback is lost.

## Verification Method
Combinational micro-tb (tb_comb pattern): directly compare vuln expression `d=1'b0` vs twin expression `d=start` when start=1.

## Twin Repair
- File: `ascon_core.sv` line 302
- Vuln: `assign hw2reg.trigger.start.d = 1'b0;`
- Twin: `assign hw2reg.trigger.start.d = start;`
- Oracle: hwext register d must passthrough reg2hw.trigger.start.q (start = reg2hw.trigger.start.q, line 297)
- Diff: 1 line changed (d: `1'b0` → `start`)

## Reproduction
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-051
bash build_vuln051.sh
# exit code 1 = finding confirmed
```

## Raw Output
```
SW writes START=1: vuln trigger.start.d=0  twin trigger.start.d=1
CONFIRMED: ascon_core.sv:302 hw2reg.trigger.start.d hardcoded to 1'b0
  vuln: d=0 always → SW reads back 0 after writing START=1 (trigger lost)
  twin: d=start → SW reads back 1 after writing START=1 (correct hwext echo)
  Oracle: hwext register d must passthrough reg2hw.trigger.start.q
exit code: 1 (1 = finding confirmed)
```

## Success Criteria Met
- vuln: reads back 0 (d=0) ✓
- twin: reads back 1 (correct hwext behavior) ✓
- Differential output: confirmed ✓
