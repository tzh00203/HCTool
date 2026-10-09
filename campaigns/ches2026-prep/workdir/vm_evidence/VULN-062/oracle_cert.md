# Oracle Certification — VULN-062

Generated: 2026-10-09 18:58 UTC
VM verification exit code: 0 (1 = confirmed)
Local verdict: None
Fidelity: None
VM result: VM-FAILED

## Twin Repair Diff

(see RESULT.md for twin diff details)

## Oracle References

- Oracle:** RISC-V PMP spec — NAPOT mask for granularity G fills G lower
- SEC_CM missing
- SEC_CM annotations
- SEC_CM anchors
- SEC_CM anchor

## Evidence Log (excerpt)

```
274:      fault_analysis_result = access_fault_check(csr_pmp_mseccfg_i.mmwp,
275:                                                 csr_pmp_mseccfg_i.mml,
304:    unused_config_fields[0] = csr_pmp_mseccfg_i.rlb;
308:  logic unused_csr_pmp_mseccfg_rlb;
309:  assign unused_csr_pmp_mseccfg_rlb = |unused_config_fields;

CONFIRMED: ibex_pmp.sv has ZERO SEC_CM anchors despite implementing
          security-critical PMP access checking with MML, MMWP, and
          lock bits. Missing: PMP.CFG.SW_NO_ACCESS, PMP.CFG.SW_REGWEN,
          PMP.MSECCFG.RLB

--- Finding 3: napot_mask truncation ---

[ibex_cs_registers.sv] napot_mask / pmp_addr_rdata logic:
1146:          assign pmp_addr_rdata[i] = pmp_addr[i];
1148:        end else if (PMPGranularity == 1) begin : g_pmp_g1
1154:            pmp_addr_rdata[i] = pmp_addr[i];
1162:        end else begin : g_pmp_g2
1166:            logic [PMPGranularity-2:0] napot_mask;
1167:            napot_mask = {(PMPGranularity){1'b1}};
1168:            pmp_addr_rdata[i] = {pmp_addr[i], napot_mask};

CONFIRMED: napot_mask width mismatch at:
  1167:            napot_mask = {(PMPGranularity){1'b1}};
  LHS: logic [PMPGranularity-2:0] (width = PMPGranularity-1)
  RHS: {(PMPGranularity){1'b1}}  (width = PMPGranularity)
  MSB of RHS truncated. Functional effect: all-1s assignment still
  produces all-1s in LHS, so no functional change for this case.
  However, NAPOT address readback in g_pmp_g2 always fills lower
  bits with all-1s regardless of stored address pattern.

=== VERIFICATION SUMMARY ===

F1 (RLB unused in ibex_pmp): CONFIRMED
F2 (SEC_CM missing anchors): CONFIRMED
F3 (napot_mask truncation):  CONFIRMED (info)

ALL FINDINGS CONFIRMED at L4 (static code walkthrough) fidelity.
F1/F2: sec-cm-mismatch confirmed. F3: informational (width mismatch, no functional impact).
Exit code: 0 (analysis complete, findings at L4 informational level)
```
