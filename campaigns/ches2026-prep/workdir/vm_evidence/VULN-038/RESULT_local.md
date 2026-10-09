# RESULT: VULN-038

## Verdict: [poc-success]

## Finding

UART `lsio_trigger_o` unconditionally assigned constant `1'b1` in `uart_core.sv:362`.

After reset, `lsio_trigger_o` is always driven to `1'b1`, completely ignoring
`event_rx_watermark` and `event_tx_watermark` threshold conditions. The file's own
comment (lines 353-354) states: "Trigger asserted when data thresholds are considered met."
The unconditional constant assignment violates this specification — the LSIO DMA
handshake trigger fires even when no FIFO watermark thresholds are met.

## Twin Repair

Change line 362 from:
```systemverilog
lsio_trigger_o <= 1'b1;
```
to:
```systemverilog
lsio_trigger_o <= event_rx_watermark | event_tx_watermark;
```

Oracle: uart_core.sv lines 353-354 comment — "Trigger asserted when data thresholds are considered met."

## Evidence

- **TB type**: combinational micro-tb (tb_comb)
- **Fidelity**: L2 (data-flow evidence)
- **Stimulus**: event_rx_watermark=0, event_tx_watermark=0 (no thresholds met)
- **Vuln behavior**: lsio_trigger_o = 1 (always fires)
- **Twin behavior**: lsio_trigger_o = 0 (correctly squelched)
- **Differential**: vuln fires unconditionally, twin respects watermark conditions

## Execution

```
$ bash build.sh
No watermarks met (rx_wm=0, tx_wm=0):
  vuln lsio_trigger_o=1 (always fires): YES
  twin lsio_trigger_o=0 (correctly squelched): YES
CONFIRMED: uart_core.sv:362 lsio_trigger_o <= 1'b1 (unconditional constant)
  vuln: trigger always fires regardless of watermark conditions
  twin: trigger fires only when event_rx_watermark|event_tx_watermark (oracle: lines 353-354)
exit code: 1 (1 = finding confirmed)
```

## Deliverables

| File | Path |
|------|------|
| tb | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-038/tb_uart_lsio.sv` |
| sim_main | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-038/sim_main.cpp` |
| build | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-038/build.sh` |
| exploit | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-038/exploit.py` |
| RESULT | `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-038/RESULT.md` |
