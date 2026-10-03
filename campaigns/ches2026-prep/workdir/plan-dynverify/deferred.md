# Deferred VULNs (超出 Batch 1 的 ≤4 节点限制)

生成时间: 2026-09-18
原因: 资源约束，每批 ≤4 并行验证节点。按 vulns.md 排序分批，Batch 1 处理 Critical VULN-001~004。
VULN-005 (Critical) 与 VULN-006~082 (High/Medium/Low) 延至后续批次。

## Batch 2 (next): Critical remainder + top High
- VULN-005 (Critical, AES SecAllowForcingMasks)
- VULN-006 (High, AES 密钥擦除用 key_expand_out)
- VULN-007 (High, AES DIP_CLEAR 用 data_in)
- VULN-008 (High, AES-256 密钥扩展被重写)

## Batch 3: High
- VULN-009 (High, HMAC wipe_secret_we 极性反转)
- VULN-010 (High, HMAC SHA2_512 长度计算错误)
- VULN-011 (High, HMAC WIPE_SECRET 读取泄露 key[0])
- VULN-012 (High, KMAC MSG.MASKING 常量替换)

## Batch 4: High
- VULN-013 (High, keymgr StCtrlInvalid 暴露 key_state_q)
- VULN-014 (High, Ascon WIPE 触发丢弃)
- VULN-015 (High, Ascon EDN 断开)
- VULN-016 (High, Ascon nonce_error 不阻塞)

## Batch 5: High
- VULN-017 (High, entropy_src markov fail_pulse 硬布零)
- VULN-018 (High, entropy_src SHA3 lc_escalate 硬布 Off)
- VULN-019 (High, entropy_src es_rng_src_valid 门控)
- VULN-020 (High, PMP MMWP 默认拒绝未实现)

## Batch 6: High
- VULN-021 (High, PMP debug 窗口 | 误用)
- VULN-022 (High, mseccfg sticky-one 缺失)
- VULN-023 (High, keymgr data_en FSM default)
- VULN-024 (High, lc_ctrl IdleSt 时钟旁路)

## Batch 7: High
- VULN-025 (High, rom_ctrl rvalid 泄漏)
- VULN-026 (High, otp_ctrl DAI empty default)
- VULN-027 (High, otp_ctrl scrmbl empty default)
- VULN-028 (High, otp_ctrl SVA 降级 + alert 未锁存)

## Batch 8: Medium
- VULN-029~032 (Medium)

## Batch 9: Medium
- VULN-033~036 (Medium)

## Batch 10: Medium
- VULN-037~040 (Medium)

## Batch 11~21: Low
- VULN-041~082 (Low, 每批 4 个)

---

## 统计

| 类别 | 范围 | 数量 |
|---|---|---|
| Batch 1 (已执行) | VULN-001~004 | 4 |
| Deferred | VULN-005~082 | 78 |
| **合计** | | **82** |
