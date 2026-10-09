# Oracle Certification — VULN-052

Generated: 2026-10-09 18:58 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle: `health_test_window` is a window size parameter, semantically unrelated to bit selection. No in-tree comment, SVA, or spec justifies the mask. `rng_bit_sel` should be a direct passthrough from the SW configuration register.
- oracle: health_test_window is window size, semantically unrelated to bit selection

## Evidence Log (excerpt)

```
MAKE FAILED
Vtb.mk:55: /home/participant/verilator/share/verilator/include/verilated.mk: No such file or directory
make: *** No rule to make target '/home/participant/verilator/share/verilator/include/verilated.mk'.  Stop.
```
