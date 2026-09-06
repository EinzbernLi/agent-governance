# Agent Dev Governance

> 面向长期、多模型、多代理开发的轻量治理层。

GitHub 是正式技术事实源；聊天负责交互。OWNER 不搬运完整 Task 或 Result。

## OWNER Quick Start

### 将治理规则接入一个项目（AI-first）

正常接入不要求 OWNER 手工复制模板或逐项配置。给一个有 GitHub/仓库读写能力的 Web、Codex 或其他 coding agent 一句意图即可：

```text
将 <governance repo> 的治理规则接入当前项目。
```

Agent 应先读取治理仓库和目标项目，保留目标项目已有规则，然后只询问无法安全推导的选择。普通接入唯一固定的更新选择是：

```text
是否启用治理规则更新检测？
- 启用（github_native_notify，推荐）
- 不启用（manual_pinned）
```

`github_native_notify` 会把 `templates/GOVERNANCE_UPDATE_CHECK.yml` 安装到目标项目的 `.github/workflows/governance-update-check.yml`，并仅在目标项目自己的 GitHub Issue 中维护 `[GOVERNANCE-UPDATE-SIGNAL]`。它只负责发现治理源版本变化或检查失败，不自动采用新版、不修改 `GOVERNANCE_LOCK`、不自动推进 pin。

`manual_pinned` 不安装主动检查器；项目继续使用当前 exact accepted pin，只有 OWNER 明确要求检查/升级时才访问治理上游。

被治理项目只认一个明确的 `governance source + exact accepted pin`。该上游是否来自官方仓库、Fork 或独立兼容发行版，不是 downstream 的额外模式。项目自己的 `LOCAL_POLICY` 永远留在项目自己仓库。

详细接入与更新契约：

- `docs/project-adoption/PROJECT_ADOPTION.md`
- `docs/project-adoption/GOVERNANCE_CURRENCY_PROTOCOL.md`
- `templates/GOVERNANCE_LOCK.yaml`

### 项目接管 / 继续开发

```text
接管 <project> 的开发，我们继续。
```

这是一条 takeover-only 入口：Lead 恢复/激活并对账 durable state，给出当前状态和建议下一步，然后进入 `AWAIT_OWNER_CONTINUE`。其中的“继续”不授权自动执行恢复出的 Task；必须等 OWNER 下一条明确指令。若同一条消息另含独立、明确、bounded 的工作指令，则不属于 takeover-only，但仍须先通过 continuity、Task、scope、safety 与 permission gates。

收到后续明确执行指令时，Lead 仍先区分 capability availability、work suitability 与 selected route。`web_interactive` 对合规 bounded work 保留 `lead_direct_preferred`；`codex_native_subagents` 在 native capability 已证明、child qualified 且工作适合时采用 `native_delegate_preferred`，通常 native dispatch 以节省 Lead quota 并隔离探索 context。Lead 直接执行 material bypass 必须有 bounded 可审计理由；quota saving alone 不足。

显式切换可说：

```text
把 <project> 项目 Lead 切给 Codex。
由这个 Web 接管 <project> 项目 Lead。
```

### 执行一个 Task，不切 Lead

```text
执行 <task_ref>；作为该 Task 的执行者，不接管项目 Lead。
```

外部 OWNER launch 时，Lead 只需要把模型/思考等级/对话作为展示信息给 OWNER；真正复制给执行端的启动词应保持为一个薄 Task pointer（一个 self-contained copy block，可换行但不得重复 durable package）：

```text
执行 <exact Task ref>；先读取该 Task，并按 Task 内引用读取关联事实；作为该 Task 的执行者执行，不接管项目 Lead。
```

独立 Validator 只替换角色描述，不把完整 SHA、测试、文件白名单和验收条件重复进 launcher；这些都属于 durable Task contract。

Delegated execution 的生命周期是 `ROUTE_RESOLVED -> TASK_PACKAGE_FROZEN -> DISPATCHED -> CHILD_RUNNING -> PARENT_WAITING -> terminal -> RESULT_READ -> LEAD_INTEGRATION -> VALIDATION / ACCEPTANCE`。Child running 时 parent 默认使用 event/blocking/long event wait，不请求 unsolicited progress、不读取 substantive intermediate output；无 event wait 时只可 bounded low-frequency terminal-status check。Worker/Validator nested delegation 默认 false、opt-in only，并且必须保留 parent accountability、bounded purpose、material benefit、ownership 与全部边界。

固定语义：

```text
project takeover / explicit handoff -> Lead continuity
Task execution                    -> Worker / Validator continuity
```

### 同项目并行

同一项目始终只有一个 Active Lead，但可并行多个 `parallel_safe` bounded Tasks：

```text
ONE project Active Lead
├─ Task A -> Worker
├─ Task B -> Worker
└─ Task V -> Validator
```

并行要求 exact frozen baseline、明确 dependencies、实质写入范围不重叠、独立 branch/PR/worktree 或等价隔离面。Worker 不创建 Lead Claim、不集成 sibling work、不做最终 acceptance。

### OWNER 正常只做什么

```text
OWNER gives intent
-> Lead freezes Tasks in GitHub
-> Lead executes/dispatches
-> OWNER only opens genuinely unreachable external runtime when needed
-> executor writes durable Result to GitHub
-> Lead verifies handoff / reviews / integrates / accepts
```

OWNER 不需要复制 Task、Result、SHA 或项目历史。

---

## Canonical Architecture

```text
ONE Active Lead Controller
        ↓
Project state + Model Routing
        ↓
Runtime Capability Probe
        ↓
Task Package
        ↓
Dispatch Policy
   current_session | native_dispatch | external_owner_launch | blocked
        ↓
Worker / Validator Result in GitHub
        ↓
Durable handoff verification
        ↓
Lead Review / Integration / Final Acceptance
```

普通治理只保留这些 authority：

```text
GitHub/project state -> durable facts
Model Governance     -> who is suitable
Task Package         -> what may be done
Dispatch Policy      -> how Lead reaches the assigned executor
Lead Acceptance      -> whether the result is accepted
```

Parallel workstream、Workspace reuse、client host、local planning 都不是额外 authority。

## Governance Conformance

`config/CONFORMANCE_POLICY.yaml` and
`docs/conformance/GOVERNANCE_CONFORMANCE_PROTOCOL.md` define one offline,
read-only evaluator over accepted facts. It supports central-governance and
downstream-project checks plus an optional non-executing Local Action Gate.

```text
explicit exact root + accepted facts
-> governance conformance checker
-> CONFORMANT | RECONCILIATION_REQUIRED | BLOCKED
```

Run it with explicit paths; it never discovers a project root:

```text
python templates/GOVERNANCE_CONFORMANCE_CHECK.py \
  --root <absolute-owner-confirmed-root> \
  --policy <absolute-CONFORMANCE_POLICY.yaml> \
  --input <absolute-conformance-input.yaml>
```

The Result is derived evidence only. `ALLOW` does not authorize or perform a
local action, update availability does not adopt a pin, and no registry,
telemetry, daemon, phone-home or automatic cleanup is introduced. A future
Console may display the Result as an optional read model only.

## Durable Task Completion

Codex/Web/其他 runtime 的 UI 显示“完成”只说明本地执行循环停止，不等于治理意义上的 Task 完成。

```text
runtime/UI completion
!= durable Task completion
!= Lead acceptance
```

Worker handoff 要求：

1. required Result 写入 Task 声明的 canonical result sink；
2. read-back 验证 exact Task ref/revision + required Result；
3. 若 Task 预期 branch/PR/artifact mutation，Result exact ref 与 remote observed ref 一致。

缺少 durable Result/ACK 时使用 `INCOMPLETE_HANDOFF`。OWNER 说“外部 Agent 已完成”只触发 Lead 自动检查 GitHub，不成为完成 authority。

Executor-local planning/scratch 只是 execution aid：

```text
durable Task contract > local planning
```

Local plan 可以为安全保守停止，但不能新增 durable Gate、弱化 acceptance/tests、关闭 Task 或覆盖 GitHub 最新授权。

## Persistent Workspace and Source Reuse

项目长期位置由 OWNER 决定，不由 Codex/Desktop/其他客户端自己的 Project Host 决定。

```text
client Project Host
!= persistent controlled Workspace
!= Task Workspace
!= Runtime Deployment
```

客户端 host 可以保存自身 planning/scratch/conversation artifacts；它不因此成为受控项目目录，也不应成为项目越堆越大的默认部署地。

建立 trusted persistent controlled Source/Workspace 后，普通开发默认复用：

```text
GitHub authoritative source/history
-> OWNER-selected persistent controlled source
-> fetch refs/objects
-> freeze exact Task SHA
-> transient isolated worktree for bounded implementation
-> disposable exact-SHA verifier when required
```

`fresh full clone` 是 clean-room、无可信 persistent source、source identity 损坏/不可验证或 Task 明确要求时的例外，不是每个 Task 的默认动作。Task baseline 不使用 blind `git pull latest`。

## Workspace != Deployment

LPRL 保持以下边界：

```text
Task != Folder
Workspace != Deployment
Deployment Identity != Task Identity
Source Identity != Physical Location
Source Origin != Controlled Workspace Identity
Deployment Definition != Runtime Deployment
```

受保护 Runtime 不为了追 GitHub HEAD 被 reset/clean/fetch-align。适用项目优先使用稳定 Deployment slot，例如：

```text
live
canary
staging
```

Source generation 更新不等于复制一整套 credentials/config/DB/State/logs 到新的 TASK 文件夹。当前 generation + 已证明的 rollback generation 按项目/LPRL policy 保留。

## Optional Local Resource Lifecycle Module

Core Governance is the default repository surface. LPRL is optional and independently pinned; enabling it loads the single module root:

```text
modules/local-resource-lifecycle/
├── docs/
└── templates/
```

The module's canonical version is `modules/local-resource-lifecycle/VERSION`. A downstream project resolves these paths at the exact LPRL module pin it accepted; an ordinary-governance upgrade must not silently repin that module or rewrite an older pin's historical paths.

## Parallel Drift

Exact-head acceptance 保持硬约束：stale candidate 不能作为 current candidate accepted。

但 unrelated sibling merge 不应自动销毁已经验证的本地 payload/evidence。如果 factual/schema/materialization/ignore contract 未变化，可以保留 reusable local evidence，随后只做 lightweight reconcile + exact-head revalidation。

```text
stale candidate != acceptable
stale candidate != automatically invalid local evidence
```

## Local Resource Cleanup

不要把所有删除都送进完整 LPRL Controlled Migration，也不要因为文件“旧、ignored、untracked、Task-named”就直接删除。

普通 bounded housekeeping 只适用于已明确 `task_execution_only`/transient 的 scratch/worktree，或正面证明为可重建的 Cache，并且同时满足：durable handoff/evidence closed、无 unique Source/Data/Evidence、无 protected/shared/runtime binding、无 active writer、local policy 已授权 exact cleanup target。

其他 persistent/shared/State/Data/Deployment/protected/unknown 资源继续进入 LPRL Retirement / Controlled Migration。

Git-tracked superseded governance 文件则在 current-tree consumer/reference 清零后通过普通 PR 删除；**Git history 就是 archive**，不再复制一份 `archive/legacy`。

## Runtime Capability Probe

不要按客户端名称猜能力：

```text
runtime/client name != runtime capability
```

每个新的正式 Lead session 在首次派发前按当前 tool/agent inventory 和 runtime metadata probe；结果默认只缓存本会话。跨 runtime takeover 必须重新 probe。

Canonical dispatch：

- `config/DISPATCH_POLICY.yaml`
- `docs/protocol/DISPATCH_ROUTING_PROTOCOL.md`

## Independence / Nested Delegation

普通 Task 默认：

```yaml
internal_delegation_allowed: false
```

Independent Validator 隔离 substantive evidence，而不是要求平台绝对零 ambient control reads。有效模式：

```text
exact_resource
frozen_bundle
bounded_context
native_isolated_context
```

特殊 exact model/reasoning identity 实验见 `docs/protocol/EXECUTOR_REASONING_COMPLIANCE.md`；它不进入普通工程 hot path。

## Project Adoption / Continuity

项目 `.agent/` 推荐最小状态：

```text
GOVERNANCE_LOCK.yaml
LOCAL_POLICY.yaml
PROJECT_STATE.md
```

GitHub Issue/PR-native 与 file-native Task/Result/Review 二选一，禁止双 authority。

自然语言 takeover 使用现有 continuity：

```text
Takeover / Resume = user entry
Bootstrap         = restore process
Checkpoint        = state continuity
Lead Claim        = control-generation continuity
RESUME_TARGET      = recommended next action, not execution authorization
takeover-only      = reconcile + recommend + AWAIT_OWNER_CONTINUE
```

治理更新发现遵循项目自己的 `GOVERNANCE_LOCK.update_policy`：

```text
github_native_notify -> downstream-local GitHub signal
manual_pinned        -> no proactive upstream check
```

任何 update signal 都不是 adoption authority。

## Hot Path / Cold Path

普通开发通常只加载：

- project `GOVERNANCE_LOCK / LOCAL_POLICY / PROJECT_STATE`；
- 当前 Task；
- `config/MODEL_ROUTING.yaml`（需要选 executor 时）；
- `config/DISPATCH_POLICY.yaml`；
- `docs/protocol/DISPATCH_ROUTING_PROTOCOL.md`；
- `templates/RESULT.md`；
- Lead Acceptance protocol。

按触发加载：Bootstrap/Checkpoint/Lead Claim、governance update signal / release migration material、model qualification/calibration、special identity mode、optional Dispatch Handoff、LPRL。

```text
module exists != module must be loaded
```

## Canonical Invariants

```text
one_active_lead
parallel_workers != parallel_leads
parallel_safe => exact_baseline + declared_dependencies + disjoint_write_scope + isolated_write_surface
write_overlap => serialise_or_replan
probe_before_route
model_routing != dispatch_routing
lead_native_dispatch != worker_nested_delegation
owner_activation_relay != owner_content_relay
GitHub = Task/Result fact source
runtime/UI completion != durable Task completion
durable Task contract > executor-local planning
stale candidate != acceptable current candidate
OWNER chooses persistent Workspace location
persistent source reuse = default
fresh full clone = exception
Task Workspace != Deployment
Deployment identity != Task identity
accepted governance pin = downstream governance authority
update discovery != governance adoption
no automatic governance pin advancement
Lead = integration + final acceptance
```

## Canonical Files

- `config/DISPATCH_POLICY.yaml`
- `config/MODEL_ROUTING.yaml`
- `docs/protocol/AGENT_COORDINATION_PROTOCOL.md`
- `docs/protocol/DISPATCH_ROUTING_PROTOCOL.md`
- `docs/task-package/TASK_PACKAGE_SPEC.md`
- `templates/TASK.md`
- `templates/RESULT.md`
- `docs/acceptance/LEAD_CONTROLLER_ACCEPTANCE_PROTOCOL.md`
- `docs/project-adoption/PROJECT_ADOPTION.md`
- `docs/project-adoption/GOVERNANCE_CURRENCY_PROTOCOL.md`
- `docs/project-adoption/LOCAL_RESOURCE_ONBOARDING.md`
- `docs/context-continuity/SESSION_BOOTSTRAP_PROTOCOL.md`
- `templates/GOVERNANCE_LOCK.yaml`
- `templates/GOVERNANCE_UPDATE_CHECK.yml` when `github_native_notify` is selected
- `modules/local-resource-lifecycle/docs/LPRL_SPEC.md` when local lifecycle governance is enabled

## Privacy

中央治理仓库只保存通用规则、release metadata 和有意匿名化的中央 calibration 结论。具体项目名、机器绝对路径、凭据、业务数据、下游 Task/Issue/Lead/branch/SHA 和项目本地模型反馈留在项目自己的事实边界中。

正确使用公开治理仓库不要求 adopter 注册、项目事实回传、usage telemetry 或 phone-home。外部项目的 local calibration 默认也不会因为采用本治理而上传到中央。
