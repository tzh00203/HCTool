# VULN-004 Verification Result

## Verdict: **[poc-success]**

## Fidelity Level: L2 (data-flow evidence, combinational micro-tb)

## Vulnerability
lc_ctrl_fsm.sv token comparison truncated from 128 bits to 32 bits, reducing
collision space from 2^128 to 2^32.

### Locations
- `lc_ctrl_fsm.sv:456` — TokenHashSt: `hashed_token_i[31:0] == hashed_token_mux[31:0]`
- `lc_ctrl_fsm.sv:497` — TokenCheck0St/TokenCheck1St: `hashed_token_i[31:0] == hashed_token_mux[31:0]`

## Twin Repair
Replace `hashed_token_i[31:0] == hashed_token_mux[31:0]` with
`hashed_token_i == hashed_token_mux` (full-width 128-bit comparison).

Oracle: `lc_ctrl_state_pkg::LcTokenWidth = 128`; `lc_token_t = logic[127:0]`.
The `[31:0]` slice is the anomaly — no other token comparison in OpenTitan
uses a width-sliced equality.

## Test Stimulus
Two 128-bit tokens sharing lower 32 bits, differing in upper 96 bits:
- TOKEN_A = 128'h0000_0000_0000_0000_0000_0000_DEAD_BEEF
- TOKEN_B = 128'hCAFE_BABE_0000_0000_0000_0000_DEAD_BEEF

## Results

```
vuln_match(truncated 32-bit): YES  twin_match(full 128-bit): YES(rejects)
CONFIRMED: lc_ctrl_fsm.sv:456,:497 token comparison truncated 128->32 bits
  vuln: hashed_token_i[31:0]==hashed_token_mux[31:0] -> collision (match=1)
  twin: hashed_token_i==hashed_token_mux -> correctly rejects (match=0)
  Collision space: 2^128 (intended) -> 2^32 (vuln)
  Oracle: lc_ctrl_state_pkg::LcTokenWidth=128
exit code: 1 (1 = finding confirmed)
```

## Build Command
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-004
bash build_lc_token_trunc.sh
```

## Exit Code
1 (finding confirmed — vuln behavior differs from twin)

## Deliverables
- `tb_lc_token_trunc.sv` — combinational micro-tb
- `sim_main.cpp` — C++ simulation driver
- `build_lc_token_trunc.sh` — Verilator build script
- `exploit.py` — redbud-mode PoC entry
