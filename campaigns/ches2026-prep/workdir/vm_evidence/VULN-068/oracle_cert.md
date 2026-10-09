# Oracle Certification — VULN-068

Generated: 2026-10-09 18:33 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle: mode+strength check is a security invariant (SEC_CM). The `cfg_en_unsupported_modestrength_i` input (line 65 comment: "errchk propagates the command...even with err_modestrength") documents intent to bypass, but this contradicts the security purpose of the check.
- Oracle: SEC_CM security invariant; SW-writable bit should not bypass mode+strength check
- SEC_CM security

## Evidence Log (excerpt)

```
make: Entering directory '/tmp/poc_vuln068_tbydy2s_/obj_dir'
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o sim_main.o /tmp/vuln_verify/VULN-068/sim_main.cpp
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o verilated.o /tools/verilator/4.210/share/verilator/include/verilated.cpp
/usr/bin/perl /tools/verilator/4.210/share/verilator/bin/verilator_includer -DVL_INCLUDE_OPT=include Vtb.cpp Vtb___024root.cpp Vtb___024root__Slow.cpp Vtb__Syms.cpp > Vtb__ALL.cpp
echo "" > Vtb__ALL.verilator_deplist.tmp
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o Vtb__ALL.o Vtb__ALL.cpp
Archive ar -rcs Vtb__ALL.a Vtb__ALL.o
g++-11    sim_main.o verilated.o Vtb__ALL.a      -o Vtb
rm Vtb__ALL.verilator_deplist.tmp
make: Leaving directory '/tmp/poc_vuln068_tbydy2s_/obj_dir'
err_modestrength=1, cfg_en_unsupported_modestrength=1:
  vuln block_swcmd: 0 (0=bypassed)  twin block_swcmd: 1 (1=enforced)
vuln_deviation: YES  twin_secure: YES
CONFIRMED: kmac_errchk.sv:236-239 en_unsupported_modestrength bypasses mode+strength check
  vuln: block_swcmd = err_swsequence || (err_modestrength && !cfg_en_unsupported_modestrength) || err_entropy_ready
        With bypass=1 and err_modestrength=1: block_swcmd=0, command propagates (check bypassed)
  twin: block_swcmd = err_swsequence || err_modestrength || err_entropy_ready
        With err_modestrength=1: block_swcmd=1, command blocked (check enforced)
  Oracle: mode+strength check is a security invariant (SEC_CM), SW-writable bit should not bypass it.
```
