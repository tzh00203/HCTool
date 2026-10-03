# 预言机目录格式（oracle-scout 产出合同）

文件：`workdir/oracle-inventory/<ip>.md`

```markdown
# <ip> 盲预言机目录

## 元信息
- 树: $OT_TREE（绝对路径）
- 扫描范围: hw/ip/<ip>/{rtl,data,doc}（+ 特例：prim/ascon 路径、ibex vendor 路径）
- SEC_CM 声明数: N / SVA 数: M / testplan 条目数: K

## 一、SEC_CM 声明 ↔ RTL 锚点
| # | SEC_CM 声明 (hjson:line) | RTL 锚点 (file:line) | 检验要点 |
|---|---|---|---|
| 1 | KEY.SEC_WIPE (aes.hjson:142) | aes_core.sv:685 // SEC_CM: KEY.SEC_WIPE | 清除值必须来自 prd_clearing_*，非常数 |

（锚点缺失的行也要列，RTL 锚点列写 "缺失!"——本身就是候选）

## 二、行为性描述句（hjson 原文 → 检验点）
| # | hjson 原文 (file:line) | 检验点 |
|---|---|---|
| 1 | "Performs a secure wipe of sensitive data" (ascon.hjson:588) | TRIGGER.WIPE 后 key/nonce/state 必须被清 |

## 三、SVA 清单（行为合同）
| # | 断言 (file:line) | 内容摘要 | 约束的预期行为 |
（注意标注哪些断言被注释/降级）

## 四、树内参考
| # | 参考物 (绝对路径) | 类型（兄弟模块/参考实现/规范注释） | 可对比什么 |

## 五、特殊结构提示
（重复 case 值风险点、参数化位宽 vs 魔法数、声明未用端口候选——按 IP 实况填）
```

## 质量线

- 每行都有 file:line，可一键跳转
- 检验要点必须具体到"看什么信号等于什么值"，不写"检查正确性"这类空话
- SEC_CM 声明一个不漏——这是盲检产出最高的预言机类别
