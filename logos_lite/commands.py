"""lt 命令行入口。"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from . import terminal as tmux
from .schema import NodeStatus
from .pipeline import PipelineError, load_config
from .supervisor import launch_control
from .backend import AgentRuntime
from .engine import Engine, EngineError
from .layout import ResolveError, Workspace, Execution, new_run_id
from .templates import (
    INIT_FLOW_YAML_TEMPLATE,
    INIT_GITIGNORE,
    CONTROL_ROLE_MD,
    agent_md_template,
    init_next_steps,
)
from .tracker import RunTracker


def _project(args) -> Workspace:
    root = Path(getattr(args, "project", None) or Path.cwd()).resolve()
    try:
        return Workspace(root=root).find_project_root()
    except ResolveError as e:
        sys.exit(f"error: {e}")


def _run(args) -> Execution:
    project = _project(args)
    run_id = getattr(args, "run_id", None) or project.latest_run_id()
    if run_id is None:
        sys.exit("error: 没有可用的 run（先 lt run）")
    return Execution(project=project, run_id=run_id)


def _pipeline_file(run: Execution, override: Path | None = None) -> Path:
    if override is not None:
        return Path(override).resolve()
    if run.pipeline_snapshot.is_file():
        return run.pipeline_snapshot
    return run.project.pipeline_file


def _load_run_context(run: Execution, pipeline_override: Path | None = None):
    cfg = load_config(_pipeline_file(run, pipeline_override))
    state = RunTracker.load(run.state_file)
    node_env = {name: {**cfg.env, **n.env} for name, n in cfg.nodes.items()}
    driver = AgentRuntime(run=run, node_env=node_env)
    orch = Engine(
        project=run.project, run=run, cfg=cfg, state=state, driver=driver,
        pipeline_file=_pipeline_file(run, pipeline_override),
    )
    return cfg, state, orch


# ---- 子命令 ----


def cmd_run(args) -> None:
    project = _project(args)
    pipeline_file = (
        Path(args.pipeline).resolve() if args.pipeline else project.pipeline_file
    )
    cfg = load_config(pipeline_file)
    run_id = new_run_id()
    run = Execution(project=project, run_id=run_id)
    state = RunTracker(pipeline=cfg.name, run_id=run_id)
    node_env = {name: {**cfg.env, **n.env} for name, n in cfg.nodes.items()}
    driver = AgentRuntime(run=run, node_env=node_env)
    orch = Engine(
        project=project, run=run, cfg=cfg, state=state, driver=driver,
        pipeline_file=pipeline_file,
    )
    yaml_text = Path(pipeline_file).read_text(encoding="utf-8")
    orch.initialize(yaml_text)
    if cfg.control:
        launch_control(project, run, cfg, driver, yaml_text)
        state.node("control").status = NodeStatus.RUNNING
        state.save(run.state_file)
    print(f"run {run_id} 已启动；tmux 会话: {run.tmux_session_name}")
    print("Ctrl-C 可中断（state 已落盘），之后 lt resume 继续")
    try:
        orch.run_loop()
    except KeyboardInterrupt:
        state.save(run.state_file)
        print(f"\n已中断。恢复: lt resume {run_id}")
        return
    print(orch.status_text())


def cmd_resume(args) -> None:
    run = _run(args)
    cfg, state, orch = _load_run_context(run, getattr(args, "pipeline", None))
    state.paused = False
    state.save(run.state_file)
    print(f"恢复 run {run.run_id}（tmux 会话若不存在会自动重建窗口）")
    try:
        orch.run_loop()
    except KeyboardInterrupt:
        state.save(run.state_file)
        print(f"\n已中断。恢复: lt resume {run.run_id}")
        return
    print(orch.status_text())


def cmd_status(args) -> None:
    run = _run(args)
    _, _, orch = _load_run_context(run, getattr(args, "pipeline", None))
    print(orch.status_text())


def cmd_stop(args) -> None:
    run = _run(args)
    _, state, _ = _load_run_context(run, getattr(args, "pipeline", None))
    if tmux.has_session(run.tmux_session_name):
        tmux.kill_session(run.tmux_session_name)
    state.paused = True
    state.save(run.state_file)
    print(f"run {run.run_id} 已停止（tmux 会话已杀，state=paused）")


def cmd_attach(args) -> None:
    run = _run(args)
    if not tmux.has_session(run.tmux_session_name):
        sys.exit(f"error: tmux 会话 {run.tmux_session_name} 不存在")
    if args.node:
        with tmux.hold_node_lock(run, args.node):
            os.execvp(
                "tmux",
                ["tmux", "attach-session", "-t", run.tmux_session_name],
            )
    else:
        os.execvp("tmux", ["tmux", "attach-session", "-t", run.tmux_session_name])


def cmd_log(args) -> None:
    run = _run(args)
    log = run.node_tty_log(args.node)
    if not log.is_file():
        sys.exit(f"error: 日志不存在: {log}")
    os.execvp("less", ["less", "-R", str(log)])


def cmd_accept(args) -> None:
    run = _run(args)
    _, _, orch = _load_run_context(run, getattr(args, "pipeline", None))
    try:
        orch.accept(args.node)
        print(f"已批准 {args.node}")
    except EngineError as e:
        sys.exit(f"error: {e}")


def cmd_retry(args) -> None:
    run = _run(args)
    _, _, orch = _load_run_context(run, getattr(args, "pipeline", None))
    try:
        orch.retry(args.node)
        print(f"已重试 {args.node}（窗口重建，若流水线暂停会自动继续）")
    except EngineError as e:
        sys.exit(f"error: {e}")


def cmd_dismiss(args) -> None:
    run = _run(args)
    _, _, orch = _load_run_context(run, getattr(args, "pipeline", None))
    reason = " ".join(args.reason) if args.reason else None
    try:
        orch.dismiss(args.node, reason)
        print(f"已跳过 {args.node}" + (f"（原因: {reason}）" if reason else ""))
    except EngineError as e:
        sys.exit(f"error: {e}")


def cmd_seed(args) -> None:
    run = _run(args)
    _, _, orch = _load_run_context(run, getattr(args, "pipeline", None))
    try:
        orch.seed(args.node, args.message)
        print(f"已注入 {args.node}")
    except EngineError as e:
        sys.exit(f"error: {e}")


def cmd_validate(args) -> None:
    project = _project(args)
    chosen = getattr(args, "flag_file", None) or args.file
    file = Path(chosen).resolve() if chosen else project.pipeline_file
    cfg = load_config(file)
    print(f"合法: {cfg.name}（{len(cfg.nodes)} 节点）")
    for name in cfg.topological_order():
        n = cfg.nodes[name]
        extras = []
        if n.checkpoint:
            extras.append("[checkpoint]")
        if n.offline:
            extras.append("[offline]")
        if n.timeout:
            extras.append(f"[timeout={n.timeout}]")
        if n.retry:
            extras.append(f"[retry={n.retry}]")
        print(
            f"  {name:<24} agent={n.agent:<16} deps={','.join(n.deps) or '-'}"
            + (" " + " ".join(extras) if extras else "")
        )
    if cfg.env:
        print(f"  顶层 env: {', '.join(cfg.env.keys())}")
    if cfg.deadline:
        print(f"  deadline: {cfg.deadline}")


def cmd_agent(args) -> None:
    project = _project(args)
    if args.action == "list":
        agents_dir = project.agents_dir
        if not agents_dir.is_dir():
            print("（无 agents/ 目录）")
            return
        for d in sorted(agents_dir.iterdir()):
            md = d / "agent.md"
            if md.is_file():
                first = md.read_text(encoding="utf-8").splitlines()[0]
                print(f"{d.name:<24} {first[:60]}")
    elif args.action == "show":
        md = project.find_agent_md(args.name)
        if md is None:
            sys.exit(f"error: agent 不存在: {args.name}")
        print(md.read_text(encoding="utf-8"))
    elif args.action == "new":
        # 全局库位置：向上找第一个含 agents/ 的祖先
        target = None
        cur = project.root.resolve()
        while True:
            if (cur / "agents").is_dir():
                target = cur / "agents" / args.name
                break
            if cur.parent == cur:
                target = project.agents_dir / args.name
                break
            cur = cur.parent
        target.mkdir(parents=True, exist_ok=True)
        md = target / "agent.md"
        if md.exists():
            sys.exit(f"error: 已存在 {md}")
        md.write_text(agent_md_template(args.name), encoding="utf-8")
        print(f"已生成 {md}")


def cmd_init(args) -> None:
    target = Path(args.dir or Path.cwd()).resolve()
    target.mkdir(parents=True, exist_ok=True)
    pipeline = target / "pipeline.yaml"
    if pipeline.exists():
        sys.exit(f"error: 已存在 {pipeline}")
    pipeline.write_text(INIT_FLOW_YAML_TEMPLATE, encoding="utf-8")
    (target / "agents").mkdir(exist_ok=True)
    (target / "agents" / "control").mkdir(exist_ok=True)
    control_md = target / "agents" / "control" / "agent.md"
    if not control_md.exists():
        control_md.write_text(CONTROL_ROLE_MD, encoding="utf-8")
    workdir = target / "workdir"
    workdir.mkdir(exist_ok=True)
    (workdir / ".gitkeep").touch()
    (target / ".gitignore").write_text(INIT_GITIGNORE, encoding="utf-8")
    print(init_next_steps(str(target)))


def cmd_clean(args) -> None:
    project = _project(args)
    killed = 0
    for sess in tmux.list_lw_sessions():
        run_id = sess[len(tmux.C.TMUX_PREFIX):]
        run = Execution(project=project, run_id=run_id)
        if not run.state_file.exists():
            continue
        state = RunTracker.load(run.state_file)
        if state.all_terminal():
            tmux.kill_session(sess)
            killed += 1
    print(f"清理了 {killed} 个已完成 run 的 tmux 会话")
    if args.runs is not None:
        ids = sorted(
            d.name for d in project.runs_dir.iterdir() if d.is_dir()
        ) if project.runs_dir.is_dir() else []
        stale = ids[:-args.runs] if args.runs > 0 else ids
        if stale:
            answer = input(f"删除 {len(stale)} 个 run 目录 ({', '.join(stale)})? [y/N] ")
            if answer.strip().lower() == "y":
                for rid in stale:
                    import shutil

                    shutil.rmtree(project.runs_dir / rid, ignore_errors=True)
                print(f"已删除 {len(stale)} 个 run 目录")


# ---- 参数解析 ----


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lt", description="ltool — Hack@CHES 多 agent 挖洞 harness"
    )
    parser.add_argument("--version", action="version", version=f"lt {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_project(p):
        p.add_argument("-p", "--project", help="项目目录（默认向上找 pipeline.yaml）")

    p = sub.add_parser("run", help="启动流水线（阻塞直到完成/暂停）")
    add_project(p)
    p.add_argument("-f", "--pipeline", help="流水线 yaml（默认项目 pipeline.yaml）")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("resume", help="恢复已暂停/中断的 run")
    add_project(p)
    p.add_argument("run_id", nargs="?")
    p.add_argument("-f", "--pipeline")
    p.set_defaults(func=cmd_resume)

    p = sub.add_parser("status", help="查看状态")
    add_project(p)
    p.add_argument("run_id", nargs="?")
    p.add_argument("-f", "--pipeline")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("stop", help="停止 run（杀 tmux 会话，state=paused）")
    add_project(p)
    p.add_argument("run_id", nargs="?")
    p.add_argument("-f", "--pipeline")
    p.set_defaults(func=cmd_stop)

    p = sub.add_parser("attach", help="进入 tmux 会话（可指定节点则持锁）")
    add_project(p)
    p.add_argument("node", nargs="?")
    p.add_argument("run_id", nargs="?")
    p.set_defaults(func=cmd_attach)

    p = sub.add_parser("log", help="查看节点终端日志")
    add_project(p)
    p.add_argument("node")
    p.add_argument("run_id", nargs="?")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("accept", help="批准 gate 节点")
    add_project(p)
    p.add_argument("node")
    p.add_argument("run_id", nargs="?")
    p.add_argument("-f", "--pipeline")
    p.set_defaults(func=cmd_accept)

    p = sub.add_parser("retry", help="重试节点")
    add_project(p)
    p.add_argument("node")
    p.add_argument("run_id", nargs="?")
    p.add_argument("-f", "--pipeline")
    p.set_defaults(func=cmd_retry)

    p = sub.add_parser("dismiss", help="跳过节点（下游照常启动）")
    add_project(p)
    p.add_argument("node")
    p.add_argument("run_id", nargs="?")
    p.add_argument("--reason", nargs="*")
    p.add_argument("-f", "--pipeline")
    p.set_defaults(func=cmd_dismiss)

    p = sub.add_parser("seed", help="向运行中节点注入提示")
    add_project(p)
    p.add_argument("node")
    p.add_argument("message")
    p.add_argument("run_id", nargs="?")
    p.add_argument("-f", "--pipeline")
    p.set_defaults(func=cmd_seed)

    p = sub.add_parser("validate", help="校验 pipeline.yaml")
    add_project(p)
    p.add_argument("file", nargs="?")
    p.add_argument("-f", "--pipeline", dest="flag_file")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("agent", help="agent 管理 (list/show/new)")
    add_project(p)
    p.add_argument("action", choices=["list", "show", "new"])
    p.add_argument("name", nargs="?")
    p.set_defaults(func=cmd_agent)

    p = sub.add_parser("init", help="生成项目骨架")
    p.add_argument("dir", nargs="?")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("clean", help="清理已完成 run 的 tmux 会话")
    add_project(p)
    p.add_argument("--runs", type=int, help="仅保留最新 N 个 run 目录")
    p.set_defaults(func=cmd_clean)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (PipelineError, ResolveError) as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
