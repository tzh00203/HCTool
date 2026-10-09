# Oracle Certification — VULN-005

Generated: 2026-10-09 18:31 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

(see RESULT.md for oracle justification)

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
             /tmp/poc_vuln005_pkpxb0m5/obj_dir//home/participant/opentitan/hw/ip/prim/rtl
             /tmp/poc_vuln005_pkpxb0m5/obj_dir//home/participant/opentitan/hw/ip/prim/rtl.v
             /tmp/poc_vuln005_pkpxb0m5/obj_dir//home/participant/opentitan/hw/ip/prim/rtl.sv
%Error-PKGNODECL: //tmp/vuln_verify/VULN-005/tb_force_masks.sv:29:42: Package/class 'aes_pkg' not found, and needs to be predeclared (IEEE 1800-2017 26.3)
   29 |   localparam int unsigned Width        = aes_pkg::WidthPRDMasking;
      |                                          ^~~~~~~
                  ... For error description see https://verilator.org/warn/PKGNODECL?v=4.210
%Error: //home/participant/opentitan/hw/ip/prim/rtl/prim_trivium.sv:57:10: Cannot find include file: prim_assert.sv
   57 | `include "prim_assert.sv"
      |          ^~~~~~~~~~~~~~~~
%Error: //home/participant/opentitan/hw/ip/prim/rtl/prim_trivium.sv:314:3: Define or directive not defined: '`ASSERT'
  314 |   `ASSERT(PrimTriviumPartialStateSeedWhileUpdate_A,
      |   ^~~~~~~
%Error: //home/participant/opentitan/hw/ip/prim/rtl/prim_trivium.sv:314:10: syntax error, unexpected '('
  314 |   `ASSERT(PrimTriviumPartialStateSeedWhileUpdate_A,
      |          ^
%Error: Cannot continue
Traceback (most recent call last):
  File "/tmp/vuln_verify/VULN-005/exploit.py", line 98, in <module>
    main()
  File "/tmp/vuln_verify/VULN-005/exploit.py", line 79, in main
    subprocess.run(
  File "/usr/lib/python3.12/subprocess.py", line 571, in run
    raise CalledProcessError(retcode, process.args,
subprocess.CalledProcessError: Command '['/home/participant/verilator/bin/verilator', '-sv', '--cc', '--exe', '--build', '-j', '2', '-Wno-fatal', '-Wno-WIDTH', '-Wno-DECLFILENAME', '-Wno-UNOPTFLAT', '--Mdir', '/tmp/poc_vuln005_pkpxb0m5/obj_dir', '-I', '/home/participant/opentitan/hw/ip/prim/rtl', '--top-module', 'tb', '/tmp/vuln_verify/VULN-005/edn_pkg_stub.sv', '/tmp/vuln_verify/VULN-005/tb_force_masks.sv', '/tmp/vuln_verify/VULN-005/sim_main.cpp', '/home/participant/opentitan/hw/ip/prim/rtl/prim_util_pkg.sv', '/home/participant/opentitan/hw/ip/aes/rtl/aes_reg_pkg.sv', '/home/participant/opentitan/hw/ip/aes/rtl/aes_pkg.sv', '/home/participant/opentitan/hw/ip/prim/rtl/prim_trivium_pkg.sv', '/home/participant/opentitan/hw/ip/prim/rtl/prim_trivium.sv', '/home/participant/opentitan/hw/ip/aes/rtl/aes_prng_masking.sv']' returned non-zero exit status 1.
```
