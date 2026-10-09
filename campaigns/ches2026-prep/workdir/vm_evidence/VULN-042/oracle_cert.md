# Oracle Certification — VULN-042

Generated: 2026-10-09 18:58 UTC
VM verification exit code: 1 (1 = confirmed)
Local verdict: None
Fidelity: L3
VM result: VM-CONFIRMED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle: aes_pkg.sv comment pattern (every other RndCnst documents its gen-lfsr-seed.py command).
- Oracle: every other RndCnst in aes_pkg.sv documents its gen-lfsr-seed.py command; SharePerm is the sole exception

## Evidence Log (excerpt)

```
build_vm.sh: line 8: cd: /tmp/vuln_verify/VULN-042/../../../../../../opentitan_blind: No such file or directory
```
