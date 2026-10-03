"""所有枚举与文件名常量。不允许其他模块硬编码字面量。"""
from enum import Enum


MANIFEST_FILE = "pipeline.yaml"
ROLES_DIR = "agents"
WORKDIR_LABEL = "workdir"
RUNS_LABEL = "runs"
SHARED_DIR = "memory"
NODE_LABEL = "agents"
OUTPUT_DIR = "artifacts"
SNAPSHOT_FILE = "state.json"
LOCK_FILE = "attach.lock"
SEED_BUS_FILE = "seed-bus.json"
RUN_MANIFEST_FILE = "pipeline.yaml"
CTRL_NODE = "control"

ROLE_MD = "agent.md"
TASK_FILE = "task.md"
POSTMORT_FILE = "summary.md"
NOTES_FILE = "memory.md"
LONGTERM_FILE = "longterm.md"
TTY_LOG = "tty.log"
COMPLETE_FLAG = "complete.marker"
SESSION_ID_FILE = "session.id"
CLAUDE_SETTINGS = "claude-settings.json"

MEM_CONTEXT = "context.md"
MEM_FINDINGS = "findings.md"
MEM_DECISIONS = "decisions.md"

TMUX_PREFIX = "hct-"
TMUX_RC = ".tmux.conf"
TMUX_RC_CONTENT = "\n".join([
    "set -g mouse on",
    "set -g history-limit 100000",
    "set-window-option -g mode-keys vi",
])

TICK_SECS = 2.0
ATTACH_RETRY_SECS = 5.0
TUI_READY_SECS = 90.0

PASSTHROUGH_ENV = [
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "PATH",
    "HOME",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
]


class Backend(str, Enum):
    CLAUDE = "claude"


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    REVIEW = "review"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"

    @classmethod
    def _missing_(cls, value):
        if value == "waiting-human":
            return cls.REVIEW
        raise ValueError(f"'{value}' is not a valid {cls.__name__}")

    @property
    def terminal(self) -> bool:
        return self in (NodeStatus.DONE, NodeStatus.FAILED, NodeStatus.SKIPPED)

    @property
    def satisfied(self) -> bool:
        """下游节点是否可以启动（DONE 或 SKIPPED 都算满足）。"""
        return self in (NodeStatus.DONE, NodeStatus.SKIPPED)
