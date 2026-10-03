# OpenTitan (Redbud) RTL — 安全猎洞笔记

## 目录速查

```
hw/ip/<ip>/
  rtl/           IP 核心 RTL（含 ibex 在 hw/vendor/lowrisc_ibex/）
  data/<ip>.hjson          寄存器规格 + sec_cm 声明
  data/<ip>_testplan.hjson 验证计划（行为预言机）
  data/<ip>_sec_cm_testplan.hjson  对策验证计划
  dv/            验证环境（vendored C 参考实现藏在 prim 的 dv/ 下）
hw/ip/prim/rtl/  原语库（prim_lc_sender、prim_count、prim_max_tree、sparse_fsm_flop...）
```

## SEC_CM 约定

- hjson `sec_cm: [NAME.KIND, ...]`，如 `KEY.SEC_WIPE`、`CTR.FSM.LOCAL_ESC`、`MSG.MASKING`
- RTL 内 `// SEC_CM: NAME.KIND` 注释锚点标实现位置
- 语义字典：SEC_WIPE=PRD 覆写 / LOCAL_ESC=错误态告警+停机 / MASKING=PRNG mask /
  DIFF=双轨 / SW_UNREADABLE=硬件不可读出 / TOKEN.*=token 校验

## 盲预言机地图（按产出排序）

1. **hjson 行为描述**（"performs a secure wipe"/"fatal"/"cannot recover"）→ RTL 逐条兑现
2. **in-file SVA**：注入者改代码忘改断言 / 直接降级断言——矛盾即洞
3. **in-file 注释**：注释声明规范行为、代码不做
4. **testplan**：声明的验证点在 RTL 无实现
5. **树内参考**：kmac_reduced.sv、prim dv/ 下 vendored ascon-c、兄弟模块
   （entropy_src 的 adaptp_ht vs markov_ht 同构对照）
6. **同文件一致性**：reg_top 所有 we 表达式极性、case 项、default 分支

## 12 IP 清单与要点

| IP | 关键文件 | 要点 |
|---|---|---|
| aes | aes_core/aes_cipher_core/aes_ctr/aes_key_expand/aes_shift_rows | SEC_WIPE 用 PRD；key schedule 差分；SVA 密 |
| hmac | hmac_core/hmac_reg_top | wipe gate 极性；SHA2 pad 长度 |
| ascon | ascon_core/prim_ascon_duplex | dv/ 有 ascon-c 参考；128a 分支多 |
| kmac | kmac_core + kmac_reduced.sv | reduced 即参考实现 |
| entropy_src | entropy_src_core + 各 *_ht.sv | 健康 HT 兄弟对照；fail 脉冲数据源 |
| keymgr | keymgr_ctrl | StCtrl 状态机；key_state 赋值链 |
| lc_ctrl | lc_ctrl_fsm/signal_decode/reg_pkg | case 查重；token 位宽；clkbyp 断言 |
| otp_ctrl | otp_ctrl_pkg + core | 混淆常量必须脚本解码 |
| rom_ctrl | rom_ctrl + scramble_image.py | ECC 检查位；错误时 rvalid |
| uart | uart_core | LSIO 触发语义 vs hjson |
| ibex (pmp) | ibex_pmp.sv | req_err 数据源；lock 检查；debug 窗口 |
| ibex (csrs) | ibex_cs_registers.sv | 特权检查；mseccfg sticky；csr_pmp_addr 字节形 |

## Verilator 构建要点

- 4.210：`--cc --exe -Wno-fatal --top-module tb -Mdir obj`，
  生成 .mk 后必须 `sed VERILATOR_ROOT`，见 verilator-4.210-caveats
- prim 技术单元在 ibex dv stub 路径：`hw/vendor/lowrisc_ibex/dv/uvm/core_ibex/common/prim/`
  （blind 树里没有 prim_flop/prim_buf 本体，用 vendor dv 版）
- pkg 依赖链断裂：stub 包优先（edn/keymgr/lc_ctrl），拉真包会拖出 entropy 全家
- 文件顺序：packages → prim 原语 → IP 叶子 → twin → tb → cpp
