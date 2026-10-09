# RESULT: VULN-003

## Verdict: [poc-success] L2

## Finding
lc_ctrl_signal_decode.sv:116 — LcStProd is listed as a duplicate case value in the
TEST_UNLOCKED branch (lines 109-124). Due to `unique case` first-match-wins semantics,
LcStProd matches the TEST_UNLOCKED branch and receives lc_dft_en=On and
lc_hw_debug_en=On — granting PROD state TEST_UNLOCKED-level DFT and hardware debug
permissions. The correct PROD/PROD_END branch (lines 139-154) is unreachable for
LcStProd.

## Fidelity Level
L2 — data flow evidence (combinational micro-tb, expression-level decode logic)

## Reproduction Command
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-003
bash build.sh
# Expected: exit code 1 (finding confirmed)
```

## Raw Output
```
LcStProd signal decode (lc_state=LcStProd, fsm=IdleSt, valid=1):
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: lc_ctrl_signal_decode.sv:116 LcStProd duplicate case value
  vuln: LcStProd in TEST_UNLOCKED branch -> lc_dft_en=On, lc_hw_debug_en=On
        (PROD state gets TEST_UNLOCKED-level DFT and debug permissions)
  twin: LcStProd removed from TEST_UNLOCKED branch -> lc_dft_en=Off, lc_hw_debug_en=Off
        (PROD state correctly has no DFT/debug; matches PROD/PROD_END block lines 139-154)
exit code: 1 (1 = finding confirmed)
```

## Twin Repair Diff
**File**: lc_ctrl_signal_decode.sv line 116
**Vuln**: `LcStTestUnlocked6, LcStProd: begin` (LcStProd in TEST_UNLOCKED branch)
**Twin**: `LcStTestUnlocked6: begin` (LcStProd removed from TEST_UNLOCKED branch)
**Repair basis**: In-tree oracle — the PROD/PRODEND case block (lines 139-154) and
LcStDev block (lines 159-173) both show production states must NOT enable lc_dft_en
or lc_hw_debug_en. Only the TEST_UNLOCKED branch enables these signals.

## Deliverables
| File | Path |
|---|---|
| tb | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-003/tb_lc_ctrl_prod.sv` |
| twin | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-003/lc_ctrl_signal_decode_twin.sv` |
| micro pkg | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-003/lc_ctrl_micro_pkg.sv` |
| build.sh | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-003/build.sh` |
| sim_main.cpp | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-003/sim_main.cpp` |
| exploit.py | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-003/exploit.py` |
