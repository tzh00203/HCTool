# Oracle Certification — VULN-057

Generated: 2026-10-09 18:33 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: L2
VM result: VM-CONFIRMED

## Twin Repair Diff

- hmac.sv:211: `assign wipe_v = reg2hw.wipe_secret.q;` → `assign wipe_v = prd_wipe_v_i;`
- Added `prd_wipe_v_i` input port (32-bit, from entropy/CSRNG)
- Added SEC_CM comments: `KEY.SEC_WIPE`, `DIGEST.SEC_WIPE`
- Oracle: AES KEY.SEC_WIPE / DATA_REG.SEC_WIPE pattern (PRD from EDN)

## Oracle References

- Oracle: AES KEY.SEC_WIPE / DATA_REG.SEC_WIPE pattern (PRD from EDN)
- Oracle: AES KEY.SEC_WIPE uses prd_clearing_key_i from EDN/CSRNG
- SEC_CM mismatch
- SEC_CM comments
- SEC_CM only
- SEC_CM countermeasures
- SEC_CM declaration
- SEC_CM declarations

## Evidence Log (excerpt)

```
Traceback (most recent call last):
  File "/tmp/vuln_verify/VULN-057/exploit.py", line 49, in <module>
    main()
  File "/tmp/vuln_verify/VULN-057/exploit.py", line 26, in main
    shutil.copy2(os.path.join(d, f), os.path.join(tmp, f))
  File "/usr/lib/python3.12/shutil.py", line 475, in copy2
    copyfile(src, dst, follow_symlinks=follow_symlinks)
  File "/usr/lib/python3.12/shutil.py", line 260, in copyfile
    with open(src, 'rb') as fsrc:
         ^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/participant/opentitan/tb_hmac_wipe_v_source.sv'
```
