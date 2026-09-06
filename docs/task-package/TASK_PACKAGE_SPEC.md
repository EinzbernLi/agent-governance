# Task Package Specification

版本：0.3.18
状态：Accepted

## 1. Authority Boundaries

普通任务只保留四个正式 authority：

```text
Model Governance -> executor suitability
Task Package      -> objective/scope/evidence/tests/acceptance
Dispatch Policy   -> current_session/native/external/blocked
Lead Acceptance   -> final PASS/REWORK/REJECT/BLOCKED
```

GitHub 是 Task / Result / Review 的正式技术事实源。

Parallel workstream 只扩展 Task Package 的执行属性，不增加第五个 authority，也不创建第二 Lead 或并行状态数据库。

### 1.1 Durable re-anchor before authority-bearing work

Runtime-local planning、memory、session restore、IDE state、cached notes、checkpoint 和 scratch 都是 execution aid only：默认非权威、provisional，不能覆盖 GitHub/项目 durable facts，也不能授予 Task scope。新 runtime 可以先恢复/读取它们，但在 applicable durable re-anchor 与 Lead activation 完成前，不得进行 authority-bearing Task execution、dispatch、source/ref/config/data/state mutation 或 network/platform/business action。

Pre-anchor 允许读取 repository/workspace/GitHub durable facts、检查 runtime capabilities，以及运行已知 no-write 或隔离、offline、无 platform effect 且不触碰 source/ref/config/data/state/protected runtime 的 bounded diagnostics。其结果只能作为 provisional evidence，不能在 re-anchor 前当作 current baseline、Task PASS 或 acceptance。

对启用 Lead Claim 的项目，activation completion 必须可观察：读取当前 durable control，写入下一 parent-bound generation，reread canonical sink 并确认唯一性，再完成 fresh Runtime Capability Probe 后才是 `ACTIVE`。若没有可验证的下一 generation，上一有效 generation 保持权威，不得合成缺失 generation。

Re-anchor 后只有 exact input/baseline 与 evidence/test contract 均未变化、且已完成 reconcile/revalidation，才可复用 provisional evidence；否则必须按当前 durable facts rerun。复用 local evidence 不会使 stale candidate 变成 current candidate。

### 1.2 Exact running-Task revision binding

Executor activation binds the running execution contract to the **exact Task
revision** named by the activation pointer. The mutable Issue is transport and
history; it is not a mutable running contract. Publishing or observing a later
Task revision on the same Issue is neither activation nor re-anchor and cannot
silently change the running scope, permissions, evidence, tests, acceptance
criteria, Result contract or execution authority.

An executor may read later durable facts for bounded reconciliation without
adopting their authority. If a later authority-bearing Task revision is relevant
and material to the running contract, the executor remains pinned to the
activated revision, performs only bounded read-only reconciliation, and enters
`NEEDS_ATTENTION_OR_REANCHOR_REQUIRED` before further material work. It must not
guess that publication was intended as activation.

Changing the binding requires explicit, route-appropriate activation or
re-anchor evidence that identifies the prior exact Task ref, the new exact Task
ref and the durable evidence ref. After valid re-anchor, the new exact ref is the
contract; without it, the old exact ref remains the contract. Internal children
remain within the parent's exact activated Task revision and cannot import a
later revision to expand the parent contract.

Lead publication of a later revision does not prove delivery to or adoption by
an already-running external Worker. A Result is interpreted against its recorded
`executed_exact_task_ref`, never a later same-Issue revision merely because that
revision existed when the Result was read. Lead acceptance of that Result as
evidence for another revision requires explicit reconciliation.

## 2. Minimal Task Control Plane

```yaml
baseline_ref: null # parallel_safe 时必须是 exact frozen ref；serial 按任务风险/现有规则决定

executor:
  role: bounded_worker|validator|other_authorized_role
  target_platform: <platform-or-null>
  model: <model-id>
  reasoning: <native-level-or-profile>

model_routing_decision:
  role: <registry-role>
  task_class: <task-class>
  risk_level: low|medium|high|critical
  authority_class: production|shadow|qualification|evidence_acquisition
  selected_model: <model-id>
  selected_reasoning: <native-level-or-profile>
  challenger_disposition: not_applicable|selected|deferred
  challenger_model: null
  challenger_evidence_strength: null
  challenger_defer_reason: null

dispatch:
  mode: auto
  internal_delegation_allowed: runtime_profile_default

nested_delegation:
  default_allowed: false
  opt_in_only: true
  authorization: task_or_lead_explicit
  parent_remains_accountable: true

parallelism:
  mode: serial # serial|parallel_safe
  workstream_id: null
  sibling_task_refs: []

independence:
  required: true|false
  substantive_evidence_isolation: exact_resource|frozen_bundle|bounded_context|native_isolated_context|null
  ambient_control_context_allowed: true

transport:
  task: repository_ref
  result: repository_ref
```

`model_routing_decision` 是由 `config/MODEL_ROUTING.yaml` 已解析结果形成的**派生启动证据**，不是第五个 authority，也不是第二个 routing state。对于标准 Worker / independent Validator 启动，它必须在 Startup Card 发出前存在并通过 fail-closed gate。`challenger_model` / `challenger_evidence_strength` 只在 `selected|deferred` 时使用；`challenger_defer_reason` 只在 `deferred` 时使用，并且必须来自现有 `challenger_exploration.deferral_reasons`。该 block 记录已完成的 routing 结论，不重新计算 candidate 排名、calibration、PEH 或 Execution Economy。

对于标准 Worker / independent Validator，Lead 在把 Task draft 写成 durable `FROZEN` comment 前，必须先用 canonical `templates/STARTUP_CARD_RENDER.py::validate_model_routing_decision` 对已解析的 `executor.model`、`executor.reasoning` 与 `model_routing_decision` 执行同一 fail-closed 校验；未通过则不得发布。这个 pre-freeze reuse 只复用 Model Routing gate，不验证或吸收 Task Package、Dispatch、placement、runtime/client 语义，也不新增 authority。

此外必须有 objective、deliverables、background、scope、non-goals、allowed/forbidden evidence/files、file/resource ownership、required facts/evidence refs、dependencies、acceptance criteria、tests、constraints、blocking conditions、review requirement 和 result contract/result sink。

Delegated Task 的 minimum-complete package 可引用 durable GitHub Task，而不应把无关 conversation、files 或 history 倾倒给 child：

```yaml
package_completeness:
  required_fields: [objective, deliverables, allowed_scope, forbidden_scope, file_or_resource_ownership, required_facts_and_evidence_refs, constraints, dependencies, validation_criteria, blocking_conditions, result_contract]
  durable_source: github_task_or_other_declared_canonical_source
  thin_launcher_may_reference_durable_source: true
  thin_launcher_one_self_contained_copy_block: true
  thin_launcher_may_wrap_lines: true
  startup_card_display_fields: [模型, 思考等级, 对话]
  standard_launcher_semantic_lines: 3
  startup_card_gate_required: true
  formal_launch_routing_decision_required: true
  startup_card_routing_decision_match_required: true
  manual_handwritten_standard_card_emission_allowed: false
  emit_only_after_gate_pass: true
  gate_failure_action: BLOCK
  thin_launcher_must_not_duplicate_durable_package: true
  unrelated_history_dump: forbidden
```

`parallelism` 只声明本 Task 是否允许与 sibling Task 同时执行；真正的写入边界仍由本 Task 已有的 scope / allowed / forbidden files 与 dependencies 定义，不复制第二份 file ownership。

Task/Result transport 默认使用 `repository_ref`。只有正式事实源不可由执行端直接访问时才允许 `manual_content` 作为 degraded fallback；Owner 手动打开外部 Agent 属于 activation，不会把 repository-backed Task/Result 自动降级成手工内容搬运。

## 3. Executor Assignment vs Dispatch

Task 的 `executor` 表示 **谁应执行**。它由 Model Routing / project calibration / Task override 决定。

对于标准 Worker / independent Validator，`model_routing_decision` 必须忠实记录这个已经解析完成的选择：selected model 必须满足 registry/status/role/task/risk 边界；candidate 只能进入 shadow/qualification/evidence-acquisition；under-evidenced challenger 若未选择则必须记录一个现有 policy 接受的 bounded deferral reason。Startup Card gate 只验证这个 resolved decision 与最终 `模型 / 思考等级` 一致，不负责选模型或排序 challenger。

Task 不预先写死 Web/Codex 的启动方式。Route、runtime profile、capability
precedence、delegated lifecycle 与 observation 由唯一 machine owner
`config/DISPATCH_POLICY.yaml` 决定。Task/Result 只引用该决策并记录其要求的
bounded evidence；平台名称本身不授予 capability 或 Lead 身份。

## 4. Parallel Workstream Contract

默认：

```yaml
parallelism:
  mode: serial
  workstream_id: null
  sibling_task_refs: []
```

只有 Active Lead 可以把 `mode` 设为 `parallel_safe`。并行派发前必须验证：

1. `baseline_ref` 是 exact frozen ref；
2. sibling Task 都有自己的正式 Task Package，并有可唯一归属的 Result ref；多个 Task 可共享 append-only Issue 作为 result sink，只要 Task ref 不混淆；
3. dependencies 已声明，且不存在要求当前 Task 等待 sibling 完成的 dependency；
4. 依据各 Task 的 Files / Evidence Allowed / Forbidden，可证明**实质项目写入范围**两两不重叠；
5. 实现类 Task 使用独立 branch/PR、worktree 或等价的隔离写入表面；
6. shared mutable runtime/state/schema migration 写入不存在；
7. executor 不拥有 Lead Claim、sibling integration 或 final acceptance 权限。

允许多个 parallel Task 读取相同源文件、规范或 frozen evidence；允许多个 Task 在同一 GitHub Issue 追加可明确归属的 Result comment。**读取重叠或 append-only Result sink 共享不等于实质项目写入冲突**。

以下情况默认不是 `parallel_safe`：

```text
same project file written by two Tasks
same generated artifact written by two Tasks
same schema/migration mutated by two Tasks
shared mutable runtime/state write
undeclared ordering dependency
baseline not exact/frozen
```

若需要共享项目文件，Lead 应串行化，或把任务重新拆成真正不重叠的写入范围。不得依赖事后 merge conflict 作为并行协调机制。

执行期间若 sibling merge 导致本 Task 的 write scope / dependency assumptions 失效，executor 应停止并记录 deviation；由 Lead 决定 rebase、replan 或 serialise。Worker 不得自行扩大 scope 来追上新基线。

### 4.1 Candidate currency vs reusable local evidence

Exact frozen baseline 仍然是 candidate acceptance 的硬条件：如果 acceptance-relevant integration/head 在 candidate freeze 后发生变化，旧 candidate **不得**作为 current-head 结果直接 accepted。

但 baseline drift 不自动销毁已经证明有效的本地 materialization/payload/evidence。若 Lead 能证明以下语义未变化：

- factual closed set；
- schema/materialization contract；
- ignore/containment semantics；
- 与该 payload 相关的 scope/acceptance assumptions；

则 Result 可以记录 `candidate_currency: stale` 与 `reusable_payload: true`。后续只需把 tracked candidate 轻量 reconcile 到最新允许 baseline，再做 exact-head revalidation；不得仅因 unrelated sibling integration advance 强制重做昂贵的本地 materialization。

```text
stale candidate != acceptable current candidate
stale candidate != automatically invalid local evidence
```

## 5. Runtime Capability Probe Is Not a Task Artifact

Capability Snapshot 默认是当前 Lead session 的临时状态，不写进每个 Task，也不要求创建新的 YAML 文件。

只有以下情况才持久化 ref：

- qualification/benchmark；
- dispatch 故障诊断；
- critical/irreversible workflow 明确要求；
- capability drift 本身影响验收。

这避免把运行时瞬时状态误当成项目长期事实。

## 6. Native vs External

Native/current/external/blocked are delivery routes owned by Dispatch Policy.
They do not change this Task contract. Owner remains an Activation Relay rather
than a Task/Result content relay.

## 7. Nested Delegation

`internal_delegation_allowed` follows Dispatch Policy: Codex Worker defaults to
allowed when native capability is proven; Web/generic Worker defaults false.
Task/Lead may explicitly tighten or override that preference without changing
scope, permissions or formal role boundaries.

若 Lead 已经拆出不同 qualified executor roles 的正式 Task，应分别派发这些 Task，而不是让 Worker 再重新做一遍正式模型路由。

Codex Worker may use zero or more qualified native children for bounded separable
work when quota preservation, specialization, context isolation or elapsed time
is a material benefit. The parent retains integration and terminal Result
accountability. Child writes require ownership; parallel writes are disjoint and
overlaps serialize/fail. Child review is not independent validation and child
recursion remains default false.

`BLOCKED` / `NEEDS_ATTENTION` 仅适用于缺少必要 authority、permission、fact、decision 或 capability 且没有安全的 in-scope alternative；普通搜索、首试失败、命令适配或 bounded debugging 不构成 blocker。

### 7.1 Delegated lifecycle and parent observation

The lifecycle and observation rules are owned by `config/DISPATCH_POLICY.yaml`.
This Task Package supplies the durable Task boundary and references that owner;
it does not mirror the state machine or intervention list.

## 8. Independence

Independent Validator 的核心是 substantive evidence isolation：

```text
exact_resource | frozen_bundle | bounded_context | native_isolated_context
```

Ambient Control Context（system/developer/AGENTS/WORKFLOW/tool/safety controls）可以存在，但不能成为未授权 substantive facts 的输入通道。

## 9. Preflight

默认 `inline_final`。Gate 始终在 substantive work 前存在，但普通 PASS/WARN 不需要单独持久化评论。

`separate_required` 只用于确有独立时间点审计价值的任务。

普通 Preflight 不验证隐藏的内部 child model/reasoning identity。

对于标准 Worker / independent Validator 的正式 launch，preflight 必须先得到有效 `model_routing_decision`；缺失、candidate production、provisional role/task/risk 越界、challenger disposition/defer reason 不合法，或 Startup Card 的 model/reasoning 与 decision 不一致时，launch gate 直接 `BLOCK`。这不新增 durable routing artifact：decision 可以内嵌于 frozen Task，仍由 Model Routing 语义解释。

对于 `parallel_safe` Task，Parallel-Safe Gate 属于普通 preflight 的一部分；正常 PASS 不要求单独生成新 artifact。

Material delegated work 的 preflight 还必须确认 dispatch decision evidence 与 complete-minimal package；terminal handoff 前不得把 child intermediate output 当作 Result。若 accepting parent 的 material substantive mid-flight observation/steering 改变了 Validator evidence boundary，该 Validator run 不得计为 independent validation，必要时必须取得 fresh substantively independent validation。Ambient control context 单独不构成 contamination。

## 10. Handoff

普通 Task **不需要额外 Handoff artifact**。

Handoff 仅用于：

- runtime profile/Task permits internal delegation and extra orchestration instructions are required；
- 特殊 queue/external automation 需要单独 activation envelope；
- model identity benchmark 等特殊模式。

不得把 Handoff 重新变成 Task Package 的重复副本。

## 11. Result

正常 Result 应简洁记录：

```yaml
task_id: ...
status: worker_complete|validator_complete|blocked
execution:
  assigned_executor: <model/role>
  dispatch_route: current_session|native_dispatch|external_owner_launch
  internal_delegation_used: false|true
  dispatch_decision:
    native_dispatch_available: true|false|unknown
    work_suitable_for_native_delegate: true|false|unknown
    selected_route: current_session|native_dispatch|external_owner_launch|blocked
    bypass_reason: <bounded-reason-or-null>
  lifecycle_terminal_state: COMPLETED|BLOCKED|NEEDS_ATTENTION|ABORTED
  observation:
    wait_mode: event_or_blocking_or_long_event|bounded_terminal_status
    unsolicited_progress_requests: 0
    substantive_intermediate_reads: 0
    interventions: []
    result_read_after_terminal: true|false
  validator_independence:
    evidence_boundary_unchanged: true|false
    material_midflight_intervention: true|false
    independent_validation_credit: retained|lost|not_required
parallelism:
  mode: serial|parallel_safe
  workstream_id: ...
  baseline_ref: ...
  conflict_or_dependency_drift: false|true
input_boundary:
  contamination: false|true
commit_or_artifact_ref: ...
tests: ...
```

再记录 Actual Work、Files Changed、Acceptance Criteria、Deviations/Risks、Scope/Safety Compliance。

Capability details、activation evidence、内部 child 链只在异常或特殊审计时展开。

### 11.1 Durable completion barrier

Executor 的本地运行结束、客户端 UI 显示“完成”、本地 planning 标记 done，均不等于 Task durable completion。

Task Package 是 substantive contract authority；executor-local plan 只能帮助执行：

```text
durable Task contract > executor-local planning
local plan may narrow for safety
local plan may not add a durable Gate
local plan may not weaken Task acceptance/tests
```

如果本地执行因额外保守条件停止，Result 必须把它标为 local conservative stop，而不能声称该条件来自 durable Task。若执行前恢复了 local context 或运行了 provisional diagnostic，Result 还应记录 exact input/baseline、evidence/test contract，以及 re-anchor 后的 reuse 或 rerun 决定。

Worker handoff 只有在以下条件满足后才视为 durable-complete：

1. required Result 已写入 Task 声明的 canonical result sink；
2. executor/Lead re-read 能确认 Task ref/revision 与 required Result marker/body；
3. Task 要求 remote mutation 时，Result 中的 exact published ref/head 与实际 remote ref 一致。

缺失时状态是 `INCOMPLETE_HANDOFF`，不是 PASS，也不是因为 UI 已结束就自动变成 BLOCKED/REWORK。即使执行 substantive work 从未开始，BLOCKED/REVISE_REQUIRED 也必须按 Task 要求写 durable Result。

## 12. Hard Rules

- one active Lead Controller per formal project task chain；
- parallel workers are not parallel Leads；
- `parallel_safe` requires exact baseline + declared dependencies + disjoint substantive write scopes + isolated write surfaces；
- write overlap defaults to serial/replan；
- stale candidate may not be accepted as current head；
- reusable local evidence does not grant candidate currency；
- probe before route；
- durable re-anchor + applicable activation before authority-bearing work；
- model routing != dispatch routing；
- standard Worker/Validator Task freeze requires the existing model-routing decision gate to pass; this reuse must not absorb Task/Dispatch/placement/runtime-client semantics；
- standard Worker/Validator launch requires a valid `model_routing_decision` before Startup Card emission；
- candidate production authority and unexplained challenger bypass fail closed at formal launch；
- channel name != runtime capability；
- GitHub-first Task/Result transport；
- repository_ref preferred; manual content is degraded fallback only；
- runtime/UI completion != durable Task completion；
- durable Task contract > executor-local planning；
- Owner does not relay Task/Result bodies；
- Codex Worker child use is default-allowed but optional when proven capable; Web/generic default false；
- independent evidence boundary remains hard；
- only Lead Controller may integrate sibling work and finally accepted。

## 13. Conformance and Formal Launcher Presentation

When a Task can change governance currency, module pins, release acceptance or
local Deployment/State/Data/resource topology, preflight references the current
conformance policy and records the exact evaluated facts/result. The conformance
Result is derived evidence and never expands Task scope or action authority.

A formal launcher is one stable copy-oriented, self-contained thin block that
points to the complete durable Task. An editable drafting surface is not the
formal launcher payload. The durable Task remains authority; neither launcher
nor draft duplicates scope, tests or constraints.

The formal startup card contains exactly `模型 / 思考等级 / 对话`. Role, route,
internal reasoning profile and dispatch explanation are not additional card
fields. The owner-native thinking level is display-only guidance.

A standard launcher uses exactly one fenced `text` block and three semantic
lines. Line breaks do not change semantics:

```text
执行 <exact Task ref>；
先读取该 Task，并按 Task 内引用读取关联事实；
作为该 Task 的执行者执行，不接管项目 Lead。
```

The independent Validator form changes only the final role phrase. A malformed
card, extra/missing text block, durable-package duplication, internal metadata
leak, or one-line standard multi-clause launcher is `REVISE_REQUIRED` before
render. A conformant three-field/one-block/three-line form is `PASS`.

For standard Worker and independent Validator launches, the canonical Startup
Card renderer is a mandatory fail-closed launch gate:

```yaml
startup_card_gate_required: true
formal_launch_routing_decision_required: true
startup_card_routing_decision_match_required: true
manual_handwritten_standard_card_emission_allowed: false
user_visible_response_equals_renderer_stdout: true
surrounding_prose_or_outer_fence_allowed: false
emit_only_after_gate_pass: true
gate_failure_action: BLOCK
```

The exact frozen Task revision, resolved model identity/route, native reasoning
level and compact `model_routing_decision` must be resolved before they become
gate inputs. The canonical renderer validates Task-ref/card structure plus the
already-resolved decision against accepted model registry/routing boundaries. It
**does not** rank candidates, read project calibration/PEH to choose a winner,
select a challenger, choose a model/reasoning level, or override Task/Dispatch
authority. Routing metadata is not printed into the user-facing card, so the
three-field/one-block/three-line payload remains unchanged.

The entire user-visible formal-launch response is the renderer stdout itself:
no leading/trailing prose and no outer Markdown/code fence may wrap it. Any such
post-render decoration is non-conformant and must be rejected before emission.

A byte-identical hand-written card still bypasses the required process and is
non-conformant. The gate blocks card emission on failure, not the underlying Task
authority.
