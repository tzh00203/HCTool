# Oracle Certification — VULN-037

Generated: 2026-10-09 18:32 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: [poc-success]
Fidelity: None
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle: SVA `NoReadsBeforeDone_A` (done=True implies check was performed),
- Oracle: SVA NoReadsBeforeDone_A + PwrmgrDataChk_A + line 20 comment.
- Oracle: SVA NoReadsBeforeDone_A + PwrmgrDataChk_A + line 20 comment

## Evidence Log (excerpt)

```
make: Entering directory '/tmp/poc_vuln037_oszxnuka/obj_dir'
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o sim_main.o /tmp/vuln_verify/VULN-037/sim_main.cpp
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o verilated.o /tools/verilator/4.210/share/verilator/include/verilated.cpp
/usr/bin/perl /tools/verilator/4.210/share/verilator/bin/verilator_includer -DVL_INCLUDE_OPT=include Vtb.cpp Vtb___024root.cpp Vtb___024root__Slow.cpp Vtb__Syms.cpp > Vtb__ALL.cpp
echo "" > Vtb__ALL.verilator_deplist.tmp
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o Vtb__ALL.o Vtb__ALL.cpp
Archive ar -rcs Vtb__ALL.a Vtb__ALL.o
g++-11    sim_main.o verilated.o Vtb__ALL.a      -o Vtb
rm Vtb__ALL.verilator_deplist.tmp
make: Leaving directory '/tmp/poc_vuln037_oszxnuka/obj_dir'
SecDisableScrambling=1: vuln_done=True(vuln) done=False(twin)  vuln_alert=0(twin=1)
vuln_deviation: YES  twin_secure: YES
CONFIRMED: rom_ctrl.sv SecDisableScrambling=1 sets pwrmgr_data_o.done=MuBi4True
and checker_alert=0, telling pwrmgr the ROM check passed even though
scrambling and the checker FSM are completely bypassed.
Twin: done=MuBi4False (check not performed) + checker_alert=1 (alert fires).
Oracle: SVA NoReadsBeforeDone_A + PwrmgrDataChk_A + line 20 comment.
```
