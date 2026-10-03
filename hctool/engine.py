"""轮询调度核心：2s tick，两段式完成（task→verify），失败暂停等人。"""
from __future__ import annotations

import json
import time

from . import schema as C
from . import terminal as tmux
from .pipeline import Job, Campaign
from .backend import AgentRuntime, LaunchError
from .bootstrap import build_verify_prompt, build_task_prompt, init_shared_memory, prepare_node_files
from .layout import Workspace, Execution
from .tracker import RunTracker


class EngineError(Exception):
    pass


class SeedBus:
    """跨进程持久注入队列（JSON 文件，写即存）。"""

    def __init__(self, path):
        self.path = path
        self._data: dict[str, list[str]] = {}
        if path.exists():
            try:
                self._data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add(self, node: str, message: str) -> None:
        self._data.setdefault(node, []).append(message)
        self.save()

    def merge(self, other: "SeedBus") -> None:
        for node, msgs in other._data.items():
            queued = self._data.setdefault(node, [])
            for m in msgs:
                if m not in queued:
                    queued.append(m)
        self.save()

    def take(self, node: str) -> list[str]:
        msgs = self._data.pop(node, [])
        self.save()
        return msgs

    def pending_nodes(self) -> list[str]:
        return [n for n, msgs in self._data.items() if msgs]


class Engine:
    def __init__(
        self,
        project: Workspace,
        run: Execution,
        cfg: Campaign,
        state: RunTracker,
        driver: AgentRuntime,
        pipeline_file=None,
    ):
        self.project = project
        self.run = run
        self.cfg = cfg
        self.state = state
        self.driver = driver
        self.pipeline_file = pipeline_file
        self.seed_bus = SeedBus(run.seed_bus_file)
        self._verifying: set[str] = set()
        # 窗口编号从 cfg 确定性重建（resume 路径不经过 initialize，
        # 否则待启动节点永远拉不起来）
        base = 1 if cfg.control else 0
        self._window_index: dict[str, int] = {
            name: base + i for i, name in enumerate(cfg.nodes)
        }
        self._stop_requested = False

    # ---- 生命周期 ----

    def initialize(self, pipeline_yaml_text: str) -> None:
        self.run.create()
        self.run.pipeline_snapshot.write_text(pipeline_yaml_text, encoding="utf-8")
        init_shared_memory(self.run, self.cfg)
        # 窗口编号：control 占 0（若开启），流水线节点从 1 起
        base = 1 if self.cfg.control else 0
        session_created = False
        for i, name in enumerate(self.cfg.nodes):
            idx = base + i
            self._window_index[name] = idx
            self.driver.prepare(name, self.cfg.nodes[name])
            prepare_node_files(self.run, self.project, name, self.cfg.nodes[name])
            cmd = self.driver.launch_command(name, self.cfg.nodes[name])
            window = self.run.window_name(idx, name)
            if not session_created:
                tmux.new_session(
                    self.run.tmux_session_name, self.run, window, cmd,
                    cwd=self.project.workdir,
                )
                session_created = True
            else:
                tmux.new_window(self.run, idx, name, cmd, cwd=self.project.workdir)
            tmux.pipe_pane(self.run, window, self.run.node_tty_log(name))
        self.state.save(self.run.state_file)

    def request_stop(self) -> None:
        self._stop_requested = True

    def run_loop(self) -> None:
        while self._continue():
            self._sync_from_disk()
            self._advance()
            if self.state.paused or self.state.all_terminal():
                break
            time.sleep(C.TICK_SECS)
        self.state.save(self.run.state_file)

    def _continue(self) -> bool:
        return not self._stop_requested

    def _sync_from_disk(self) -> None:
        """从磁盘同步最新状态：state.json 可被外部 CLI 修改，seed-bus 也会被写入。"""
        if self.run.state_file.exists():
            loaded = RunTracker.load(self.run.state_file)
            self.state.__dict__.update(loaded.__dict__)
        disk_queue = SeedBus(self.run.seed_bus_file)
        self.seed_bus.merge(disk_queue)

    # ---- 每 tick 四阶段 ----

    def _advance(self) -> None:
        # 1. 刷新 RUNNING 节点
        for name, st in list(self.state.nodes.items()):
            if st.status != C.NodeStatus.RUNNING:
                continue
            cfg = self.cfg.nodes.get(name)
            if cfg is None:
                continue
            if name in self._verifying:
                if self.driver.done(name):
                    self._finish_verify(name)
                continue
            if self.driver.done(name):
                self._start_verify(name, cfg)
                continue
            if self._timed_out(st, cfg):
                self._fail(name, "timeout")
        if self.state.paused:
            return
        # 2. 启动就绪的 PENDING 节点
        for name, cfg in self.cfg.nodes.items():
            st = self.state.node(name)
            if st.status != C.NodeStatus.PENDING:
                continue
            if all(
                self.state.node(d).status.satisfied for d in cfg.deps
            ):
                self._launch(name, cfg)
        # 3. 投递注入队列
        for name in self.seed_bus.pending_nodes():
            if name not in self.state.nodes:
                continue
            if self.state.nodes[name].status != C.NodeStatus.RUNNING:
                continue
            if name in self._verifying:
                continue
            for msg in self.seed_bus.take(name):
                try:
                    self.driver.send_prompt(name, msg)
                except LaunchError:
                    # 投递失败不崩引擎：消息回队，下轮重试
                    self.seed_bus.add(name, msg)
        self.state.save(self.run.state_file)

    @staticmethod
    def _timed_out(st, cfg: Job) -> bool:
        if cfg.timeout is None or st.started_at is None:
            return False
        return time.time() - st.started_at > cfg.timeout

    # ---- 两段式完成 ----

    def _launch(self, name: str, cfg: Job) -> None:
        self.driver.reset_done(name)
        window = self._ensure_window(name)
        if window is None:
            self._fail(name, "tmux 会话不存在，用 hct resume 恢复")
            return
        prompt = build_task_prompt(self.run, self.project, name, cfg)
        try:
            self.driver.send_prompt(name, prompt)
        except LaunchError as e:
            # 投递失败只失败该节点（记 attempt 防无限重启），不崩引擎
            st = self.state.node(name)
            st.attempts += 1
            st.error = f"prompt 投递失败: {e}"
            if st.attempts <= cfg.retry:
                st.status = C.NodeStatus.PENDING
            else:
                st.status = C.NodeStatus.FAILED
                self.state.paused = True
            return
        self.state.set_status(name, C.NodeStatus.RUNNING)

    def _ensure_window(self, name: str) -> str | None:
        """窗口不存在（resume 场景）时重建。"""
        idx = self._window_index.get(name)
        if idx is None:
            return None
        window = self.run.window_name(idx, name)
        if not tmux.has_session(self.run.tmux_session_name):
            return None
        if not tmux.window_exists(self.run, name):
            cfg = self.cfg.nodes[name]
            cmd = self.driver.launch_command(name, cfg)
            tmux.new_window(self.run, idx, name, cmd, cwd=self.project.workdir)
            tmux.pipe_pane(self.run, window, self.run.node_tty_log(name))
        return window

    def _start_verify(self, name: str, cfg: Job) -> None:
        self.driver.reset_done(name)
        try:
            self.driver.send_prompt(name, build_verify_prompt(self.run, name, cfg))
        except LaunchError as e:
            # summary 投递失败 → 节点按失败重试，不崩引擎
            self._fail(name, f"summary 投递失败: {e}")
            return
        self._verifying.add(name)

    def _finish_verify(self, name: str) -> None:
        self._verifying.discard(name)
        cfg = self.cfg.nodes[name]
        if cfg.checkpoint:
            self.state.set_status(name, C.NodeStatus.REVIEW)
        else:
            self.state.set_status(name, C.NodeStatus.DONE)

    # ---- 失败与人工干预 ----

    def _fail(self, name: str, reason: str) -> None:
        cfg = self.cfg.nodes[name]
        st = self.state.node(name)
        if st.attempts <= cfg.retry:
            st.status = C.NodeStatus.PENDING
            st.error = reason
            self._verifying.discard(name)
        else:
            self.state.set_status(name, C.NodeStatus.FAILED)
            st.error = reason
            self.state.paused = True  # 不可恢复的失败 → 暂停等人

    def accept(self, node: str) -> None:
        st = self.state.node(node)
        if st.status != C.NodeStatus.REVIEW:
            raise EngineError(f"节点 {node} 不在等待审核状态（当前 {st.status.value}）")
        self.state.set_status(node, C.NodeStatus.DONE)
        self.state.paused = False
        self.state.save(self.run.state_file)

    def dismiss(self, node: str, reason: str | None = None) -> None:
        st = self.state.node(node)
        if st.status not in (C.NodeStatus.FAILED, C.NodeStatus.REVIEW):
            raise EngineError(f"节点 {node} 不可跳过（当前 {st.status.value}）")
        self._reset_window(node)
        self.state.set_status(node, C.NodeStatus.SKIPPED)
        if reason:
            st.error = reason
        self.state.paused = False
        self.state.save(self.run.state_file)

    def retry(self, node: str) -> None:
        st = self.state.node(node)
        if st.status not in (
            C.NodeStatus.FAILED,
            C.NodeStatus.DONE,
            C.NodeStatus.REVIEW,
            C.NodeStatus.RUNNING,
        ):
            raise EngineError(f"节点 {node} 不可重试（当前 {st.status.value}）")
        self._reset_window(node)
        st.status = C.NodeStatus.PENDING
        st.error = None
        self._verifying.discard(node)
        self.state.paused = False
        self.state.save(self.run.state_file)

    def seed(self, node: str, message: str) -> None:
        if node not in self.state.nodes:
            raise EngineError(f"节点不存在: {node}")
        if self.state.nodes[node].status != C.NodeStatus.RUNNING:
            raise EngineError(
                f"节点 {node} 当前不是 RUNNING（{self.state.nodes[node].status.value}），"
                "只能向运行中的节点注入"
            )
        self.seed_bus.add(node, message)

    def _reset_window(self, node: str) -> None:
        if tmux.has_session(self.run.tmux_session_name) and tmux.window_exists(self.run, node):
            try:
                window = tmux._resolve_window_name(self.run, node)
                tmux.kill_window(self.run, window)
            except tmux.TerminalError:
                pass

    # ---- 展示 ----

    def status_text(self) -> str:
        lines = [f"run {self.run.run_id}（流水线: {self.cfg.name}）"]
        if self.cfg.deadline:
            lines.append(f"deadline: {self.cfg.deadline}")
        if self.state.paused:
            lines.append("** 已暂停 **（FAILED 需决策或 gate 待审批；"
                         "可 `lw attach control` 或 `lw status` 后 accept/retry/dismiss）")
        for name in self.cfg.topological_order():
            st = self.state.node(name)
            cfg = self.cfg.nodes[name]
            flags = ""
            if cfg.checkpoint:
                flags += " [gate]"
            if st.error:
                flags += f" error={st.error}"
            lines.append(
                f"  {name:<24} {st.status.value:<14} needs={','.join(cfg.deps) or '-'}{flags}"
            )
        return "\n".join(lines)
