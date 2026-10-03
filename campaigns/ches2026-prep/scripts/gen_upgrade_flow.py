#!/usr/bin/env python3
"""生成"证据升级"子流水线：16 个 GT 外 L3/L4 VULN 升级验证。

目标：把仅静态/脚本结论的发现升级到可达的最高证据档。
- 行为可仿真子项 → L2 组合 micro-tb（vuln vs twin 差分，exit 1）
- 属性/声明缺失 → L3 脚本证明（hjson 解析/grep 机器证据）
- 确实无法升级的 → 诚实保留原档位并说明原因
"""
from __future__ import annotations

from pathlib import Path

HARNESS = Path(__file__).resolve().parents[2].parent
CAMPAIGN = HARNESS / "campaigns" / "ches2026-prep"
W = CAMPAIGN / "workdir"

OT_TREE = "/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind"
VERILATOR = (
    "/data_hdd/tzh24/zgc4/projects/tools/logos/logos-workspace/contexts/"
    "targets/opentitan-ches2026/runtime-samples/verilator-4.210/v4.210"
)

# VULN -> (当前档, 标题摘要, 升级分析)
NOTES: dict[str, tuple[str, str, str]] = {
    "VULN-031": ("L4", "Ascon hjson 无 sec_cm 字段",
        "无可仿真行为。升级路径：L3 脚本证明——用 Python/yq 解析 ascon.hjson，机器证明 sec_cm 字段缺失"
        "（对比兄弟 IP 如 aes/hjson 的 sec_cm 结构作为预言机），输出可复核脚本+运行输出。"),
    "VULN-032": ("L4", "KMAC hjson 缺 MSG.MASKING SEC_CM 声明",
        "无可仿真行为（掩码常量 bug 本身已由 VULN-012 L2 验证）。升级路径：L3 脚本证明——解析 kmac.hjson "
        "countermeasures 列表，机器证明 MSG.MASKING 缺失而 RTL 存在 msg_mask 逻辑（grep 锚点）。"),
    "VULN-042": ("L3", "AES 5 个 RndCnst 混淆常量仅验置换完整性不验值",
        "当前已有脚本。升级路径：对每个常量完成 (a) 置换双射性机器验证 (b) 常量在 RTL 中的消费点追踪"
        "（不悬空、参与运算）(c) 若树内存在生成脚本/文档种子则交叉比对。无法比对上游（Rule 3）需明说。"),
    "VULN-043": ("L4", "AES canright_masked SBox 文档声明 REBECCA insecure",
        "可仿真！升级路径：L2 micro-tb——实例化 aes_sbox_canright_masked（或其核心组合逻辑），固定 mask=0，"
        "穷举 256 个输入比对 Canright 代数实现的输出与 AES SBox 标准查表值（预言机：FIPS-197 SBox 表，"
        "脚本内嵌）；再随机 mask 验证 masked 输出 = sbox(in)^mask 形式的分解正确性。差异即证明实现错误。"),
    "VULN-048": ("L4", "Ascon 无 SVA 断言 + reqParity ASSUME 被注释",
        "断言缺失本身无可仿真。升级路径：L3 脚本证明——grep 机器证据：对比兄弟 IP（如 aes/kmac）的 "
        "ASSERT 密度与 ascon RTL 的 ASSERT 计数；reqParity ASSUME 注释行号锚定。若 reqParity 信号在"
        "RTL 中有实际消费且注释后有行为差异，可尝试 L2。"),
    "VULN-049": ("L4", "Ascon valid_bytes>15 无范围检查 + data_out_ready_i unused",
        "valid_bytes 部分可仿真！升级路径：L2 micro-tb——驱动 valid_bytes=0..255 扫描，观察 out-of-range "
        "值（>15）时数据通路行为（是否产生非预期 word 使能/越界写）；twin 加范围钳位。"
        "data_out_ready_i unused 部分做 L3 elaboration/lint 证明。"),
    "VULN-054": ("L3", "entropy_src SHA3 EnMasking=0 + rand 全零",
        "可升级 L2！micro-tb：检查 SHA3 实例的 mask 输入在默认参数下是否恒零（Elaboration 后常量传播），"
        "或组合探测 sha3 mask 端口；对照 hjson SEC_CM 声明（预言机）。"),
    "VULN-057": ("L4", "HMAC wipe_v 来自 SW 非 PRD",
        "可仿真！升级路径：L2 micro-tb——wipe 触发时捕获实际写入 FIFO/寄存器的 wipe 向量值，"
        "vuln = SW 写入值，twin = PRD（预言机：hjson 'pseudo-random data' 措辞 + 兄弟 IP aes 的 "
        "prd_clearing 模式）。SEC_CM 声明部分保持 L3 脚本证明。"),
    "VULN-062": ("L4", "ibex-csrs unused RLB / napot_mask 宽度截断",
        "napot_mask 部分可仿真！升级路径：L2 micro-tb——构造 NA4/NAPOT region 配置，检查 napot_mask "
        "生成逻辑在截断位宽下的实际掩码值 vs 规范值（预言机：RISC-V PMP 规范 NA4/NAPOT 掩码定义，"
        "脚本内嵌参考表）。RLB unused 做 L3 lint 证明。"),
    "VULN-063": ("L4", "ibex-pmp pmp_mseccfg vs _q 混用 / mask_bits & '0 冗余",
        "可仿真！升级路径：L2 micro-tb——驱动 mseccfg 组合路径（_q vs 组合输入），观察混用导致的"
        "行为差异（如写后立即生效 vs 下周期生效窗口）；mask_bits & '0 部分证明其为冗余 no-op（脚本）。"),
    "VULN-064": ("L4", "keymgr CTRL.FSM.CONSISTENCY 锚点跨模块",
        "结构/声明类。升级路径：L3 脚本证明——解析 hjson SEC_CM CTRL.FSM.CONSISTENCY 声明与 RTL 中"
        "一致性检查逻辑的位置关系（跨模块锚点失效 = 声明无法验证），机器输出 file:line 对照表。"),
    "VULN-067": ("L4", "KMAC sha3pad SVA 注释 + msg_mask 悬空",
        "msg_mask 悬空可升级：L3 elaboration 证明（Verilator lint 或常量追踪脚本证明 msg_mask 信号"
        "无消费点）；SVA 注释部分 grep 锚定。若悬空导致可观测行为（掩码恒定值），进一步 L2 micro-tb。"),
    "VULN-074": ("L4", "otp intg_error[2] 语义错配 / VendorTest ECC 不 fatal / KDI ErrorSt 不锁输出",
        "KDI ErrorSt 不锁输出可仿真！升级路径：L2 micro-tb——ErrorSt 下驱动 KDI 请求，观察输出是否"
        "仍被消费（vuln）/被锁（twin，预言机：ErrorSt 是 terminal 的 hjson 声明）。intg_error 语义"
        "错配做脚本位追踪。"),
    "VULN-076": ("L4", "otp part_buf ecc_err→ErrorSt 不设 fsm_err_o / KDI nonce 索引",
        "fsm_err_o 部分可仿真！升级路径：L2 micro-tb——ecc_err 注入进 part_buf 路径，观察 ErrorSt "
        "进入但 fsm_err_o 不置位（vuln）vs 置位（twin，预言机：兄弟分区/LCI 的 ErrorSt 行为）。"),
    "VULN-079": ("L4", "rom_ctrl checker 侧地址无冗余 / FSM 提取依赖枚举 / PRINCE 参数需脚本比对",
        "PRINCE 参数升级路径：L3 脚本——用 Python 实现 PRINCE 参考模型（树内 prim Prince 多项式表为"
        "预言机），随机向量比对 RTL 参数集。地址冗余/FSM 枚举部分保持 L4 并说明。"),
    "VULN-082": ("L4", "UART rx_fifo_wvalid 门控 / reg_we_check 只读 / TX/RX baud 不一致",
        "rx_fifo_wvalid 与 baud 部分可仿真！升级路径：L2 micro-tb——(a) 驱动 rx 事件，观察 wvalid "
        "门控下的丢失窗口 (b) 计算 TX/RX 两个 NCO 分频路径的等效 baud 差异。reg_we_check 部分做 "
        "L3 脚本（解析寄存器权限表）。"),
}

STAGES = [
    ["VULN-043", "VULN-049", "VULN-054", "VULN-057"],
    ["VULN-062", "VULN-063", "VULN-074", "VULN-076"],
    ["VULN-082", "VULN-079", "VULN-067", "VULN-064"],
    ["VULN-031", "VULN-032", "VULN-042", "VULN-048"],
]


def gen_workorders() -> None:
    for vid, (cur, title, note) in NOTES.items():
        d = W / "plan-dynverify" / "skills-upgrade" / vid
        d.mkdir(parents=True, exist_ok=True)
        (d / "skill.md").write_text(f"""# 证据升级工单: {vid}

## 元数据
- VULN-ID: {vid}
- 标题: {title}
- 当前档位: {cur}（静态/脚本结论）
- 目标: 升级到本 VULN 可达到的最高证据档

## 必读输入
1. 原工单: {W}/plan-dynverify/skills/{vid}/skill.md
2. 原验证结果: {W}/poc/{vid}/RESULT.md（先读，保留其历史结论）
3. 模板与已验证样板: {HARNESS}/templates/REF.md

## 升级分析（预判，可修正但需说明理由）
{note}

## 升级方法论（硬性要求）
1. **先拆分**：把工单的每个子 claim 分成「行为可仿真」/「属性缺失」/「声明缺失」三类。
2. 行为可仿真 → L2 组合 micro-tb（vuln vs twin 差分，exit 1 = 确认）。twin 修复必须有树内预言机
   依据（hjson 措辞/兄弟模块/SVA/规范参考表），禁止凭空造 twin。
3. 属性/声明缺失 → L3 脚本证明：写可复核的 Python 脚本（解析 hjson/grep/常量追踪），运行并留存输出。
4. 确实无法升级的子项 → 诚实保留 L4 并写明原因。**禁止伪造动态证据。**
5. 产出：在 {W}/poc/{vid}/RESULT.md 末尾追加 `## Upgrade (2026-09-23)` 段落——
   新 verdict + 新档位 + 每个子 claim 的升级结果表 + 复现命令。不删除原有内容。
6. 新建文件（tb/twin/build.sh/脚本）放在 {W}/poc/{vid}/upgrade/ 子目录。

## 约束
- Rule 3：禁止访问网络/上游仓库（no_web 已强制）。
- Verilator 4.210 已知坑见 {HARNESS}/knowledge/standards/verilator-4.210-caveats.md。
- 若 30 分钟内无法建立可运行实验，降级为 L3 脚本证明并如实记录。
""", encoding="utf-8")
    print(f"workorders written: {len(NOTES)}")


def gen_flow() -> None:
    lines: list[str] = []
    a = lines.append
    a("# dyn-verify upgrade — 由 scripts/gen_upgrade_flow.py 生成")
    a("# 16 个 GT 外 L3/L4 VULN 证据升级，4 阶段 × 4 并行")
    a("name: dyn-verify-upgrade")
    a("control: false")
    a("env:")
    a(f"  OT_TREE: {OT_TREE}")
    a(f"  VERILATOR: {VERILATOR}")
    a(f"  HARNESS: {HARNESS}")
    a("nodes:")
    prev: list[str] = []
    for stage in STAGES:
        cur = [f"dyn-verifier-{v}" for v in stage]
        needs = ", ".join(prev)
        for name, vid in zip(cur, stage):
            a(f"  {name}:")
            a("    agent: dyn-verifier")
            a(f"    deps: [{needs}]")
            a(
                "    task: "
                + "'"
                + f"证据升级 {vid}（当前 {NOTES[vid][0]}）。升级工单: "
                  f"{W}/plan-dynverify/skills-upgrade/{vid}/skill.md。"
                  "读原工单+原 RESULT.md+升级工单→拆分子 claim→可仿真部分建 micro-tb 差分、"
                  "声明缺失做脚本证明→在 RESULT.md 追加 Upgrade 段落。"
                + "'"
            )
            a("    offline: true")
            a("    retry: 1")
            a("    timeout: 7200")
            a("    seed:")
            a(f"      - {W}/plan-dynverify/skills-upgrade/{vid}/skill.md")
            a(f"      - {W}/poc/{vid}/RESULT.md")
            a(f"      - {HARNESS}/templates/REF.md")
            a(f"      - {HARNESS}/knowledge/standards/verilator-twin-methodology.md")
        prev = cur
    out = W / "plan-dynverify" / "pipeline-upgrade.yaml"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"flow written: {out} ({sum(len(s) for s in STAGES)} nodes)")


if __name__ == "__main__":
    gen_workorders()
    gen_flow()
