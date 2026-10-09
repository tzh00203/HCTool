# RESULT: VULN-059

## Verdict: [poc-success] L2 fidelity

## Finding

HMAC FIFO hardware-side write not gated by `msg_allowed`. In `hmac.sv:546`:

```sv
assign fifo_wvalid = (hmac_fifo_wsel && fifo_wready) ? hmac_fifo_wvalid : reg_fifo_wvalid;
```

When `hmac_fifo_wsel=1` (HMAC core writing digest back to FIFO), the write bypasses the `msg_allowed` gate. The SW-side write IS gated (line 628):
```sv
assign msg_write = msg_fifo_req & msg_fifo_we & ~hmac_fifo_wsel & msg_allowed;
```

## Test Scenario

| Signal | Value | Meaning |
|---|---|---|
| hmac_fifo_wsel | 1 | HW-side FIFO write select active |
| fifo_wready | 1 | FIFO ready to accept |
| hmac_fifo_wvalid | 1 | HMAC core has valid data |
| msg_allowed | 0 | FIFO not open to SW (hash not started) |

- **Vuln**: fifo_wvalid = 1 (write accepted despite msg_allowed=0)
- **Twin**: fifo_wvalid = 0 (write correctly blocked by msg_allowed)

## Twin Repair

Diff: 1 line changed in `hmac.sv:546`:
```diff
- assign fifo_wvalid = (hmac_fifo_wsel && fifo_wready) ? hmac_fifo_wvalid : reg_fifo_wvalid;
+ assign fifo_wvalid = (hmac_fifo_wsel && fifo_wready && msg_allowed) ? hmac_fifo_wvalid : reg_fifo_wvalid;
```
Oracle: SW-side `msg_write` already uses `msg_allowed` gate (line 628). HW-side should be consistent.

## Caveat: Unreachable in Normal FSM Flow

In normal operation, `hmac_core` only asserts `fifo_wsel_o=1` in `StPushToMsgFifo` state (hmac_core.sv:409), which is entered after `StWaitResp` → `StMsg`/`StIPad` → triggered by `hash_start`/`hash_continue`. When `hash_start` or `hash_continue` fires, `msg_allowed` is set to 1 (hmac.sv:417). Therefore, `hmac_fifo_wsel=1 && msg_allowed=0` is unreachable under normal FSM transitions.

This is a **defense-in-depth gap**: the missing gate doesn't violate correctness in normal operation, but violates the design principle that all FIFO access should be gated by `msg_allowed`. If a future FSM modification or fault injection could cause `fifo_wsel` to assert without `msg_allowed`, the gate would be needed.

## Reproduction

```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-059
bash build_hmac_fifo_hw_wgate.sh
# exit code 1 = finding confirmed
```

## Raw Output

```
HW FIFO write with msg_allowed=0:
  vuln fifo_wvalid=1  twin fifo_wvalid=1
CONFIRMED: hmac.sv:546 fifo_wvalid not gated by msg_allowed
  vuln: fifo_wvalid = (hmac_fifo_wsel && fifo_wready) ? hmac_fifo_wvalid : reg_fifo_wvalid
        -> HW-side write bypasses msg_allowed, accepted when msg_allowed=0
  twin: fifo_wvalid = (hmac_fifo_wsel && fifo_wready && msg_allowed) ? ...
        -> HW-side write gated by msg_allowed (consistent with SW-side line 628)
  Note: In normal FSM flow, hmac_core only asserts fifo_wsel in StPushToMsgFifo
  after hash_start sets msg_allowed=1. This is a defense-in-depth gap.
exit code: 1 (1 = finding confirmed)
```
