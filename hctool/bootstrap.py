"""共享 memory 初始化与 prompt 组装。"""
from __future__ import annotations

from pathlib import Path

from . import schema as C
from .pipeline import Job, Campaign
from .layout import Workspace, Execution
from .templates import node_task_prompt, summary_prompt


def _write_if_absent(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def init_shared_memory(run: Execution, cfg: Campaign) -> None:
    overview = "\n".join(f"- {n}: {c.task}" for n, c in cfg.nodes.items())
    _write_if_absent(
        run.mem_context,
        f"""# 流水线上下文（只读参考）

- 流水线：{cfg.name}
- 运行编号：{run.run_id}
- 截止时间：{cfg.deadline or "未设置"}

## 节点概览
{overview}
""",
    )
    _write_if_absent(run.mem_findings, "# 发现日志（仅追加）\n\n在文件末尾追加你的条目，不修改他人条目。条目格式：\n\n## [节点名] YYYY-MM-DD HH:MM\n- 发现/结论\n\n标记约定：[major] 确认 / [minor] 可疑 / [chain] 链索（入口可控性→数据流→sink→前置条件→置信度）\n")
    _write_if_absent(run.mem_decisions, "# 决策记录\n\n记录关键决策与人工干预：时间、决策内容、理由。\n")


def prepare_node_files(
    run: Execution, project: Workspace, node: str, cfg: Job
) -> None:
    """把 agent.md 快照 + task.md + 私有 memory.md 写进节点目录。幂等（resume 安全）。"""
    nd = run.node_path(node)
    nd.mkdir(parents=True, exist_ok=True)
    agent_md = project.find_agent_md(cfg.agent)
    assert agent_md is not None  # load_config 已校验
    _write_if_absent(run.node_agent_md(node), agent_md.read_text(encoding="utf-8"))
    # sidecar 合同文件（lenses.md/FORMAT.md 等）一并快照，
    # 让 agent.md 里"本目录 xxx.md"的引用在节点目录内成立
    for sidecar in agent_md.parent.glob("*.md"):
        if sidecar.name in (C.ROLE_MD, C.LONGTERM_FILE):
            continue
        _write_if_absent(nd / sidecar.name, sidecar.read_text(encoding="utf-8"))
    _write_if_absent(
        run.node_task_file(node), f"# 任务：{node}\n\n{cfg.task}\n"
    )
    longterm = agent_md.parent / C.LONGTERM_FILE
    seed = longterm.read_text(encoding="utf-8") if longterm.is_file() else ""
    _write_if_absent(
        run.node_memory_file(node),
        f"# {node} 私有记忆\n\n{seed}",
    )


def build_task_prompt(
    run: Execution, project: Workspace, node: str, cfg: Job
) -> str:
    inject_lines = "\n".join(
        f"- {_abs(run, p)}" for p in ([C.MEM_CONTEXT, C.MEM_FINDINGS] + cfg.seed)
    )
    return node_task_prompt(
        agent_name=cfg.agent,
        agent_md_path=str(run.node_agent_md(node)),
        task_summary=cfg.task,
        task_file_path=str(run.node_task_file(node)),
        inject_lines=inject_lines,
        workdir=str(project.workdir),
        memory_file_path=str(run.node_memory_file(node)),
        done_flag_path=str(run.node_done_flag(node)),
        findings_path=str(run.mem_findings),
    )


def build_verify_prompt(run: Execution, node: str, cfg: Job) -> str:
    return summary_prompt(
        summary_path=str(run.node_summary_file(node)),
        task_summary=cfg.task,
    )


def _abs(run: Execution, p: str) -> Path:
    path = Path(p)
    if path.is_absolute():
        return path
    # 共享 memory 文件名解析到 memory/ 子目录（与 init_shared_memory 写入位置一致）
    if p in (C.MEM_CONTEXT, C.MEM_FINDINGS, C.MEM_DECISIONS):
        return run.memory_dir / p
    return run.root / path
