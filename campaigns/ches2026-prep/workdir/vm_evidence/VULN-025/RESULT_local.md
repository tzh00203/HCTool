# RESULT: VULN-025

## Verdict: [poc-success] — finding confirmed

## Vulnerability
rom_ctrl.sv:260-261 BUS.LOCAL_ESC rvalid leak: `bus_rom_rvalid` expression
uses `(bus_rom_rvalid_raw | bus_rom_req) & ~(internal_alert & ~bus_rom_req)`.
When `internal_alert=1` AND `bus_rom_req=1`, the alert suppression is bypassed
because `~(1 & ~1) = ~0 = 1`, so `bus_rom_rvalid=1` — ROM response leaks
through despite active alert.

## Twin Fix
```sv
assign bus_rom_rvalid = bus_rom_rvalid_raw & ~internal_alert;
```
Oracle: BusLocalEscChk_A SVA (line 548) asserts `Invalid => !bus_rom_rvalid`;
NoReadsBeforeDone_A SVA (line 538) asserts `!done => !bus_rom_rvalid`;
comment line 251 "response signal muxing and alert suppression logic".

## Fidelity: L2 (combinational micro-tb, data-flow evidence)

## Evidence

### Test Inputs
- `internal_alert = 1` (alert active, e.g., FSM in Invalid state)
- `bus_rom_req = 1` (bus ROM request pending)
- `bus_rom_rvalid_raw = 0` (no real ROM data ready)

### Observed Behavior
- **Vuln**: `(0|1) & ~(1&~1) = 1 & 1 = 1` — rvalid leaks through
- **Twin**: `0 & ~1 = 0` — correctly suppressed per BUS.LOCAL_ESC

### Build & Run
```
bash build_rom_ctrl_rvalid.sh
```

### Raw Output
```
internal_alert=1, bus_rom_req=1, bus_rom_rvalid_raw=0
  vuln rvalid leaks:    YES
  twin rvalid suppressed: YES
CONFIRMED: rom_ctrl.sv:260-261 bus_rom_rvalid leaks when internal_alert=1 & bus_rom_req=1
  vuln: (rvalid_raw|req) & ~(alert&~req) = (0|1)&~(1&0) = 1 — rvalid leaks through
  twin: rvalid_raw & ~alert = 0 & 0 = 0 — correctly suppressed per BUS.LOCAL_ESC
  Oracle: BusLocalEscChk_A SVA, NoReadsBeforeDone_A SVA, alert suppression comment
exit code: 1 (1 = finding confirmed)
```

### Exit Code: 1 = finding confirmed
