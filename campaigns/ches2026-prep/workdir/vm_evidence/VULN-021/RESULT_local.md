# RESULT: VULN-021

## Verdict
**[poc-success]** L2 fidelity

## Finding
ibex_pmp.sv:258 `debug_address_range_match` uses bitwise OR (`|`) instead of AND (`&`)
with `~DmAddrMask`. The expression `(addr | ~DmAddrMask) == DmBaseAddr` always produces
`0xFFFFFxxx` (because `~DmAddrMask = 0xFFFFF000` has upper 20 bits set, OR forces them
to 1), which can never equal `DmBaseAddr = 0x1A110000`. Therefore `debug_address_range_match`
is permanently 0, and the debug-module address window never matches.

Consequence: `debug_mode_allowed_access[c] = debug_mode_i & debug_address_range_match`
is always 0, so PMP bypass for the debug-module address range (RISC-V Debug Spec A.2)
is completely dead — even in debug mode, accesses to the debug-module address range go
through normal PMP checking instead of being automatically allowed.

## Reproduction
```bash
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-021/build_pmp_dbgwin.sh
```

## Raw Output
```
PMP debug_address_range_match (addr=0x1A110040, DmBaseAddr=0x1A110000):
  vuln_deviation: YES
  twin_secure:    YES
CONFIRMED: ibex_pmp.sv:258 debug_address_range_match uses | instead of &
  vuln: (addr | ~DmAddrMask) == DmBaseAddr → 0xFFFFF040 != 0x1A110000 → 0
  twin: (addr & ~DmAddrMask) == DmBaseAddr → 0x1A110000 == 0x1A110000 → 1
  Debug window never matches in vuln, bypassing PMP for debug-module range.
exit code: 1 (1 = finding confirmed)
```

## Twin Repair Diff
Only change: line 258, replace `|` with `&`:

```systemverilog
// Vuln (line 258):
debug_address_range_match = ((pmp_req_addr_i[c][31:0] | ~DmAddrMask) == DmBaseAddr);

// Twin (fixed):
debug_address_range_match = ((pmp_req_addr_i[c][31:0] & ~DmAddrMask) == DmBaseAddr);
```

Oracle: RISC-V Debug Specification Section A.2 — the debug module address range
is `[DmBaseAddr, DmBaseAddr + ~DmAddrMask]`; an address matches iff its upper
bits (masked by `~DmAddrMask`) equal `DmBaseAddr`. This requires AND masking,
not OR. Also confirmed by `ibex_pmp_twin` in `examples/ibex_pmp/` (verified pattern).

## Files
- tb: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-021/tb_pmp_dbgwin.sv`
- sim_main: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-021/sim_main.cpp`
- build: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-021/build_pmp_dbgwin.sh`
- exploit: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-021/exploit.py`
