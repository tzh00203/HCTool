# VULN-058: HMAC done_state cool-down counter not reset

## Verdict
**[poc-success]** L2 fidelity

## Finding
In `hmac.sv`, the `done_state` FSM's `DoneAwaitHashComplete` state has no
assignment for `cool_down_ct_d` when `hash_running=1`. Since `cool_down_ct_d`
has no default value at the top of the `always_comb` block, it latches to
`cool_down_ct_q` — the partial cool-down count is **retained** instead of being
reset to 0 when the hash engine re-starts while in the cool-down wait.

This means if `hash_running` goes high (hash re-started) partway through the
cool-down period, then drops again, the counter **resumes from its stale
partial value** rather than starting from 0. This shortens the effective
cool-down period on subsequent completion, potentially causing `hash_done_event`
to fire prematurely.

## Twin Fix
Add `cool_down_ct_d = 8'd0` in the else branch of `if (!hash_running)` within
`DoneAwaitHashComplete`:

```diff
 DoneAwaitHashComplete: begin
   if (!hash_running) begin
     if (cool_down_ct_q < 8'd127) begin
       cool_down_ct_d = cool_down_ct_q + 1'b1;
       hash_done_event = 1'b0;
       done_state_d = DoneAwaitHashComplete;
     end else begin
       hash_done_event = 1'b1;
       done_state_d = DoneAwaitCmd;
     end
-  end
+  end else begin
+    cool_down_ct_d = 8'd0;  // Oracle: DoneAwaitCmd line 155
+  end
 end
```

**Oracle**: `DoneAwaitCmd` already sets `cool_down_ct_d = 8'd0` (hmac.sv:155),
establishing the intended reset-when-idle pattern. The partial count is stale
when `hash_running` goes back high and must be discarded.

## Reproduction
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-058
bash build.sh
```

## Raw Output
```
DoneAwaitHashComplete + hash_running=1 + cool_down_ct_q=10:
  vuln cool_down_ct_d=10 (retains old value): YES
  twin cool_down_ct_d=0  (resets):           YES
CONFIRMED: hmac.sv DoneAwaitHashComplete cool_down counter not reset
  vuln: when hash_running=1 in DoneAwaitHashComplete, cool_down_ct_d
        is unassigned (latches to cool_down_ct_q) — partial count
        from prior !hash_running period is retained instead of reset.
        Counter resumes from stale value when hash_running drops again,
        shortening the cool-down period.
  twin: cool_down_ct_d = 8'd0 when hash_running=1 in
        DoneAwaitHashComplete (else branch added).
        Oracle: DoneAwaitCmd already sets cool_down_ct_d=0 (line 155),
        establishing the intended reset-when-idle pattern.
exit code: 1 (1 = finding confirmed)
```

## Fidelity
L2 (data-flow evidence): expression-level differential of `cool_down_ct_d`
next-state logic in `DoneAwaitHashComplete` with `hash_running=1`.
