# RESULT: VULN-026

## Verdict: [poc-success]

## Finding
otp_ctrl_dai.sv:309 `default: ;` in IdleSt's `unique case (dai_cmd_i)` silently swallows 5 invalid command encodings (3'b000, 3'b011, 3'b101, 3'b110, 3'b111 out of 8 possible 3-bit values). When an invalid command is received with dai_req_i=1, the FSM stays in IdleSt with fsm_err_o=0 — no error is reported.

## Twin Fix
Replace `default: ;` with:
```systemverilog
default: begin
  state_d = ErrorSt;
  fsm_err_o = 1'b1;
end
```
Oracle: line 278-279 comment "Invalid commands trigger a CmdInvErr" + outer default: pattern at line 681-684.

## Evidence
- Fidelity: L2 (combinational micro-tb, data-flow evidence)
- Test: inject invalid command encoding 3'b011 with dai_req=1 while FSM in IdleSt
- vuln: state_d = IdleSt, fsm_err_o = 0 (invalid command silently ignored)
- twin: state_d = ErrorSt, fsm_err_o = 1 (invalid command correctly caught)
- Differential output: confirmed

## Commands
```bash
cd /data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-026
bash build_otp_dai_cmd.sh
```

## Raw Output
```
Invalid cmd 3'b011 with dai_req=1 in IdleSt:
  vuln: state stays IdleSt=YES  fsm_err=0
  twin: state jumps ErrorSt=YES  fsm_err=1=YES
CONFIRMED: otp_ctrl_dai.sv:309 default: ; swallows 5 invalid dai_cmd_e encodings
  vuln: IdleSt unique case (dai_cmd_i) empty default -> FSM stays IdleSt, fsm_err_o=0
  twin: default branch -> ErrorSt + fsm_err_o=1 (oracle: line 278-279 comment,
        outer default: pattern at line 681-684)
exit code: 1 (1 = finding confirmed)
```

## Deliverables
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-026/tb_otp_dai_cmd.sv`
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-026/sim_main.cpp`
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-026/build_otp_dai_cmd.sh`
- `/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow/campaigns/ches2026-prep/workdir/poc/VULN-026/exploit.py`
