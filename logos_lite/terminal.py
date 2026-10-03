"""全部 tmux 操作 + fcntl attach 锁。"""
from __future__ import annotations

import contextlib
import fcntl
import subprocess
import time
from pathlib import Path

from . import schema as C
from .layout import Execution


class TerminalError(Exception):
    pass


def _run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["tmux", *args], capture_output=True, text=True, timeout=10
    )
    if check and proc.returncode != 0:
        raise TerminalError(f"tmux {' '.join(args)} 失败: {proc.stderr.strip()}")
    return proc


def has_session(name: str) -> bool:
    return _run(["has-session", "-t", name], check=False).returncode == 0


def kill_session(name: str) -> None:
    _run(["kill-session", "-t", name])


def list_hct_sessions() -> list[str]:
    proc = _run(["list-sessions", "-F", "#{session_name}"], check=False)
    if proc.returncode != 0:
        return []
    return [
        ln.strip()
        for ln in proc.stdout.splitlines()
        if ln.strip().startswith(C.TMUX_PREFIX)
    ]


def _window_target(run: Execution, window: str) -> str:
    return f"{run.tmux_session_name}:={window}"


def _resolve_window_name(run: Execution, node: str) -> str:
    proc = _run(["list-windows", "-t", run.tmux_session_name, "-F", "#{window_name}"])
    names = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    for name in names:
        if name == node or name.endswith(f"-{node}"):
            return name
    raise TerminalError(f"窗口不存在: {node} (会话 {run.tmux_session_name})")


def window_exists(run: Execution, node: str) -> bool:
    try:
        _resolve_window_name(run, node)
        return True
    except TerminalError:
        return False


def new_session(
    name: str, run: Execution, window: str, command: str, cwd: Path
) -> None:
    _run(
        [
            "new-session",
            "-d",
            "-s",
            name,
            "-n",
            window,
            "-x",
            "200",
            "-y",
            "50",
            "-c",
            str(cwd),
            command,
        ]
    )


def new_window(run: Execution, index: int, node: str, command: str, cwd: Path) -> None:
    """index 只用于窗口命名（NN- 前缀）；定位一律靠窗口名，
    不做数字索引定位（用户的 tmux 可能配 base-index 1）。"""
    _run(
        [
            "new-window",
            "-t",
            run.tmux_session_name,
            "-n",
            run.window_name(index, node),
            "-c",
            str(cwd),
            command,
        ]
    )


def kill_window(run: Execution, window: str) -> None:
    _run(["kill-window", "-t", _window_target(run, window)])


def pipe_pane(run: Execution, window: str, log_file: Path) -> None:
    _run(
        [
            "pipe-pane",
            "-t",
            _window_target(run, window),
            "-o",
            f"cat >> '{log_file}'",
        ]
    )


def send_text(run: Execution, node: str, text: str) -> None:
    window = _resolve_window_name(run, node)
    target = _window_target(run, window)
    _run(["send-keys", "-t", target, "-l", text])
    _run(["send-keys", "-t", target, "Enter"])
    # 多行文本会被 claude TUI 折叠为 paste 状态，紧跟的 Enter 可能被吞。
    # 检查输入区是否仍停在 "paste again to expand"，是则补发 Enter（空输入的 Enter 是 no-op）。
    for _ in range(3):
        time.sleep(2.0)
        pane = _run(["capture-pane", "-t", target, "-p"]).stdout
        if "paste again to expand" not in pane:
            return
        _run(["send-keys", "-t", target, "Enter"])


def send_keys(run: Execution, node: str, keys: str) -> None:
    window = _resolve_window_name(run, node)
    _run(["send-keys", "-t", _window_target(run, window), keys])


def capture_pane(run: Execution, node: str, lines: int = 30) -> str:
    window = _resolve_window_name(run, node)
    proc = _run(
        ["capture-pane", "-t", _window_target(run, window), "-p", "-S", f"-{lines}"]
    )
    return proc.stdout


def wait_window(run: Execution, node: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if window_exists(run, node):
            time.sleep(2.0)  # 等 TUI 画完
            return
        time.sleep(0.5)
    raise TerminalError(f"等待窗口超时: {node}")


# ---- fcntl attach 锁 ----


def node_locked(run: Execution, node: str) -> bool:
    lock_file = run.node_attach_lock(node)
    if not lock_file.exists():
        return False
    try:
        with open(lock_file, "r") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        return False  # 拿到锁 = 没人持有（陈旧文件）
    except BlockingIOError:
        return True


@contextlib.contextmanager
def hold_node_lock(run: Execution, node: str):
    lock_file = run.node_attach_lock(node)
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_file, "w") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
