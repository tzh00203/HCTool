"""state.json 持久化（原子写）。"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import schema as C


@dataclass
class JobState:
    status: C.NodeStatus = C.NodeStatus.PENDING
    attempts: int = 0
    started_at: float | None = None
    finished_at: float | None = None
    error: str | None = None


@dataclass
class RunTracker:
    pipeline: str
    run_id: str
    paused: bool = False
    nodes: dict[str, JobState] = field(default_factory=dict)

    def node(self, name: str) -> JobState:
        if name not in self.nodes:
            self.nodes[name] = JobState()
        return self.nodes[name]

    def set_status(self, name: str, status: C.NodeStatus) -> None:
        st = self.node(name)
        st.status = status
        if status == C.NodeStatus.RUNNING:
            st.started_at = time.time()
            st.finished_at = None
            st.error = None
            st.attempts += 1
        if status.terminal:
            st.finished_at = time.time()

    def all_terminal(self) -> bool:
        """control 是常驻对话节点，不参与完成判定。"""
        return all(
            st.status.terminal for n, st in self.nodes.items() if n != C.CTRL_NODE
        )

    def save(self, path: Path) -> None:
        data = {
            "pipeline": self.pipeline,
            "run_id": self.run_id,
            "paused": self.paused,
            "nodes": {
                n: {
                    "status": st.status.value,
                    "attempts": st.attempts,
                    "started_at": st.started_at,
                    "finished_at": st.finished_at,
                    "error": st.error,
                }
                for n, st in self.nodes.items()
            },
        }
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    @classmethod
    def load(cls, path: Path) -> "RunTracker":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        state = cls(pipeline=raw["pipeline"], run_id=raw["run_id"])
        state.paused = bool(raw.get("paused", False))
        for n, ns in raw.get("nodes", {}).items():
            status = C.NodeStatus(ns.get("status", C.NodeStatus.PENDING.value))
            st = JobState(status=status)
            st.attempts = int(ns.get("attempts", 0))
            st.started_at = ns.get("started_at")
            st.finished_at = ns.get("finished_at")
            st.error = ns.get("error")
            state.nodes[n] = st
        return state
