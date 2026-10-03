#!/usr/bin/env python3
"""生成 dyn-verify backlog 子流水线（VULN-005~082，78 节点）。

按 deferred.md 的批次计划，用 needs 做批次屏障：
stage k 的节点 needs stage k-1 的全部节点 → 每时刻最多 4 个 dyn-verifier 并行。
Batch 1（VULN-001~004）已由 run 20260919-150436 完成，不含在内。
"""
from __future__ import annotations

from pathlib import Path

HARNESS = Path(__file__).resolve().parents[2].parent  # hctool/
CAMPAIGN = HARNESS / "campaigns" / "ches2026-prep"
W = CAMPAIGN / "workdir"

OT_TREE = "/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind"
VERILATOR = (
    "/data_hdd/tzh24/zgc4/projects/tools/logos/logos-workspace/contexts/"
    "targets/opentitan-ches2026/runtime-samples/verilator-4.210/v4.210"
)

# stage -> VULN 序号（对应 deferred.md Batch 2~21）
STAGES: list[list[int]] = [
    [5, 6, 7, 8],
    [9, 10, 11, 12],
    [13, 14, 15, 16],
    [17, 18, 19, 20],
    [21, 22, 23, 24],
    [25, 26, 27, 28],
    [29, 30, 31, 32],
    [33, 34, 35, 36],
    [37, 38, 39, 40],
    [41, 42, 43, 44],
    [45, 46, 47, 48],
    [49, 50, 51, 52],
    [53, 54, 55, 56],
    [57, 58, 59, 60],
    [61, 62, 63, 64],
    [65, 66, 67, 68],
    [69, 70, 71, 72],
    [73, 74, 75, 76],
    [77, 78, 79, 80],
    [81, 82],
]


def gen() -> str:
    lines: list[str] = []
    a = lines.append
    a("# dyn-verify backlog — 由 scripts/gen_backlog_flow.py 生成")
    a("# VULN-005~082（78 节点），needs 批次屏障 → 每阶段 ≤4 并行")
    a("name: dyn-verify-backlog")
    a("control: false")
    a("env:")
    a(f"  OT_TREE: {OT_TREE}")
    a(f"  VERILATOR: {VERILATOR}")
    a(f"  HARNESS: {HARNESS}")
    a("nodes:")
    prev: list[str] = []
    for stage in STAGES:
        cur = [f"dyn-verifier-VULN-{i:03d}" for i in stage]
        needs = ", ".join(prev)
        for name in cur:
            vid = name.removeprefix("dyn-verifier-")
            a(f"  {name}:")
            a("    agent: dyn-verifier")
            a(f"    deps: [{needs}]")
            a(
                "    task: "
                + "'"
                + f"动态验证 {vid}。工单: {W}/plan-dynverify/skills/{vid}/skill.md。"
                  "读工单全文+模板+活样板→生成 twin+tb+build→执行→裁决→写 RESULT.md。"
                + "'"
            )
            a("    offline: true")
            a("    retry: 1")
            a("    timeout: 7200")
            a("    seed:")
            a(f"      - {W}/plan-dynverify/skills/{vid}/skill.md")
            a(f"      - {HARNESS}/templates/REF.md")
            a(f"      - {HARNESS}/knowledge/standards/verilator-twin-methodology.md")
        prev = cur
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    out = W / "plan-dynverify" / "pipeline-backlog.yaml"
    out.write_text(gen(), encoding="utf-8")
    n = sum(len(s) for s in STAGES)
    print(f"written: {out}")
    print(f"nodes: {n} in {len(STAGES)} stages (max 4 parallel)")
