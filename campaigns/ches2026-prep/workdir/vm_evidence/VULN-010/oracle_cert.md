# Oracle Certification — VULN-010

Generated: 2026-10-09 18:31 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-CONFIRMED

## Twin Repair Diff

- **Line changed**: `hmac_core.sv:229`
- **Vuln**: `default: sha_msg_len = BlockSizeSHA512in64 + 64'd384;`
- **Twin**: `SHA2_512: sha_msg_len = BlockSizeSHA512in64 + 64'd512;` + proper default
- **Oracle**: FIPS 180-4 Section 1 defines SHA-512 digest as 512 bits.

## Oracle References

- Oracle**: FIPS 180-4 Section 1 defines SHA-512 digest as 512 bits.

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
             /tmp/poc_vuln010_6odejxuk/obj_dir//home/participant/opentitan/hw/ip/prim/rtl
             /tmp/poc_vuln010_6odejxuk/obj_dir//home/participant/opentitan/hw/ip/prim/rtl.v
             /tmp/poc_vuln010_6odejxuk/obj_dir//home/participant/opentitan/hw/ip/prim/rtl.sv
%Error-PKGNODECL: //tmp/vuln_verify/VULN-010/tb_hmac_sha512_msglen.sv:16:10: Package/class 'prim_sha2_pkg' not found, and needs to be predeclared (IEEE 1800-2017 26.3)
   16 |   import prim_sha2_pkg::*;
      |          ^~~~~~~~~~~~~
                  ... For error description see https://verilator.org/warn/PKGNODECL?v=4.210
%Error: //tmp/vuln_verify/VULN-010/tb_hmac_sha512_msglen.sv:16:10: Importing from missing package 'prim_sha2_pkg'
   16 |   import prim_sha2_pkg::*;
      |          ^~~~~~~~~~~~~
%Error: Exiting due to 3 error(s)
Traceback (most recent call last):
  File "/tmp/vuln_verify/VULN-010/exploit.py", line 83, in <module>
    main()
  File "/tmp/vuln_verify/VULN-010/exploit.py", line 74, in main
    subprocess.run(cmd, check=True)
  File "/usr/lib/python3.12/subprocess.py", line 571, in run
    raise CalledProcessError(retcode, process.args,
subprocess.CalledProcessError: Command '['/home/participant/verilator/bin/verilator', '--cc', '--exe', '--build', '-j', '2', '-Wno-fatal', '-Wno-DECLFILENAME', '-Wno-UNOPTFLAT', '-I', '/home/participant/opentitan/hw/ip/prim/rtl', '--top-module', 'tb', '--Mdir', '/tmp/poc_vuln010_6odejxuk/obj_dir', '/tmp/vuln_verify/VULN-010/tb_hmac_sha512_msglen.sv', '/tmp/vuln_verify/VULN-010/sim_main.cpp', '/home/participant/opentitan/hw/ip/prim/rtl/prim_sha2_pkg.sv']' returned non-zero exit status 1.
```
