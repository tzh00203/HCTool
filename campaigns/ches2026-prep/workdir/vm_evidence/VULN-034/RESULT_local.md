# RESULT: VULN-034

## Verdict
**[poc-success]** AES cipher core state_sel default conditionalized — for AES-128/AES-192, illegal state_sel causes self-hold instead of PRD clearing. L2 fidelity.

## Vulnerability
- **File**: `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind/hw/ip/aes/rtl/aes_cipher_core.sv`
- **Line**: 253
- **Code**: `default: state_d = (key_len_i == AES_256) ? prd_clearing_state_i : state_d;`
- **Root Cause**: sec-cm-mismatch (SEC_CM: DATA_REG.SEC_WIPE)
- **Impact**: For AES-128/AES-192, when `state_sel` takes an invalid/spurious value (FI or encoding error), the state register self-holds (`state_d = state_d`) instead of being cleared with pseudo-random data. This means the previous state (potentially containing key material) survives the "secure wipe" countermeasure.

## Twin Fix
- **Line**: 253
- **Original**: `default: state_d = (key_len_i == AES_256) ? prd_clearing_state_i : state_d;`
- **Fixed**: `default: state_d = prd_clearing_state_i;`
- **Oracle**: STATE_CLEAR case (line 252) uses `prd_clearing_state_i`; `key_full_sel` default (line 444) uses `prd_clearing_key_i` unconditionally; SEC_CM: DATA_REG.SEC_WIPE comment on line 245.

## Verification
- **TB Type**: tb_comb (combinational micro-tb)
- **Fidelity**: L2 (data flow evidence)
- **Stimulus**: Inject illegal `state_sel` value, AES-128 mode, with `prd_clearing_state != state_q`
- **Success Criteria**: vuln `state_d = state_q` (retains old state, deviation from secure expectation); twin `state_d = prd_clearing_state_i` (unconditional PRD clear)

## Execution Evidence

### Command
```bash
bash /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-034/build_aes_state_default.sh
```

### Raw Output
```
AES-128 illegal state_sel: vuln retains state_q: YES  twin clears with PRD: YES
CONFIRMED: aes_cipher_core.sv:253 state_sel default conditionalized
  vuln: default: state_d = (key_len_i==AES_256) ? prd_clearing_state_i : state_d
        For AES-128/AES-192, state_d self-holds (retains state_q, no PRD clear)
  twin: default: state_d = prd_clearing_state_i (unconditional PRD clear)
  Oracle: STATE_CLEAR case uses prd_clearing_state_i; key_full_sel default
  uses prd_clearing_key_i unconditionally; SEC_CM: DATA_REG.SEC_WIPE
exit code: 1 (1 = finding confirmed)
```

### Exit Code
1 (finding confirmed)

## Deliverables
- `tb_aes_state_default.sv` — combinational micro-tb (vuln + twin expression comparison)
- `build_aes_state_default.sh` — Verilator build script
- `sim_main.cpp` — C++ simulation driver
- `exploit.py` — PoC entry (redbud mode)
