#!/usr/bin/env python3
"""生成 ches2026-prep campaign 的 pipeline.yaml。

12 IP × (oracle-scout + hunter) 并行对 + 下游链
correlator → verify-planner → reviewer → reporter。
改 IP 清单/路径后重跑本脚本即可再生成。
"""
from __future__ import annotations

from pathlib import Path

HARNESS = Path(__file__).resolve().parents[2].parent  # logos-lite/
CAMPAIGN = HARNESS / "campaigns" / "ches2026-prep"

OT_TREE = "/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind"
VERILATOR = (
    "/data_hdd/tzh24/zgc4/projects/tools/logos/logos-workspace/contexts/"
    "targets/opentitan-ches2026/runtime-samples/verilator-4.210/v4.210"
)

# 节点超时（秒）：网关挂起等死锁防护，超时→retry→仍失败暂停等人。
# 依据冒烟实测：scout ~10min，hunter ~25min。
SCOUT_TIMEOUT = 3600
HUNTER_TIMEOUT = 5400
DOWNSTREAM_TIMEOUT = {
    "correlator": 3600,
    "verify-planner": 14400,  # 含同步等待子流水线（dyn-verifier 分批执行）
    "reviewer": 5400,         # 含 PoC 复现重跑
    "reporter": 1800,
}

# ip -> $OT_TREE 下的 RTL 路径（hunter/scout 的主战场）
IPS: dict[str, list[str]] = {
    "aes": ["hw/ip/aes/rtl"],
    "hmac": ["hw/ip/hmac/rtl"],
    "ascon": ["hw/ip/ascon/rtl"],
    "entropy_src": ["hw/ip/entropy_src/rtl"],
    "keymgr": ["hw/ip/keymgr/rtl"],
    "lc_ctrl": ["hw/ip/lc_ctrl/rtl"],
    # 模板 IP：本体在 ip_autogen（top_earlgrey 实例化），hjson/prim 在 hw/ip
    "otp_ctrl": ["hw/ip/otp_ctrl/rtl", "hw/top_earlgrey/ip_autogen/otp_ctrl/rtl"],
    "rom_ctrl": ["hw/ip/rom_ctrl/rtl"],
    "uart": ["hw/ip/uart/rtl"],
    "ibex-pmp": ["hw/vendor/lowrisc_ibex/rtl"],
    "ibex-csrs": ["hw/vendor/lowrisc_ibex/rtl"],
    "kmac": ["hw/ip/kmac/rtl"],
}

# 个别 IP 的聚焦提示（同一 ibex 树两个不同关注面）
FOCUS: dict[str, str] = {
    "ibex-pmp": "重点文件 ibex_pmp.sv（pmpcfg/addr 语义、字节形、锁定语义）",
    "ibex-csrs": "重点文件 ibex_cs_registers.sv（dcsr/dcsr_ebreak、mseccfg、权限检查）",
    "otp_ctrl": "本体在 top_earlgrey/ip_autogen（寄存器拓扑），hjson/SEC_CM 在 hw/ip/otp_ctrl/data",
}


def workdir(*parts: str) -> str:
    return str(CAMPAIGN / "workdir" / Path(*parts))


def yq(text: str) -> str:
    """YAML 单引号标量（task 文本含 `: `，必须引号包裹）。"""
    return "'" + text.replace("'", "''") + "'"


def gen() -> str:
    W = CAMPAIGN / "workdir"
    lines: list[str] = []
    a = lines.append

    a("# ches2026-prep — Hack@CHES 2026 决赛备战流水线（由 scripts/gen_nodes.py 生成）")
    a("# 24 个 IP 节点并行对 → correlator(门) → verify-planner(子流水线) → reviewer(门) → reporter")
    a("name: ches2026-prep")
    a("control: true")
    a("# deadline: 2026-10-01T09:00:00   # 决赛开始时间，按实际填")
    a("env:")
    a(f"  OT_TREE: {OT_TREE}")
    a(f"  VERILATOR: {VERILATOR}")
    a(f"  HARNESS: {HARNESS}")
    a("nodes:")

    hunter_names: list[str] = []
    for ip, rtl_paths in IPS.items():
        scout = f"oracle-scout-{ip}"
        hunter = f"hunter-{ip}"
        hunter_names.append(hunter)
        paths = " + ".join(f"$OT_TREE/{p}" for p in rtl_paths)
        focus = FOCUS.get(ip, "")
        loc = paths + (f"；{focus}" if focus else "")

        a(f"  {scout}:")
        a("    agent: oracle-scout")
        a(
            "    task: "
            + yq(
                f"盘点 IP {ip} 的全部树内预言机（RTL: {loc}）。"
                f"按 FORMAT.md 格式产出 {W}/oracle-inventory/{ip}.md，"
                "每条预言机带 file:line 且可检验。"
            )
        )
        a("    offline: true")
        a("    retry: 1")
        a(f"    timeout: {SCOUT_TIMEOUT}")
        a("    seed:")
        a(f"      - {HARNESS}/knowledge/INDEX.md")
        a(f"      - {HARNESS}/knowledge/tech-stacks/rtl-opentitan/SECURITY_NOTES.md")

        a(f"  {hunter}:")
        a("    agent: hunter")
        a(f"    deps: [{scout}]")
        a(
            "    task: "
            + yq(
                f"对 IP {ip} 执行 6-lens 盲猎（{loc}），"
                f"弹药 {W}/oracle-inventory/{ip}.md（不存在则先自做精简盘点）。"
                f"report-everything，逐条带预言机依据，产出 {W}/findings/{ip}/candidates.md。"
            )
        )
        a("    offline: true")
        a("    retry: 1")
        a(f"    timeout: {HUNTER_TIMEOUT}")
        a("    seed:")
        a(f"      - {W}/oracle-inventory/{ip}.md")
        a(f"      - {HARNESS}/knowledge/INDEX.md")
        a(f"      - {HARNESS}/knowledge/tech-stacks/rtl-opentitan/SECURITY_NOTES.md")

    a("  correlator:")
    a("    agent: correlator")
    a(f"    deps: [{', '.join(hunter_names)}]")
    a(
        "    task: "
        + yq(
            f"汇总全部 hunter 候选（{W}/findings/*/candidates.md + "
            f"runs/<run>/memory/findings.md），去重合并同根因，赋 VULN-ID 并按预估分排序，"
            f"产出 {W}/artifacts/vulns.md（全部 pending-verify，不删任何候选）。"
        )
    )
    a("    seed:")
    a(f"      - {HARNESS}/knowledge/INDEX.md")
    a(f"    timeout: {DOWNSTREAM_TIMEOUT['correlator']}")
    a("    checkpoint: true   # 人工审 vulns.md 后 lt approve correlator")

    a("  verify-planner:")
    a("    agent: verify-planner")
    a("    deps: [correlator]")
    a(
        "    task: "
        + yq(
            f"读 {W}/artifacts/vulns.md，逐 VULN 写验证工单到 "
            f"{W}/plan-dynverify/skills/<VULN-ID>/skill.md，生成并同步执行子流水线 "
            f"{W}/plan-dynverify/pipeline.yaml（dyn-verifier ×N，每批≤4 并行），"
            "执行完把裁决回写 vulns.md 状态字段。"
        )
    )
    a("    seed:")
    a(f"      - {W}/artifacts/vulns.md")
    a(f"      - {HARNESS}/knowledge/standards/verilator-twin-methodology.md")
    a(f"      - {HARNESS}/templates/REF.md")
    a(f"    timeout: {DOWNSTREAM_TIMEOUT['verify-planner']}")

    a("  reviewer:")
    a("    agent: reviewer")
    a("    deps: [verify-planner]")
    a(
        "    task: "
        + yq(
            f"逐条审计已验证 VULN（{W}/artifacts/vulns.md + "
            f"{W}/poc/*/RESULT.md）：Rule 3 合规、PoC 复现重跑、CVSS 校准、查重、"
            f"证据链完整，产出 {W}/artifacts/review.md（PASS/FAIL/RETURN + 提交优先级）。"
        )
    )
    a("    seed:")
    a(f"      - {W}/artifacts/vulns.md")
    a(f"      - {HARNESS}/knowledge/INDEX.md")
    a(f"    timeout: {DOWNSTREAM_TIMEOUT['reviewer']}")
    a("    checkpoint: true   # 人工审 review.md 后 lt approve reviewer")

    a("  reporter:")
    a("    agent: reporter")
    a("    deps: [reviewer]")
    a(
        "    task: "
        + yq(
            f"把 review PASS 条目转成 CHES 19 字段提交包（按 FIELDS.md 映射），"
            f"按预估分排序写入 {W}/submissions/<bug-number>_<slug>.md + INDEX.md。"
        )
    )
    a("    seed:")
    a(f"      - {W}/artifacts/review.md")
    a(f"      - {W}/artifacts/vulns.md")
    a(f"      - {HARNESS}/knowledge/standards/ches-2026-rules.md")
    a(f"    timeout: {DOWNSTREAM_TIMEOUT['reporter']}")

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    out = CAMPAIGN / "pipeline.yaml"
    out.write_text(gen(), encoding="utf-8")
    print(f"written: {out}")
    n_nodes = 2 * len(IPS) + 4
    print(f"nodes: {n_nodes} ({len(IPS)} IP × 2 + 4 下游)")
