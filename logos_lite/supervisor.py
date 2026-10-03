"""常驻总控节点（window 0，不参与完成判定）。"""
from __future__ import annotations

from pathlib import Path

from . import schema as C
from . import terminal as tmux
from .pipeline import Job
from .backend import AgentRuntime
from .layout import Workspace, Execution
from .templates import control_system_prompt

CONTROL_OPENING_PROMPT = (
    "你好，我是本流水线的总控 agent。请先自我介绍并运行 `lt status` "
    "汇报当前流水线状态，然后等待用户指令。"
)

_CLI_HELP = """- `lt status` — 查看各节点状态
- `lt log <node>` — 查看节点终端日志
- `lt seed <node> "<msg>"` — 向运行中节点注入提示
- `lt accept <node>` — 批准 gate 节点
- `lt retry <node>` — 重试节点（重建窗口）
- `lt dismiss <node> --reason "..."` — 跳过节点（下游照常启动）
- `lw stop` — 停止流水线"""


def control_node_config(project: Workspace, run: Execution) -> Job:
    return Job(
        name=C.CTRL_NODE,
        agent=C.CTRL_NODE,
        task="流水线总控（常驻对话）",
    )


def prepare_control_files(
    project: Workspace, run: Execution, cfg, pipeline_yaml_text: str
) -> None:
    control_agent_md = project.find_agent_md(C.CTRL_NODE)
    if control_agent_md is None:
        raise FileNotFoundError(
            f"control: true 需要 {project.agents_dir}/control/agent.md（lt init 会生成）"
        )
    nd = run.node_path(C.CTRL_NODE)
    nd.mkdir(parents=True, exist_ok=True)
    system = control_system_prompt(
        pipeline_name=cfg.name,
        pipeline_yaml_content=pipeline_yaml_text,
        run_root=str(run.root),
        deadline_text=cfg.deadline or "未设置",
        cli_help=_CLI_HELP,
    )
    agent_md_text = control_agent_md.read_text(encoding="utf-8")
    # 项目级 control agent.md + 运行时系统提示（追加）
    (nd / C.ROLE_MD).write_text(
        agent_md_text + "\n\n---\n\n# 运行时系统提示（引擎追加）\n\n" + system,
        encoding="utf-8",
    )
    (nd / C.TASK_FILE).write_text("# 任务：control\n\n常驻总控。\n", encoding="utf-8")
    (nd / C.NOTES_FILE).write_text("# control 私有记忆\n\n", encoding="utf-8")


def launch_control(
    project: Workspace,
    run: Execution,
    cfg,
    driver: AgentRuntime,
    pipeline_yaml_text: str,
) -> None:
    node_cfg = control_node_config(project, run)
    driver.prepare(C.CTRL_NODE, node_cfg)
    prepare_control_files(project, run, cfg, pipeline_yaml_text)
    cmd = driver.launch_command(C.CTRL_NODE, node_cfg)
    if tmux.has_session(run.tmux_session_name):
        tmux.new_window(run, 0, C.CTRL_NODE, cmd, cwd=project.workdir)
    else:
        tmux.new_session(
            run.tmux_session_name,
            run,
            run.window_name(0, C.CTRL_NODE),
            cmd,
            cwd=project.workdir,
        )
    window = run.window_name(0, C.CTRL_NODE)
    log = run.node_tty_log(C.CTRL_NODE)
    log.touch()
    tmux.pipe_pane(run, window, log)
    driver.send_prompt(C.CTRL_NODE, CONTROL_OPENING_PROMPT)
    Path(run.node_done_flag(C.CTRL_NODE)).unlink(missing_ok=True)
