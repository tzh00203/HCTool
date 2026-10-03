# SEC_CM 声明与 RTL 实现不匹配

## 根因

OpenTitan 的 hjson 里 `sec_cm:` 字段声明安全对策（如 `KEY.SEC_WIPE`、
`CTR.FSM.LOCAL_ESC`、`MSG.MASKING`），RTL 里对应 `// SEC_CM:` 注释锚点。
注入式漏洞最常落在"声明还在、实现被削弱"——因为删 hjson 字段太显眼，
改 RTL 一两行更隐蔽。

## 代码特征

- hjson `sec_cm:` 列表项在 RTL 中找不到对应实现（grep `SEC_CM:` 注释锚点缺失）
- 注释锚点在，但实现语义弱化：wipe 用常数 0 而非 PRD、mask 是全 1、
  LOCAL_ESC 态不拉 alert、比较被截断
- SEC_CM testplan (`*_sec_cm_testplan.hjson`) 声称验证的对策，对应 SVA 不存在或被降级

## 盲检方法（Rule 3 合规）

1. 从 `data/{ip}.hjson` 提取全部 `sec_cm:` 条目
2. 在 RTL 中找 `// SEC_CM: <name>` 注释锚点，逐条建立映射
3. 对每个锚点读上下文 30 行，验证实现与声明语义一致：
   - `SEC_WIPE` → 清除值必须是 `prd_clearing_*` 而非常数
   - `LOCAL_ESC` / `FSM.LOCAL_ESC` → 错误态必须无条件拉 alert
   - `*.MASKING` / `MASK` → mask 必须来自 PRNG/LFSR 且非常数
   - `*.DIFF` / 双轨检查 → 两轨都要参与比较，不允许 break/短路
   - `TOKEN.CTRL.MUX` / 比较类 → 位宽必须等于完整 token 宽度
4. 交叉 `data/{ip}_sec_cm_testplan.hjson`：声明的验证点在 testplan 有、在 RTL 无 = 高危

## GT 实例（blind-scan eval）

- OT-001 aes KEY.SEC_WIPE：key 清除用了 key-schedule 数据（可逆）而非 PRD —— 盲检命中
- OT-006 kmac MSG.MASKING：LFSR mask 被换成全 1 常数 —— 盲检命中
- OT-012 keymgr ECC key_state 未赋值（声明的 key 管理断链）—— 盲检命中
- OT-013 lc_ctrl TOKEN compare：128bit token 比较被截断到 32bit —— 盲检命中
- OT-016 lc_ctrl CLKBYP：断言允许了 Dev/Prod 态 bypass —— 盲检命中

这是盲检产出最高的预言机（5/27 GT 命中，且都是高severity）。

## 缓解识别

PRD 相关信号命名：`prd_clearing_data`、`sec_wipe`、`lc_escalate`、`alert_*`。
见到这些信号被常数替换或被门控绕过即候选。
