# Oracle Certification — VULN-041

Generated: 2026-10-09 18:32 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-CONFIRMED

## Twin Repair Diff

- The SVA AesCtrStateValid intent (no CTR_ERROR state with alert_o=0)
- The default case (line 95-98) which already alerts immediately
- The SEC_CM CTR.FSM.LOCAL_ESC security countermeasure intent

## Oracle References

- SEC_CM CTR

## Evidence Log (excerpt)

```
%Error: Cannot find file containing module: /home/participant/opentitan/hw/ip/prim/rtl
        ... Looked in:
             //home/participant/opentitan/hw/ip/prim/rtl
             //home/participant/opentitan/hw/ip/prim/rtl.v
             //home/participant/opentitan/hw/ip/prim/rtl.sv
             /home/participant/opentitan/hw/ip/prim/rtl
             /home/participant/opentitan/hw/ip/prim/rtl.v
             /home/participant/opentitan/hw/ip/prim/rtl.sv
             /tmp/poc_vuln041_rftm8umx/obj_dir//home/participant/opentitan/hw/ip/prim/rtl
             /tmp/poc_vuln041_rftm8umx/obj_dir//home/participant/opentitan/hw/ip/prim/rtl.v
             /tmp/poc_vuln041_rftm8umx/obj_dir//home/participant/opentitan/hw/ip/prim/rtl.sv
%Error: //tmp/vuln_verify/VULN-041/aes_ctr_fsm_twin.sv:7:10: Cannot find include file: prim_assert.sv
    7 | `include "prim_assert.sv"
      |          ^~~~~~~~~~~~~~~~
%Error-PKGNODECL: //tmp/vuln_verify/VULN-041/aes_ctr_fsm_twin.sv:17:32: Package/class 'aes_pkg' not found, and needs to be predeclared (IEEE 1800-2017 26.3)
   17 | module aes_ctr_fsm_twin import aes_pkg::*;
      |                                ^~~~~~~
                  ... For error description see https://verilator.org/warn/PKGNODECL?v=4.210
%Error: //tmp/vuln_verify/VULN-041/aes_ctr_fsm_twin.sv:17:32: Importing from missing package 'aes_pkg'
   17 | module aes_ctr_fsm_twin import aes_pkg::*;
      |                                ^~~~~~~
%Error: //tmp/vuln_verify/VULN-041/aes_ctr_fsm_twin.sv:119:3: Define or directive not defined: '`PRIM_FLOP_SPARSE_FSM'
  119 |   `PRIM_FLOP_SPARSE_FSM(u_state_regs, aes_ctr_ns, aes_ctr_cs, aes_ctr_e, CTR_IDLE)
      |   ^~~~~~~~~~~~~~~~~~~~~
%Error: //tmp/vuln_verify/VULN-041/aes_ctr_fsm_twin.sv:119:24: syntax error, unexpected '('
  119 |   `PRIM_FLOP_SPARSE_FSM(u_state_regs, aes_ctr_ns, aes_ctr_cs, aes_ctr_e, CTR_IDLE)
      |                        ^
%Error: //tmp/vuln_verify/VULN-041/aes_ctr_fsm_twin.sv:127:3: Define or directive not defined: '`ASSERT'
  127 |   `ASSERT(AesCtrStateValid, !alert_o |-> aes_ctr_cs inside {
      |   ^~~~~~~
%Error: Cannot continue
Traceback (most recent call last):
  File "/tmp/vuln_verify/VULN-041/exploit.py", line 99, in <module>
    main()
  File "/tmp/vuln_verify/VULN-041/exploit.py", line 80, in main
    subprocess.run(
  File "/usr/lib/python3.12/subprocess.py", line 571, in run
    raise CalledProcessError(retcode, process.args,
subprocess.CalledProcessError: Command '['/home/participant/verilator/bin/verilator', '-sv', '--cc', '--exe', '--build', '-j', '2', '-Wno-fatal', '-Wno-WIDTH', '-Wno-DECLFILENAME', '-Wno-UNOPTFLAT', '--Mdir', '/tmp/poc_vuln041_rftm8umx/obj_dir', '-I', '/home/participant/opentitan/hw/ip/prim/rtl', '--top-module', 'tb', '/tmp/vuln_verify/VULN-041/aes_ctr_fsm_twin.sv', '/tmp/vuln_verify/VULN-041/tb_ctr.sv', '/tmp/vuln_verify/VULN-041/sim_main.cpp', '/home/participant/opentitan/hw/ip/prim/rtl/prim_util_pkg.sv', '/home/participant/opentitan/hw/ip/prim/rtl/prim_mubi_pkg.sv', '/home/participant/opentitan/hw/ip/aes/rtl/aes_reg_pkg.sv', '/home/participant/opentitan/hw/ip/aes/rtl/aes_pkg.sv', '/home/participant/opentitan/hw/ip/prim/rtl/prim_flop_macros.sv', '/home/participant/opentitan/hw/ip/prim/rtl/prim_sparse_fsm_flop.sv', '/home/participant/opentitan/hw/ip/prim_generic/rtl/prim_generic_flop.sv', '/home/participant/opentitan/hw/ip/aes/rtl/aes_ctr_fsm.sv', '/home/participant/opentitan/hw/vendor/lowrisc_ibex/dv/uvm/core_ibex/common/prim/prim_flop.sv']' returned non-zero exit status 1.
```
