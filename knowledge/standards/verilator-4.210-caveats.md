# Verilator 4.210 已知坑（全部踩过，血泪清单）

## 语法/语义限制

1. **每个 initial 只允许一个时序控制**。不能 task 里多个 `@()`、不能顺序
   `@(posedge clk); ... @(posedge clk);`。解法：tb 写成 negedge 驱动的 FSM
   （`always_ff @(negedge clk)` + state reg），或 C++ 侧半拍驱动。
2. **无 `wait()`**。轮询改成 FSM 状态 + 计数超时。
3. **同一变量禁止混用阻塞/非阻塞赋值**。
4. **flop 求值顺序竞态**：同一 posedge eval 里，Verilator 按拓扑序求值 flop，
   下游 flop（prim_max_tree）会看到上游 flop（prim_count 清零）的**更新后**值。
   解法：把 DUT 原始脉冲作为 tb 输出端口暴露，C++ 在**每个 negedge 半拍 eval 后**
   采样，再进下一个 posedge（entropy_markov 的 fail 脉冲就是这么抓的）。

## 构建

5. 生成 .mk 后必须：`sed -i "s|VERILATOR_ROOT = .*|VERILATOR_ROOT = $VD/share/verilator|" obj/Vtb.mk`
6. 固定 flag 组：`--cc --exe -Wno-fatal -Wno-DECLFILENAME -Wno-UNOPTFLAT --top-module tb -Mdir obj`
7. 文件顺序敏感：packages → prim 原语 → IP 叶子 → twin → tb → cpp。
   import 的包必须在 import 者**之前**。
8. prim_flop/prim_buf 技术单元：blind 树没有本体，用
   `hw/vendor/lowrisc_ibex/dv/uvm/core_ibex/common/prim/` 的 DV 版。
9. 依赖链断裂用 stub 包（keymgr/edn/lc_ctrl），真包会拖出 entropy/csrng 全家。
   stub 里 lc_tx_t 枚举：On=4'b0101 / Off=4'b1010（多比特编码）。

## DPI

10. open-array 用 `svGetArrElemPtr1`。
11. DPI 的 .c 用 gcc 编译（Verilator 会用 C++ 编译导致 name mangling），
    传绝对 .o 路径进 verilator 命令行。
12. svdpi.h 在 `$VD/share/verilator/include/vltstd/`。

## IP 特定

13. ibex csr_pmp_addr_i 喂**字节形**（{pmpaddr, 2'b00}，见 ibex_cs_registers.sv:1265），
    word 形式会让 region matching 静默失败（看起来全不命中）。
14. aes_core 触发 KEY_IV_DATA_IN_CLEAR 从 IDLE 就行，不用先配 CTRL。
15. aes_prng_masking 常数 mask 需要全零重播种配合（Trivium 重设计里
    FORCE_MASKS 只置 allow_lockup_i，不门 data_update）——SCA 结论别下早。

## 采样协议（C++ 驱动模板）

```cpp
void half(Vtop& top, int clk) {
  top.clk_i = clk; top.eval();
}
// 循环体：
//   half(top, 0);  采样输出（negedge 后稳定）;
//   half(top, 1);  // posedge 推进
```
