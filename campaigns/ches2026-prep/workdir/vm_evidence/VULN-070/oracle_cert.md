# Oracle Certification — VULN-070

Generated: 2026-10-09 18:34 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: L2
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle: SVA NoClkBypInProdStates_A (line 860-863) constrains lc_clk_byp_req in PROD/PROD_END/DEV;
- oracle: SVA NoClkBypInProdStates_A + ClkMuxSt inside-set (lines 369-385)
- SEC_CM declaration
- SEC_CM declarations
- SEC_CM gap

## Evidence Log (excerpt)

```
make: Entering directory '/tmp/poc_vuln070_jjgyuho1/obj_dir'
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o sim_main.o /tmp/vuln_verify/VULN-070/sim_main.cpp
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o verilated.o /tools/verilator/4.210/share/verilator/include/verilated.cpp
/usr/bin/perl /tools/verilator/4.210/share/verilator/bin/verilator_includer -DVL_INCLUDE_OPT=include Vtb_lc_check_byp_en.cpp Vtb_lc_check_byp_en___024root.cpp Vtb_lc_check_byp_en___024root__Slow.cpp Vtb_lc_check_byp_en__Syms.cpp > Vtb_lc_check_byp_en__ALL.cpp
echo "" > Vtb_lc_check_byp_en__ALL.verilator_deplist.tmp
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o Vtb_lc_check_byp_en__ALL.o Vtb_lc_check_byp_en__ALL.cpp
Archive ar -rcs Vtb_lc_check_byp_en__ALL.a Vtb_lc_check_byp_en__ALL.o
g++-11    sim_main.o verilated.o Vtb_lc_check_byp_en__ALL.a      -o Vtb_lc_check_byp_en
rm Vtb_lc_check_byp_en__ALL.verilator_deplist.tmp
make: Leaving directory '/tmp/poc_vuln070_jjgyuho1/obj_dir'
cycles=1
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: lc_check_byp_en unconditionally On in ClkMuxSt
  vuln: lc_check_byp_en=On even for non-bypass-eligible states (PROD/PROD_END/DEV)
  twin: lc_check_byp_en gated by bypass-eligible set; Off for PROD/PROD_END/DEV
  oracle: SVA NoClkBypInProdStates_A + ClkMuxSt inside-set (lines 369-385)
  SEC_CM gap: no CHECK_BYP.SIGNAL.REDUN declaration for lc_check_byp_en_o
```
