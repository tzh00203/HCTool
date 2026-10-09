# Oracle Certification — VULN-019

Generated: 2026-10-09 18:31 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle: upstream OpenTitan code has only `es_rng_src_valid = rng_valid`. The `entropy_data_reg_enable` bit controls the ENTROPY_DATA register read path (line 3045: `es_data_reg_rd_en = es_enable_fo[17] && efuse_es_sw_reg_en && entropy_data_reg_en_pfe`), NOT the RNG source validity. Gate is misapplied.
- Oracle: upstream OpenTitan code (es_rng_src_valid = rng_valid only)

## Evidence Log (excerpt)

```
Traceback (most recent call last):
  File "/tmp/vuln_verify/VULN-019/exploit.py", line 50, in <module>
    main()
  File "/tmp/vuln_verify/VULN-019/exploit.py", line 26, in main
    shutil.copy2(os.path.join(repo, f), os.path.join(td, f))
  File "/usr/lib/python3.12/shutil.py", line 475, in copy2
    copyfile(src, dst, follow_symlinks=follow_symlinks)
  File "/usr/lib/python3.12/shutil.py", line 260, in copyfile
    with open(src, 'rb') as fsrc:
         ^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/participant/opentitan/tb_es_rng_valid.sv'
```
