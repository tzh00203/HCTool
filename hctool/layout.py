"""目录约定与项目/run 路径解析。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import schema as C


class ResolveError(Exception):
    pass


def new_run_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


@dataclass(frozen=True)
class Workspace:
    root: Path

    @property
    def pipeline_file(self) -> Path:
        return self.root / C.MANIFEST_FILE

    @property
    def agents_dir(self) -> Path:
        return self.root / C.ROLES_DIR

    @property
    def workdir(self) -> Path:
        return self.root / C.WORKDIR_LABEL

    @property
    def runs_dir(self) -> Path:
        return self.root / C.RUNS_LABEL

    def find_project_root(self) -> "Workspace":
        """从 root 向上找含 pipeline.yaml 的目录；跳过路径中带 runs/ 分量的候选
        （子流水线 yaml 在 runs/ 下，不能当项目根）。"""
        cur = self.root.resolve()
        while True:
            if "runs" in cur.parts:
                cur = cur.parent
                continue
            if (cur / C.MANIFEST_FILE).is_file():
                return Workspace(root=cur)
            if cur.parent == cur:
                raise ResolveError(
                    f"未找到项目根（{PIPELINE_DESC}）：从 {self.root} 向上未发现 pipeline.yaml"
                )
            cur = cur.parent

    def find_agent_md(self, agent: str) -> Path | None:
        """先项目内 agents/，再向上祖先目录找共享全局 agent 库。"""
        cur = self.root.resolve()
        while True:
            if (cur / C.ROLES_DIR / agent / C.ROLE_MD).is_file():
                return cur / C.ROLES_DIR / agent / C.ROLE_MD
            if cur.parent == cur:
                return None
            cur = cur.parent

    def latest_run_id(self) -> str | None:
        if not self.runs_dir.is_dir():
            return None
        ids = sorted(d.name for d in self.runs_dir.iterdir() if d.is_dir())
        return ids[-1] if ids else None


PIPELINE_DESC = "项目 = 含 pipeline.yaml 的目录"


@dataclass(frozen=True)
class Execution:
    project: Workspace
    run_id: str

    @property
    def root(self) -> Path:
        return self.project.runs_dir / self.run_id

    @property
    def memory_dir(self) -> Path:
        return self.root / C.SHARED_DIR

    @property
    def mem_context(self) -> Path:
        return self.memory_dir / C.MEM_CONTEXT

    @property
    def mem_findings(self) -> Path:
        return self.memory_dir / C.MEM_FINDINGS

    @property
    def mem_decisions(self) -> Path:
        return self.memory_dir / C.MEM_DECISIONS

    @property
    def node_dir(self) -> Path:
        return self.root / C.NODE_LABEL

    @property
    def artifacts_dir(self) -> Path:
        return self.root / C.OUTPUT_DIR

    @property
    def state_file(self) -> Path:
        return self.root / C.SNAPSHOT_FILE

    @property
    def pipeline_snapshot(self) -> Path:
        return self.root / C.RUN_MANIFEST_FILE

    @property
    def attach_lock(self) -> Path:
        return self.root / C.LOCK_FILE

    @property
    def seed_bus_file(self) -> Path:
        return self.root / C.SEED_BUS_FILE

    @property
    def tmux_session_name(self) -> str:
        return f"{C.TMUX_PREFIX}{self.run_id}"

    def node_path(self, node: str) -> Path:
        return self.node_dir / node

    def node_agent_md(self, node: str) -> Path:
        return self.node_path(node) / C.ROLE_MD

    def node_task_file(self, node: str) -> Path:
        return self.node_path(node) / C.TASK_FILE

    def node_memory_file(self, node: str) -> Path:
        return self.node_path(node) / C.NOTES_FILE

    def node_summary_file(self, node: str) -> Path:
        return self.node_path(node) / C.POSTMORT_FILE

    def node_tty_log(self, node: str) -> Path:
        return self.node_path(node) / C.TTY_LOG

    def node_done_flag(self, node: str) -> Path:
        return self.node_path(node) / C.COMPLETE_FLAG

    def node_attach_lock(self, node: str) -> Path:
        return self.node_path(node) / f"{C.LOCK_FILE}.{node}.lock"

    def node_claude_settings(self, node: str) -> Path:
        return self.node_path(node) / C.CLAUDE_SETTINGS

    def window_name(self, index: int, node: str) -> str:
        return f"{index:02d}-{node}"

    def create(self) -> None:
        for d in (self.root, self.memory_dir, self.node_dir, self.artifacts_dir):
            d.mkdir(parents=True, exist_ok=True)
