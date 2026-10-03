"""claude 后端驱动：per-node settings.json（Stop hook → complete.marker）、
env 前缀转发、TUI 就绪检测、prompt 投递。"""
from __future__ import annotations

import json
import os
import time

from . import schema as C
from . import terminal as tmux
from .pipeline import Job
from .layout import Execution


class LaunchError(Exception):
    pass


class AgentRuntime:
    def __init__(self, run: Execution, node_env: dict[str, dict[str, str]]):
        self.run = run
        self.node_env = node_env

    # ---- 完成标记 ----

    def done(self, node: str) -> bool:
        return self.run.node_done_flag(node).exists()

    def reset_done(self, node: str) -> None:
        self.run.node_done_flag(node).unlink(missing_ok=True)

    # ---- 后端准备 ----

    def prepare(self, node: str, cfg: Job) -> None:
        nd = self.run.node_path(node)
        nd.mkdir(parents=True, exist_ok=True)
        settings: dict = {
            "hooks": {
                "Stop": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": f"touch '{self.run.node_done_flag(node)}'",
                            }
                        ]
                    }
                ]
            }
        }
        if cfg.offline:
            # Rule 3 机器级强制：禁上游检索
            settings["permissions"] = {"deny": ["WebSearch", "WebFetch"]}
        self.run.node_claude_settings(node).write_text(
            json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def launch_command(self, node: str, cfg: Job) -> str:
        env_prefix = self._env_prefix(cfg)
        settings = self.run.node_claude_settings(node)
        return (
            f"{env_prefix} claude --settings '{settings}' "
            f"--dangerously-skip-permissions"
        )

    # ---- env 转发 ----

    def _env_prefix(self, cfg: Job) -> str:
        merged: dict[str, str] = {}
        for var in C.PASSTHROUGH_ENV:
            if var in os.environ:
                merged[var] = os.environ[var]
        merged.update(self.node_env.get(cfg.name, {}))
        merged.update(cfg.env)
        return " ".join(f"{k}='{v}'" for k, v in merged.items())

    # ---- prompt 投递 ----

    def send_prompt(self, node: str, text: str) -> None:
        tmux.wait_window(self.run, node)
        self._wait_tui_ready(node)
        # 人工 attach 时推迟投递（观察优先于调度）
        while tmux.node_locked(self.run, node):
            time.sleep(C.ATTACH_RETRY_SECS)
        tmux.send_text(self.run, node, text)

    def _wait_tui_ready(self, node: str, timeout: float = C.TUI_READY_SECS) -> None:
        """claude TUI 就绪 = 最后 6 条非空行中出现 ❯ 输入提示符。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            pane = tmux.capture_pane(self.run, node, lines=40)
            lines = [ln for ln in pane.splitlines() if ln.strip()]
            if lines and any("❯" in ln for ln in lines[-6:]):
                return
            time.sleep(1.0)
        raise LaunchError(f"节点 {node} 的 TUI 在 {timeout}s 内未就绪")
