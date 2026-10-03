"""config/state 单元测试（不触碰 tmux/driver）。"""
import json
from pathlib import Path

import pytest

from hctool.pipeline import PipelineError, load_config
from hctool.schema import NodeStatus
from hctool.tracker import JobState, RunTracker


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "agents" / "alpha").mkdir(parents=True)
    (tmp_path / "agents" / "alpha" / "agent.md").write_text("# alpha\n")
    (tmp_path / "pipeline.yaml").write_text("name: t\nnodes: {}\n")
    return tmp_path


MINIMAL_YAML = """
name: minimal
nodes:
  n1:
    agent: alpha
    task: 做事
  n2:
    agent: alpha
    task: 接着做
    deps: [n1]
"""


class TestLoadConfig:
    def test_minimal(self, project: Path):
        (project / "pipeline.yaml").write_text(MINIMAL_YAML)
        cfg = load_config(project / "pipeline.yaml")
        assert cfg.name == "minimal"
        assert list(cfg.nodes) == ["n1", "n2"]
        assert cfg.nodes["n2"].deps == ["n1"]
        assert cfg.topological_order() == ["n1", "n2"]

    def test_defaults(self, project: Path):
        (project / "pipeline.yaml").write_text(MINIMAL_YAML)
        cfg = load_config(project / "pipeline.yaml")
        n = cfg.nodes["n1"]
        assert n.checkpoint is False
        assert n.timeout is None
        assert n.retry == 0
        assert n.seed == []
        assert n.env == {}
        assert n.offline is False

    def test_unknown_agent(self, project: Path):
        (project / "pipeline.yaml").write_text(
            "name: t\nnodes:\n  n:\n    agent: ghost\n    task: x\n"
        )
        with pytest.raises(PipelineError, match="ghost"):
            load_config(project / "pipeline.yaml")

    def test_unknown_needs_ref(self, project: Path):
        (project / "pipeline.yaml").write_text(
            "name: t\nnodes:\n  n:\n    agent: alpha\n    task: x\n    deps: [missing]\n"
        )
        with pytest.raises(PipelineError, match="missing"):
            load_config(project / "pipeline.yaml")

    def test_cycle(self, project: Path):
        (project / "pipeline.yaml").write_text(
            "name: t\nnodes:\n  a:\n    agent: alpha\n    task: x\n    deps: [b]\n"
            "  b:\n    agent: alpha\n    task: y\n    deps: [a]\n"
        )
        with pytest.raises(PipelineError, match="环"):
            load_config(project / "pipeline.yaml")

    def test_reserved_control_name(self, project: Path):
        (project / "pipeline.yaml").write_text(
            "name: t\nnodes:\n  control:\n    agent: alpha\n    task: x\n"
        )
        with pytest.raises(PipelineError, match="保留字"):
            load_config(project / "pipeline.yaml")

    def test_top_level_env(self, project: Path):
        (project / "pipeline.yaml").write_text(
            "name: t\nenv:\n  OT_TREE: /opt/ot\nnodes:\n"
            "  n1:\n    agent: alpha\n    task: x\n"
        )
        cfg = load_config(project / "pipeline.yaml")
        assert cfg.env == {"OT_TREE": "/opt/ot"}

    def test_top_level_env_must_be_str_map(self, project: Path):
        (project / "pipeline.yaml").write_text(
            "name: t\nenv:\n  OT_TREE: 42\nnodes:\n  n1:\n    agent: alpha\n    task: x\n"
        )
        with pytest.raises(PipelineError, match="env"):
            load_config(project / "pipeline.yaml")

    def test_no_web(self, project: Path):
        (project / "pipeline.yaml").write_text(
            "name: t\nnodes:\n  n1:\n    agent: alpha\n    task: x\n    offline: true\n"
        )
        cfg = load_config(project / "pipeline.yaml")
        assert cfg.nodes["n1"].offline is True

    def test_deadline(self, project: Path):
        (project / "pipeline.yaml").write_text(
            "name: t\ndeadline: 2026-10-01T09:00:00\nnodes:\n"
            "  n1:\n    agent: alpha\n    task: x\n"
        )
        cfg = load_config(project / "pipeline.yaml")
        assert cfg.deadline == "2026-10-01T09:00:00"

    def test_agents_fallback_to_ancestor(self, project: Path, tmp_path: Path):
        """campaign 项目内没有 agents/<name>，向上回溯到全局库。"""
        campaign = project / "campaigns" / "demo"
        campaign.mkdir(parents=True)
        (campaign / "pipeline.yaml").write_text(MINIMAL_YAML)
        cfg = load_config(campaign / "pipeline.yaml")
        assert cfg.nodes["n1"].agent == "alpha"

    def test_diamond_topo_order(self, project: Path):
        (project / "pipeline.yaml").write_text(
            "name: t\nnodes:\n"
            "  a:\n    agent: alpha\n    task: x\n"
            "  b:\n    agent: alpha\n    task: y\n    deps: [a]\n"
            "  c:\n    agent: alpha\n    task: z\n    deps: [a]\n"
            "  d:\n    agent: alpha\n    task: w\n    deps: [b, c]\n"
        )
        cfg = load_config(project / "pipeline.yaml")
        order = cfg.topological_order()
        assert order.index("a") < order.index("b") < order.index("d")
        assert order.index("a") < order.index("c") < order.index("d")


class TestRunTracker:
    def test_roundtrip(self, tmp_path: Path):
        state = RunTracker(pipeline="p", run_id="r1")
        state.set_status("n1", NodeStatus.RUNNING)
        state.set_status("n1", NodeStatus.DONE)
        f = tmp_path / "state.json"
        state.save(f)
        loaded = RunTracker.load(f)
        assert loaded.node("n1").status == NodeStatus.DONE
        assert loaded.node("n1").attempts == 1
        assert loaded.node("n1").finished_at is not None

    def test_running_increments_attempts(self, tmp_path: Path):
        state = RunTracker(pipeline="p", run_id="r1")
        state.set_status("n1", NodeStatus.RUNNING)
        state.set_status("n1", NodeStatus.RUNNING)
        assert state.node("n1").attempts == 2

    def test_skipped_satisfied_failed_not(self):
        assert NodeStatus.SKIPPED.satisfied is True
        assert NodeStatus.DONE.satisfied is True
        assert NodeStatus.FAILED.satisfied is False
        assert NodeStatus.FAILED.terminal is True

    def test_all_terminal_ignores_control(self):
        state = RunTracker(pipeline="p", run_id="r1")
        state.node("control").status = NodeStatus.RUNNING
        state.node("n1").status = NodeStatus.DONE
        assert state.all_terminal() is True

    def test_tolerant_load(self, tmp_path: Path):
        f = tmp_path / "state.json"
        f.write_text(
            json.dumps(
                {"pipeline": "p", "run_id": "r1", "nodes": {"n1": {"status": "running"}}}
            )
        )
        loaded = RunTracker.load(f)
        assert loaded.node("n1").status == NodeStatus.RUNNING
        assert loaded.node("n1").attempts == 0


class TestEnvMerge:
    def test_node_env_merges_over_top_level(self, project: Path):
        """驱动侧合并逻辑：{**cfg.env, **n.env} —— 节点覆盖顶层。"""
        (project / "pipeline.yaml").write_text(
            "name: t\nenv:\n  A: top\n  B: top\nnodes:\n"
            "  n1:\n    agent: alpha\n    task: x\n    env:\n      B: node\n"
        )
        cfg = load_config(project / "pipeline.yaml")
        n = cfg.nodes["n1"]
        merged = {**cfg.env, **n.env}
        assert merged == {"A": "top", "B": "node"}


class TestScaffold:
    def test_prepare_node_files_snapshots_sidecars(self, project: Path):
        """agent.md 旁的 sidecar（如 lenses.md）必须快照进节点目录。"""
        from hctool.bootstrap import prepare_node_files
        from hctool.layout import Workspace, Execution

        (project / "agents" / "alpha" / "lenses.md").write_text("# lenses\n")
        (project / "pipeline.yaml").write_text(MINIMAL_YAML)
        cfg = load_config(project / "pipeline.yaml")
        pp = Workspace(root=project).find_project_root()
        run = Execution(project=pp, run_id="r1")
        run.create()
        prepare_node_files(run, pp, "n1", cfg.nodes["n1"])
        assert (run.node_path("n1") / "agent.md").is_file()
        assert (run.node_path("n1") / "lenses.md").is_file()
        assert (run.node_path("n1") / "lenses.md").read_text(encoding="utf-8") == "# lenses\n"
        # 幂等：再次调用不覆盖
        (run.node_path("n1") / "lenses.md").write_text("改过的\n")
        prepare_node_files(run, pp, "n1", cfg.nodes["n1"])
        assert (
            run.node_path("n1") / "lenses.md"
        ).read_text(encoding="utf-8") == "改过的\n"

    def test_agent_new_template(self, project: Path, monkeypatch, capsys):
        from hctool import commands as cli

        args = type("A", (), {"project": None, "action": "new", "name": "beta"})()
        monkeypatch.chdir(project)
        cli.cmd_agent(args)
        md = project / "agents" / "beta" / "agent.md"
        assert md.is_file()
        assert "## 角色" in md.read_text(encoding="utf-8")

    def test_validate_output(self, project: Path, capsys, monkeypatch):
        from hctool import commands as cli

        (project / "pipeline.yaml").write_text(MINIMAL_YAML)
        args = type(
            "A", (), {"project": None, "file": None}
        )()
        monkeypatch.chdir(project)
        cli.cmd_validate(args)
        out = capsys.readouterr().out
        assert "合法: minimal" in out
        assert "deps=n1" in out
