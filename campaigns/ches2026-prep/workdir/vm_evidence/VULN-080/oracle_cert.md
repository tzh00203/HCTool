# Oracle Certification — VULN-080

Generated: 2026-10-09 18:34 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle: sibling IP SEC_CM pattern — AES/KMAC/OTP all assert `fsm_err_o` in
- Oracle: SEC_CM convention —
- Oracle: parameter-zero error detection pattern in sibling IPs.
- Oracle: sibling IP SEC_CM patterns (AES/KMAC/OTP all assert fsm_err in default,
- SEC_CM gaps
- SEC_CM convention
- SEC_CM pattern
- SEC_CM patterns

## Evidence Log (excerpt)

```
Traceback (most recent call last):
  File "/tmp/vuln_verify/VULN-080/exploit.py", line 35, in <module>
    main()
  File "/tmp/vuln_verify/VULN-080/exploit.py", line 26, in main
    shutil.copy2(os.path.join(args.repo, f), os.path.join(td, f))
  File "/usr/lib/python3.12/shutil.py", line 475, in copy2
    copyfile(src, dst, follow_symlinks=follow_symlinks)
  File "/usr/lib/python3.12/shutil.py", line 260, in copyfile
    with open(src, 'rb') as fsrc:
         ^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/participant/opentitan/tb_uart_sec_cm.sv'
```
