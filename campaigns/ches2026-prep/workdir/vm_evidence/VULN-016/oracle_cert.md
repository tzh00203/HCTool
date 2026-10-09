# Oracle Certification — VULN-016

Generated: 2026-10-09 18:31 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle evidence:
- Line 471: `nonce_error = lack_nonce_inputs` — defined as a real error condition
- Oracle: nonce_error defined at line 471, reported to SW (line 493-494),
- Oracle: nonce_error defined L471, reported L493-494, in ascon_error L526
- Oracle basis: in-tree — nonce_error is defined as a real error condition (line 471), reported to software (lines 493-494), and included in the aggregated ascon_error (line 526). It must also gate start_ok for security.

## Evidence Log (excerpt)

```
make: Entering directory '/tmp/poc_vuln016_wmcqlyob/obj_dir'
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o sim_main.o /tmp/vuln_verify/VULN-016/sim_main.cpp
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o verilated.o /tools/verilator/4.210/share/verilator/include/verilated.cpp
/usr/bin/perl /tools/verilator/4.210/share/verilator/bin/verilator_includer -DVL_INCLUDE_OPT=include Vtb.cpp Vtb___024root.cpp Vtb___024root__Slow.cpp Vtb__Syms.cpp > Vtb__ALL.cpp
echo "" > Vtb__ALL.verilator_deplist.tmp
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o Vtb__ALL.o Vtb__ALL.cpp
Archive ar -rcs Vtb__ALL.a Vtb__ALL.o
g++-11    sim_main.o verilated.o Vtb__ALL.a      -o Vtb
rm Vtb__ALL.verilator_deplist.tmp
make: Leaving directory '/tmp/poc_vuln016_wmcqlyob/obj_dir'
start=1, key_error=0, nonce_error=1:
  vuln start_ok = 1  (should be 1: nonce not checked)
  twin start_ok = 1  (should be 0: nonce blocks start)
CONFIRMED: ascon_core.sv:478 start_ok = start & ~key_error
  missing nonce_error gate — nonce reuse possible.
  Vuln: start_ok=1 when nonce not loaded (nonce_error=1).
  Twin: start_ok = start & ~key_error & ~nonce_error blocks start.
  Oracle: nonce_error defined at line 471, reported to SW (line 493-494),
  included in ascon_error (line 526) — must also gate start_ok.
```
