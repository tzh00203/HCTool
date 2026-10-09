# Oracle Certification — VULN-040

Generated: 2026-10-09 18:32 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: [poc-success]
Fidelity: L2
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle**: SEC_CM: SCRMBL.FSM.SPARSE annotation; terminal error state security convention requires clearing sensitive working registers to prevent data leakage. The FSM comment (line 420) states "Terminal error state" — no further operations should use retained state.
- Oracle: SEC_CM: SCRMBL.FSM.SPARSE; terminal error state must clear
- Oracle: SEC_CM: SCRMBL.FSM.SPARSE + terminal error state security convention

## Evidence Log (excerpt)

```
make: Entering directory '/tmp/poc_vuln040_qi_uw9ru/obj_dir'
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o sim_main.o /tmp/vuln_verify/VULN-040/sim_main.cpp
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o verilated.o /tools/verilator/4.210/share/verilator/include/verilated.cpp
/usr/bin/perl /tools/verilator/4.210/share/verilator/bin/verilator_includer -DVL_INCLUDE_OPT=include Vtb.cpp Vtb___024root.cpp Vtb___024root__Slow.cpp Vtb__Syms.cpp > Vtb__ALL.cpp
echo "" > Vtb__ALL.verilator_deplist.tmp
g++-11  -I.  -MMD -I/tools/verilator/4.210/share/verilator/include -I/tools/verilator/4.210/share/verilator/include/vltstd -DVM_COVERAGE=0 -DVM_SC=0 -DVM_TRACE=0 -DVM_TRACE_FST=0 -faligned-new -fcf-protection=none -Wno-bool-operation -Wno-sign-compare -Wno-uninitialized -Wno-unused-but-set-variable -Wno-unused-parameter -Wno-unused-variable -Wno-shadow      -std=gnu++14 -Os -c -o Vtb__ALL.o Vtb__ALL.cpp
Archive ar -rcs Vtb__ALL.a Vtb__ALL.o
g++-11    sim_main.o verilated.o Vtb__ALL.a      -o Vtb
rm Vtb__ALL.verilator_deplist.tmp
make: Leaving directory '/tmp/poc_vuln040_qi_uw9ru/obj_dir'
ErrorSt register control signal check:
  vuln: key_state_en=0, data_state_en=0, digest_state_en=0 (NOT cleared)
  twin: key_state_en=1, data_state_en=1, digest_state_en=1 (cleared to 0)
vuln_deviation: YES  twin_secure: YES
CONFIRMED: otp_ctrl_scrmbl.sv ErrorSt doesn't clear sensitive internal state.
  vuln: ErrorSt sets only fsm_err_o=1; key_state_en=0, data_state_en=0,
        digest_state_en=0 -> key_state_q/data_state_q/digest_state_q retain
        pre-error values (sensitive key material survives).
  twin: ErrorSt also asserts key_state_en=1, data_state_en=1,
        digest_state_en=1 with data='0 -> registers cleared to 0.
  Oracle: SEC_CM: SCRMBL.FSM.SPARSE; terminal error state must clear
          sensitive working registers per security convention.
```
