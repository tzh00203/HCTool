"""pipeline.yaml 解析与 DAG 校验。"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import schema as C
from .layout import ResolveError, Workspace


class PipelineError(Exception):
    pass


@dataclass
class Job:
    name: str
    agent: str
    task: str
    deps: list[str] = field(default_factory=list)
    checkpoint: bool = False
    timeout: float | None = None
    retry: int = 0
    seed: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    offline: bool = False


@dataclass
class Campaign:
    name: str
    nodes: dict[str, Job]
    control: bool = False
    deadline: str | None = None
    env: dict[str, str] = field(default_factory=dict)

    def topological_order(self) -> list[str]:
        """Kahn 算法，确定性稳定排序。"""
        # 计算入度与反向邻接
        in_count: dict[str, int] = {}
        fwd: dict[str, list[str]] = {n: [] for n in self.nodes}
        for name, job in self.nodes.items():
            unique_deps = set(job.deps)
            in_count[name] = len(unique_deps)
            for d in unique_deps:
                fwd[d].append(name)
        # BFS
        ready = [n for n in self.nodes if in_count[n] == 0]
        sorted_names: list[str] = []
        while ready:
            node = ready.pop(0)
            sorted_names.append(node)
            for child in fwd[node]:
                in_count[child] -= 1
                if in_count[child] == 0:
                    ready.append(child)
        if len(sorted_names) != len(self.nodes):
            raise PipelineError("deps 依赖图存在环")
        return sorted_names


def _parse_node(name: str, raw: object, project: Workspace) -> Job:
    prefix = f"节点 `{name}`: "
    if not isinstance(raw, dict):
        raise PipelineError(prefix + "必须是映射")
    agent = raw.get("agent")
    if not isinstance(agent, str) or not agent:
        raise PipelineError(prefix + "缺少 agent 字段")
    if project.find_agent_md(agent) is None:
        raise PipelineError(prefix + f"agent `{agent}` 不存在（agents/{agent}/agent.md）")
    task = raw.get("task")
    if not isinstance(task, str) or not task.strip():
        raise PipelineError(prefix + "缺少 task 字段（非空字符串）")
    needs = raw.get("deps", [])
    if not isinstance(needs, list) or not all(isinstance(x, str) for x in needs):
        raise PipelineError(prefix + "deps 必须是字符串列表")
    timeout = raw.get("timeout")
    if timeout is not None and (not isinstance(timeout, (int, float)) or timeout <= 0):
        raise PipelineError(prefix + "timeout 必须是正数或 null")
    retry = raw.get("retry", 0)
    if not isinstance(retry, int) or retry < 0:
        raise PipelineError(prefix + "retry 必须是非负整数")
    inject = raw.get("seed", [])
    if not isinstance(inject, list) or not all(isinstance(x, str) for x in inject):
        raise PipelineError(prefix + "seed 必须是字符串列表")
    env = raw.get("env", {})
    if not isinstance(env, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in env.items()
    ):
        raise PipelineError(prefix + "env 必须是 str->str 映射")
    no_web = raw.get("offline", False)
    if not isinstance(no_web, bool):
        raise PipelineError(prefix + "offline 必须是布尔值")
    return Job(
        name=name,
        agent=agent,
        task=task,
        deps=list(dict.fromkeys(needs)),
        checkpoint=bool(raw.get("checkpoint", False)),
        timeout=float(timeout) if timeout is not None else None,
        retry=retry,
        seed=inject,
        env=env,
        offline=no_web,
    )


def load_config(pipeline_file: Path) -> Campaign:
    pipeline_file = Path(pipeline_file).resolve()
    if not pipeline_file.is_file():
        raise PipelineError(f"流水线文件不存在: {pipeline_file}")
    try:
        raw = yaml.safe_load(pipeline_file.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise PipelineError(f"YAML 解析失败: {e}") from e
    if not isinstance(raw, dict):
        raise PipelineError("pipeline.yaml 顶层必须是映射")
    name = raw.get("name")
    if not isinstance(name, str) or not name:
        raise PipelineError("缺少 name 字段")
    nodes_raw = raw.get("nodes")
    if not isinstance(nodes_raw, dict) or not nodes_raw:
        raise PipelineError("nodes 必须是非空映射")

    try:
        project = Workspace(root=pipeline_file.parent).find_project_root()
    except ResolveError as e:
        raise PipelineError(str(e)) from e

    if C.CTRL_NODE in nodes_raw:
        raise PipelineError(f"节点名 `{C.CTRL_NODE}` 为保留字")

    nodes: dict[str, Job] = {}
    for node_name, node_raw in nodes_raw.items():
        nodes[node_name] = _parse_node(node_name, node_raw, project)
    for cfg in nodes.values():
        for dep in cfg.deps:
            if dep not in nodes:
                raise PipelineError(f"节点 `{cfg.name}`: deps 引用了不存在的节点 `{dep}`")

    deadline = raw.get("deadline")
    if deadline is not None:
        # PyYAML 会把未加引号的 ISO 时间解析成 datetime —— 规范化成字符串
        if hasattr(deadline, "isoformat"):
            deadline = deadline.isoformat()
        elif not isinstance(deadline, str):
            raise PipelineError("deadline 必须是 ISO 8601 字符串")
    env = raw.get("env", {})
    if not isinstance(env, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in env.items()
    ):
        raise PipelineError("顶层 env 必须是 str->str 映射")
    control = bool(raw.get("control", False))

    cfg = Campaign(
        name=name, nodes=nodes, control=control, deadline=deadline, env=env
    )
    cfg.topological_order()  # 环检测
    return cfg
