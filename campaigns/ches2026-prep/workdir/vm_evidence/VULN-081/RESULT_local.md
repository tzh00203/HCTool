# VULN-081 Dynamic Verification Result

## Verdict: [poc-success] L2 fidelity

## Finding

**UART rxilvl=7 sets rx_thresh_val to unreachable value, rx_watermark interrupt can NEVER fire.**

uart_core.sv:341 — when `uart_fifo_rxilvl > RxFifoDepthW - 1`, the threshold is set to
`{RxFifoDepthW{1'b1}}` (all-ones). With RxFifoDepth=64 (RxFifoDepthW=7), rxilvl=7 produces
rx_thresh_val=127. Since max rx_fifo_depth=64, `event_rx_watermark = (rx_fifo_depth >= 127)`
is always false — the watermark interrupt is permanently dead for this setting.

**L4 info: EnableRacl=1'b0 default (uart.sv:13) disables RACL entirely — all register
access permitted without role/policy checking.**

## Twin Fix

When rxilvl exceeds valid range, saturate at `RxFifoDepth - 2` instead of all-ones.
Oracle: line 347 already uses `RxFifoDepth - 2` for the explicit `RxFifoDepthW-1` case;
TX watermark (line 316-317) also saturates rather than using all-ones for out-of-range txilvl.

## Evidence

```
VULN-081: UART rxilvl=7 rx_watermark threshold test
  RxFifoDepth=64, RxFifoDepthW=7, rxilvl=7, fifo_depth=64
  vuln watermark never triggers: YES
  twin watermark triggers:       YES
CONFIRMED: uart_core.sv:341 rxilvl=7 sets rx_thresh_val={RxFifoDepthW{1'b1}}=127
  (unreachable: max rx_fifo_depth=64 for RxFifoDepth=64)
  -> rx_watermark interrupt can NEVER fire when rxilvl=7
  Twin: saturate at RxFifoDepth-2=62 (same as explicit RxFifoDepthW-1 case, line 347)
  L4 note: EnableRacl=1'b0 default (uart.sv:13) disables RACL, all access permitted
exit code: 1 (1 = finding confirmed)
```

## Build & Run Command

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-081
bash build_uart_rxilvl.sh
```

## Deliverables

| File | Description |
|---|---|
| `tb_uart_rxilvl.sv` | Combinational micro-tb (vuln vs twin dual expression) |
| `sim_main.cpp` | C++ driver |
| `build_uart_rxilvl.sh` | Verilator build script |
| `exploit.py` | Redbud-mode PoC entry |
