# 门控极性反转

## 根因

写使能/清除/告警的门控条件极性被反转：本该 `!error` 的地方写 `error`，
本该 valid 触发的地方变成 error 触发。行为完全颠倒但只改了一个操作符。

## 代码特征

- `we = addr_hit && reg_we && < polarity >` —— 同文件其他寄存器用一种极性，
  独此一个相反
- 清除/wipe 类操作挂在错误条件上（error 时才清，valid 写不清）
- `if (alert) ... else clear` 的分支互换

## 盲检方法

1. **同文件一致性检查**（最强信号）：reg_top 文件里所有寄存器的 we 表达式
   结构对比，极性异类即候选
2. 语义自问："这个动作应该在什么条件下发生？"——wipe 应该在合法写时发生；
   告警应该在错误时发生
3. hjson 的 swaccess 定义（"rw" 意味 valid 写必须生效）对照 RTL 门控

## GT 实例

- OT-008 hmac `hmac_reg_top.sv`：`wipe_secret_we = addr_hit[8] && reg_we && reg_error`
  （应为 `!reg_error`，同文件所有其他 we 都是 `!reg_error`）。
  结果：合法 SW 读 key-hash 不触发 wipe（密钥状态存活），总线错误反而触发。
  盲检命中，组合 micro-tb 动态确认（vuln we=0 / twin we=1）。

## 动态验证

组合逻辑洞不需要时序 tb：直接把条件表达式抄进 micro-tb，
vuln vs twin 各算一遍，常数输入下比较输出。hmac_wipe_gate 模式，10 分钟建好。
