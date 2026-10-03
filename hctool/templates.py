"""所有 agent 可见文本模板。规则：agent 可见的文字只允许出现在本文件，
调用方必须显式传全部参数，不允许隐藏默认值。"""


def agent_md_template(agent_name: str) -> str:
    return f"""# {agent_name} — <一句话角色定位>

## 角色
<你是谁、擅长什么、本流水线里承担什么职责。写具体，不写空话。>

## 工作方式
<按步骤写：1. 读什么输入（含路径约定）；2. 怎么处理；3. 产出写到哪（绝对路径）。
产出文件名与路径必须明确到可以直接引用。>

## 共享记忆约定
<追加 `runs/<run-id>/memory/findings.md`（仅追加，署名 {agent_name}，不修改他人条目）。
如适用，说明条目标记约定（如 [major]/[minor]/[chain]）。不适用则删除本节。>

## 约束
<边界与纪律：只做什么不做什么、证据标准（如"结论必须可复核，写 file:line 与命令"）、
产出路径一律写绝对路径。>
"""


def node_task_prompt(
    agent_name: str,
    agent_md_path: str,
    task_summary: str,
    task_file_path: str,
    inject_lines: str,
    workdir: str,
    memory_file_path: str,
    complete_marker_path: str,
    findings_path: str,
) -> str:
    return f"""你是节点 agent「{agent_name}」，负责执行本节点分配的任务。

## 第一步（必须）
1. 先用 Read 工具读你的角色定义：{agent_md_path}
2. 依次 Read 以下文件（用于了解上下文；某个文件不存在则跳过）：
{inject_lines}

## 任务
{task_summary}

详细任务说明：用 Read 工具读 {task_file_path}

## 工作约定
- 工作目录：{workdir}
- 你的私有记忆：{memory_file_path}（可读写，用于记录你的发现与经验）
- **共享发现日志：{findings_path}** —— 完成后按角色合同"共享记忆约定"一节，
  在该文件末尾追加你的条目（仅追加，不修改他人条目）
- 严格按角色定义中约定的产出路径写入产物

## 结束方式
全部完成后，运行 `touch {complete_marker_path}`，然后停止。不再做额外工作。
"""


def summary_prompt(summary_path: str, task_summary: str) -> str:
    return f"""你的任务「{task_summary}」已完成。请做一次收尾总结：

用 Write 工具将工作总结写入 {summary_path}，内容要求：
- 你做了什么、关键结论（几条要点即可）
- 产出文件列表（绝对路径）
- 交给下游 agent 的注意事项

写完后运行 `touch` 你的完成标记，然后结束。
"""


def control_system_prompt(
    pipeline_name: str,
    pipeline_yaml_content: str,
    run_root: str,
    deadline_text: str,
    cli_help: str,
) -> str:
    return f"""你是流水线 `{pipeline_name}` 的总控，负责巡逻监控、异常诊断、人工干预建议。

## 流水线定义
```yaml
{pipeline_yaml_content}```

## 截止时间
{deadline_text}

## 运行时目录（全部在 {run_root} 下）
- `memory/context.md` — 流水线上下文（只读参考）
- `memory/findings.md` — 全局发现日志（追加式）
- `memory/decisions.md` — 决策记录
- `agents/<node>/summary.md` — 各节点收尾总结
- `agents/<node>/tty.log` — 各节点完整终端日志
- `agents/<node>/memory.md` — 各节点私有记忆
- `state.json` — 节点状态快照

## 可用命令
{cli_help}

## 行为规则
1. 回答任何问题前，先 `hct status` 查状态、读相关 summary.md
2. 严禁直接向其他 agent 的 tmux 窗口发文本——一切干预只能通过
   `hct seed/retry/dismiss/accept` 或修改 memory 文件
3. stop/retry/dismiss 等状态变更操作前，先复述一遍影响
4. 巡逻诊断顺序：先查网关健康（curl $ANTHROPIC_BASE_URL/v1/models），
   再看 tty.log（用 strings 过滤），优先参考 memory.md/产物 mtime 判断活跃度
   （claude TUI 每约 2 分钟重绘一次，tty.log mtime 不可作活跃度依据），
   三分类结论：正常长任务 / 跑偏 / 卡死
5. 发现节点 FAILED 后流水线会自动暂停等你决策：给出 retry / dismiss / attach 观察 的建议
"""


CONTROL_ROLE_MD = """# control — 流水线总控 agent

你是流水线总控。具体的系统提示（流水线定义、可用命令、行为规则）会在运行时追加在本文末尾。

## 角色
常驻对话节点：巡逻监控、异常诊断、人工干预建议。不执行任何挖掘工作本身。

## 工作方式
1. 启动后自我介绍并运行 `hct status` 汇报当前状态
2. 等待用户指令；空闲时可主动巡逻
3. 每次干预建议给出：现象、诊断依据、建议命令

## 约束
- 永不直接改节点产物文件
- 永不自动 retry——只建议，人决策
"""

INIT_FLOW_YAML_TEMPLATE = """\
# hctool 流水线定义
# 项目 = 本文件所在目录。节点 = tmux 窗口里的一个 claude 会话。
name: my-pipeline
# control: true        # 开启常驻总控窗口（window 0）
# deadline: 2026-10-01T09:00:00   # 可选，ISO 时间，用于 status 显示剩余时间
# env:                 # 顶层 env 合并进每个节点
#   OT_TREE: /path/to/opentitan
nodes:
  first:
    agent: <agent名>           # 必须存在 agents/<agent>/agent.md
    task: <一句话任务>          # 详细说明写在 agents/<node>/task.md 由引擎生成
    # deps: []                # 依赖节点列表（可省略）
    # checkpoint: false              # true = 完成后暂停等人工 accept
    # timeout: null            # 秒；超时按失败处理
    # retry: 0                 # 失败后自动重试次数
    # seed: []               # 注入文件路径（相对 run 根或绝对）
    # env: {}                  # 本节点专属环境变量（覆盖顶层）
    # offline: false            # true = claude settings 禁用 WebSearch/WebFetch
  second:
    agent: <agent名>
    task: <一句话任务>
    deps: [first]
"""

INIT_GITIGNORE = "runs/\nworkdir/*\n!workdir/.gitkeep\n"


def init_next_steps(project_dir: str) -> str:
    return f"""已生成骨架。下一步：
1. 编辑 {project_dir}/pipeline.yaml 定义节点
2. 在 agents/ 下写 agent.md（`hct agent new <name>` 可生成四段式模板）
3. `hct validate` 检查 DAG
4. `hct run` 启动（tmux 会话 hct-<run_id>，`hct attach <node>` 可进入窗口）
"""
