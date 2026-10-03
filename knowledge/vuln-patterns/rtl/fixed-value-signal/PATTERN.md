# 安全信号被绑死常量

## 根因

安全输出/错误输出被硬编码为 0 或 1，使对策完全失效但接口看起来完好。
一行改动，影响是整个对策死亡。

## 代码特征

- `assign xxx_fail_o = 1'b0;` / `assign xxx_err_o = 1'b1;`（错误极性看语义）
- 条件输出的 else 分支直接给常数
- 信号在 sensitivity/逻辑中完全不被引用（`access_fail` 计算后被丢弃）
- 阈值/比较输入（`thresh_hi_i`）声明了但从未使用

## 盲检方法

1. grep 模块输出端口：`output logic` + 同名 `assign` 常数 → 立即候选
2. 对安全语义端口（`*_fail*`、`*_err*`、`*_alert*`、`*_req*`）全数核对数据源
3. 检查"声明未用"：输入端口在模块体内零引用（lint 工具或人工 grep）
4. 兄弟模块对照：同目录下同构模块（如 entropy_src 的各 health test）互相比较
   端口使用方式——一个用 thresh 一个不用，就是被杀死的那个

## GT 实例

- OT-025 ibex_pmp：`pmp_req_err_o` 被绑 0（同注入行还有另一半
  `access_fail = 1'b0`，即额外发现 unmatched-access fail-open）
- entropy_src markov HT：`test_fail_hi/lo_pulse_o` 绑 1'b0，
  阈值输入完全未用 —— 兄弟模块 adaptp_ht 对照发现，动态验证确认
  （喂交替位流 fail_hi 该跳不跳，健康测试死了）

## 动态验证要点

这类洞的 tb 最简单：直接驱动违规激励，看 fail 脉冲是否出现。
vuln 永不脉冲 + twin（恢复比较逻辑）脉冲 = 确认。
