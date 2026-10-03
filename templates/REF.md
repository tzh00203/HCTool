# dyn-verify 模板库索引

## 骨架模板（本目录，填空即用）

| 模板 | 型 | 适用 |
|---|---|---|
| `tb_comb.sv.tmpl` | 组合 micro-tb | 门控极性/截断/常量绑定（L2 数据流实证） |
| `tb_seq.sv.tmpl` | negedge-FSM 时序 tb | FSM/数据通路/SEC_WIPE 类（L1 执行级） |
| `tb_dpi.sv.tmpl` | DPI 差分 | 密码功能洞，对照 vendored C 参考（L1） |
| `sim_main.cpp.tmpl` | C++ 驱动 | 三型通用：半拍驱动 + verdict 读取 |
| `build.sh.tmpl` | 构建脚本 | Verilator 4.210 全流程 |
| `exploit.py.tmpl` | PoC 入口 | redbud 模式，评委 VM 可跑 |

## 活样板（examples/ → blind_eval/dyn_verify，已验证）

| 案例 | 学什么 |
|---|---|
| `examples/hmac_wipe_gate` | 最小组合 tb：表达式抄进去直接比 |
| `examples/entropy_markov` | negedge 采样协议抓单拍脉冲；兄弟模块 twin |
| `examples/aes_core` | 大模块依赖清单组织（~45 文件）；XMR 探 data_in_prev_q |
| `examples/aes_data_out_reset` | 复位时序的 micro-tb 技巧（FSM 内驱动 rst） |
| `examples/aes_ctr` | leaf-module 隔离；SVA 违规计数当证据 |
| `examples/aes_force_masks` | 机制再定性：报告 High 被实验降到 Medium |
| `examples/ascon` | DPI 差分全流程：gcc 编 .c、绝对 .o、6 配置矩阵 |
| `examples/ascon_core` | reg2hw 结构体当 SW 驱动 |
| `examples/ibex_pmp` | 判定矩阵 + 随机 sweep + XMR 窗口探针 |

## stub 库（stubs/）

`edn_pkg_stub.sv` / `keymgr_pkg_stub.sv`（Shares=2, KeyWidth=256, hw_key_req_t）/
`lc_ctrl_pkg_stub.sv`（lc_tx_t: On=4'b0101/Off=4'b1010 + test 函数）。
用法：依赖链拖出 entropy/csrng 全家时，用 stub 替换真包。
注意 stub 必须在 import 它的文件**之前**进文件清单。

## 规矩

- **exit 1 = finding confirmed**（所有 build 脚本统一）
- twin 修复依据必须写注释（哪条树内预言机）
- 产出目录自包含（不依赖相对路径外的东西），exploit.py 接 `--repo`/`--verilator`
