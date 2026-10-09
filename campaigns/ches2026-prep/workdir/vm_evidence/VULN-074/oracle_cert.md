# Oracle Certification — VULN-074

Generated: 2026-10-09 18:34 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: L2
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle**: `fatal_lc_fsm_err` is an FSM alert (SEC_CM: LC_CTRL.INTERSIG.MUBI), not a TL-UL integrity error; `intg_error[0]` and `intg_error[1]` are true bus integrity errors from `otp_ctrl_core_reg_top` and `tlul_adapter_sram`
- Oracle**: ALL other partitions have `integrity=1'b1`; VENDOR_TEST is the sole outlier. Uncorrectable ECC errors are critical regardless of partition integrity flag.
- Oracle**: DAI ErrorSt locks access; scrmbl ErrorSt clears internal state; sibling modules zero outputs in terminal error states
- Oracle**: DAI ErrorSt sets `fsm_err_o=1`; scrmbl ErrorSt sets `fsm_err_o=1`; KDI ErrorSt sets `fsm_err_o=1`; LCI is the sole FSM that omits `fsm_err_o` in ErrorSt
- oracle: DAI locks access, scrmbl clears state, sibling modules zero outputs in error states)
- Oracle correction**: Original finding claimed DAI sets `fsm_err_o=1` in ErrorSt — this was incorrect. DAI has the same omission pattern as LCI. The inconsistency is with scrmbl and KDI which do set it.

## Evidence Log (excerpt)

```
Traceback (most recent call last):
  File "/tmp/vuln_verify/VULN-074/exploit.py", line 62, in <module>
    main()
  File "/tmp/vuln_verify/VULN-074/exploit.py", line 38, in main
    r = subprocess.run(
        ^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/subprocess.py", line 548, in run
    with Popen(*popenargs, **kwargs) as process:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.12/subprocess.py", line 1026, in __init__
    self._execute_child(args, executable, preexec_fn, close_fds,
  File "/usr/lib/python3.12/subprocess.py", line 1955, in _execute_child
    raise child_exception_type(errno_num, err_msg, err_filename)
NotADirectoryError: [Errno 20] Not a directory: '/home/participant/verilator/bin/verilator/bin/verilator'
```
