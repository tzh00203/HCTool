# Oracle Certification — VULN-030

Generated: 2026-10-09 18:32 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle: sibling module aes_core uses `prd_clearing_key`/`prd_clearing_data`
- Oracle: sibling module aes_core prd_clearing_* pattern + ascon.hjson "secure wipe"

## Evidence Log (excerpt)

```
make: Entering directory '/tmp/poc_vuln030_dpkgz2_o/obj_dir'
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o sim_main.o /tmp/vuln_verify/VULN-030/sim_main.cpp
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o verilated.o /tools/verilator/4.210/share/verilator/include/verilated.cpp
/usr/bin/perl /tools/verilator/4.210/share/verilator/bin/verilator_includer -DVL_INCLUDE_OPT=include Vtb.cpp Vtb___024root.cpp Vtb___024root__Slow.cpp Vtb__Syms.cpp > Vtb__ALL.cpp
echo "" > Vtb__ALL.verilator_deplist.tmp
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o Vtb__ALL.o Vtb__ALL.cpp
Archive ar -rcs Vtb__ALL.a Vtb__ALL.o
g++-11    sim_main.o verilated.o Vtb__ALL.a      -o Vtb
rm Vtb__ALL.verilator_deplist.tmp
make: Leaving directory '/tmp/poc_vuln030_dpkgz2_o/obj_dir'
vuln_deviation: YES
twin_secure:    YES
CONFIRMED: Ascon SEC_WIPE clears KEY/NONCE shares to '0 instead of PRD.
  hw2reg.key_share0[i].d = '0 (line 163), key_share1[i].d = '0 (line 172),
  hw2reg.nonce_share0[i].d = '0 (line 213), nonce_share1[i].d = '0 (line 222).
  Deterministic zero clearing provides no SCA protection.
  Twin uses edn_data (PRD) per sibling module pattern (aes_core prd_clearing_*).
```
