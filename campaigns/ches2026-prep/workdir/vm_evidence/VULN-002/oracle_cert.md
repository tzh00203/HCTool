# Oracle Certification — VULN-002

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
      |     ^~~
%Error: //tmp/vuln_verify/VULN-002/ibex_pmp_twin.sv:144:21: syntax error, unexpected IDENTIFIER
  144 |     for (int r = 0; r < PMPNumRegions; r++) begin
      |                     ^
%Error: //tmp/vuln_verify/VULN-002/ibex_pmp_twin.sv:220:7: syntax error, unexpected always_comb
  220 |       always_comb begin
      |       ^~~~~~~~~~~
%Error: //tmp/vuln_verify/VULN-002/ibex_pmp_twin.sv:246:7: syntax error, unexpected always_comb
  246 |       always_comb begin
      |       ^~~~~~~~~~~
%Error: //tmp/vuln_verify/VULN-002/ibex_pmp_twin.sv:257:5: syntax error, unexpected always_comb
  257 |     always_comb begin
      |     ^~~~~~~~~~~
%Error: //tmp/vuln_verify/VULN-002/ibex_pmp_twin.sv:269:5: syntax error, unexpected always_comb
  269 |     always_comb begin
      |     ^~~~~~~~~~~
%Error: //tmp/vuln_verify/VULN-002/ibex_pmp_twin.sv:298:5: syntax error, unexpected always_comb
  298 |     always_comb begin
      |     ^~~~~~~~~~~
%Error: //tmp/vuln_verify/VULN-002/ibex_pmp_twin.sv:309:3: syntax error, unexpected always_comb
  309 |   always_comb begin
      |   ^~~~~~~~~~~
%Error: //tmp/vuln_verify/VULN-002/ibex_pmp_twin.sv:315:3: syntax error, unexpected assign
  315 |   assign unused_csr_pmp_mseccfg_rlb = |unused_config_fields;
      |   ^~~~~~
%Error: //tmp/vuln_verify/VULN-002/tb_pmp_err.sv:15:10: Importing from missing package 'ibex_pkg'
   15 |   import ibex_pkg::*;
      |          ^~~~~~~~
%Error: //tmp/vuln_verify/VULN-002/tb_pmp_err.sv:22:13: syntax error, unexpected IDENTIFIER, expecting TYPE-IDENTIFIER
   22 |   ibex_pkg::pmp_cfg_t cfg [NUMR];
      |             ^~~~~~~~~
%Error: Exiting due to 26 error(s)
Traceback (most recent call last):
  File "/tmp/vuln_verify/VULN-002/exploit.py", line 84, in <module>
    main()
  File "/tmp/vuln_verify/VULN-002/exploit.py", line 65, in main
    subprocess.run(
  File "/usr/lib/python3.12/subprocess.py", line 571, in run
    raise CalledProcessError(retcode, process.args,
subprocess.CalledProcessError: Command '['/home/participant/verilator/bin/verilator', '-sv', '--cc', '--exe', '--build', '-j', '2', '-Wno-fatal', '-Wno-WIDTH', '-Wno-DECLFILENAME', '-Wno-UNOPTFLAT', '--Mdir', '/tmp/poc_vuln002_hs11abwh/obj_dir', '-I', '/tmp/vuln_verify/VULN-002', '--top-module', 'tb', '/tmp/vuln_verify/VULN-002/dv_fcov_macros.svh', '/tmp/vuln_verify/VULN-002/ibex_pmp_twin.sv', '/tmp/vuln_verify/VULN-002/tb_pmp_err.sv', '/tmp/vuln_verify/VULN-002/sim_main.cpp', '/home/participant/opentitan/hw/vendor/lowrisc_ibex/rtl/ibex_pkg.sv', '/home/participant/opentitan/hw/vendor/lowrisc_ibex/rtl/ibex_pmp.sv']' returned non-zero exit status 1.
```
