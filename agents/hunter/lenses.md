# hunter 六大 lens 操作手册

先读知识库 `knowledge/vuln-patterns/rtl/`（12 模式，每个含盲检方法+GT 实例）。
本手册是执行顺序与产出要求。

## L1 SEC_CM-vs-RTL（产出最高的预言机，盲 eval 命中 5 个 GT）

1. 从预言机目录取 SEC_CM 映射表
2. 对每条声明读 RTL 锚点上下文 30 行，核对语义字典：
   - SEC_WIPE → 清除值必须 prd_clearing_*（全 0 = 洞）
   - LOCAL_ESC → 错误态无条件 alert（被门控/延迟 = 洞）
   - MASKING → mask 来自 PRNG/LFSR（常数 = 洞）
   - DIFF/双轨 → 两轨都参与，无 break/短路
   - TOKEN/比较类 → 全位宽参与
3. 锚点缺失的 SEC_CM 直接列候选

## L2 hjson-spec-vs-RTL

1. 取预言机目录"行为性描述句"表
2. 逐句找 RTL 实现点，验证：TRIGGER 真有效果 / escalate 真拉 fatal alert /
   "cannot recover" 真不可恢复 / hwext 寄存器 we/re/de/d/q 五件套完整
3. 特别注意：wipe/清除语义挂在什么条件下（合法写？错误？极性）

## L3 树内参考对比

1. 取预言机目录"树内参考"表
2. 兄弟模块逐端口对照（一个用 thresh 一个不用 = 死对策）
3. 参考实现数据通路走查（kmac_reduced 的 mask 机制 vs kmac 本体）
4. vendored C 参考（ascon-c）留作 dyn-verify 的 DPI 底座——把路径记进候选

## L4 结构 lint

1. 端口清单三方对照：模块端口 vs 实例化连线 vs hjson/文档文字引用——缺失即候选
2. case 值查重（SV first-match-wins，重复项 = 高危，lc LcStProd 案例）
3. default 分支必须是安全侧
4. 声明未用信号/端口（lint 级扫描：grep 端口名在模块体内的出现次数）

## L5 常量折叠（混淆常量必须脚本，禁心算）

1. 识别混淆：位操作装饰的 localparam、共享 decode 函数
2. 写 Python：常量逐位抄入 → 移植 decode → 与期望值 bit-exact 比对
3. 期望值来源：枚举定义、兄弟常量模式、文档
4. **"或上某位"几乎必然改变解码结果——"语义等价"结论一律非法**（OT-017/018）

## L6 SCA 结构

1. 密码数据通路的中间信号是否 op 依赖（变量移位量、条件 mask mux、op 路径选择）
2. 对照：正常设计两条固定路径（FWD/INV 各一套），异常设计一条路径+操作数切换
3. 候选标注"功能正确但 SCA 弱化"，验证型选时序 tb（对照移位寄存器差分，
   redbud-5 的 tb_aes_shift_rows 模式）

## 执行纪律

- 每个 lens 跑完立刻写候选进 candidates.md（增量，防中断丢工）
- lens 之间交叉：L1 的候选用 L2/L3 的预言机二次佐证 → 升 [major]
- 完成所有 lens 后在 candidates.md 头部写覆盖摘要：
  扫了哪些文件、每个 lens 产出几条、哪些区域没覆盖到（诚实申报）
