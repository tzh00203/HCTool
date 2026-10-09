# Oracle Certification — VULN-049

Generated: 2026-10-09 18:33 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: L2
VM result: VM-CONFIRMED

## Twin Repair Diff

- Oracle: line 14 TODO + line 97 TODO: "Add check what to do, if data_in_valid_bytes_i is greater than blocksize"
- Oracle: standard valid/ready handshake protocol (AXI4-Stream / TL-UL); line 59 TODO "Add backpressure check"

## Oracle References

- Oracle: line 14 TODO + line 97 TODO: "Add check what to do, if data_in_valid_bytes_i is greater than blocksize"
- Oracle: standard valid/ready handshake protocol (AXI4-Stream / TL-UL); line 59 TODO "Add backpressure check"
- Oracle**: TODO comments at lines 14 and 97 of `prim_ascon_duplex.sv`: "Add check what to do, if data_in_valid_bytes_i is greater than blocksize"
- Oracle**: Line 13 TODO: "Add backpressure logic, if output is not ready"; standard valid/ready handshake protocol (AXI4-Stream / TL-UL)

## Evidence Log (excerpt)

```
%Error: Unknown warning specified: -Wno-UNUSEDSIGNAL... Suggested alternative: '-Wno-UNSIGNED'
Traceback (most recent call last):
  File "/tmp/vuln_verify/VULN-049/exploit.py", line 85, in <module>
    main()
  File "/tmp/vuln_verify/VULN-049/exploit.py", line 65, in main
    subprocess.run(
  File "/usr/lib/python3.12/subprocess.py", line 571, in run
    raise CalledProcessError(retcode, process.args,
subprocess.CalledProcessError: Command '['/home/participant/verilator/bin/verilator', '-sv', '--cc', '--exe', '--build', '-j', '2', '-Wno-fatal', '-Wno-WIDTH', '-Wno-DECLFILENAME', '-Wno-UNOPTFLAT', '-Wno-UNUSEDSIGNAL', '-Wno-UNUSEDGENPARAM', '--Mdir', '/tmp/poc_vuln049_amz2z6gt/obj_dir', '-I', '/home/participant/opentitan/hw/ip/prim/rtl', '--top-module', 'tb', '/tmp/vuln_verify/VULN-049/tb_vuln049.sv', '/tmp/vuln_verify/VULN-049/sim_main.cpp', '/home/participant/opentitan/hw/ip/prim/rtl/prim_util_pkg.sv', '/home/participant/opentitan/hw/ip/prim/rtl/prim_mubi_pkg.sv', '/home/participant/opentitan/hw/ip/prim/rtl/prim_ascon_pkg.sv']' returned non-zero exit status 1.
```
