# Task Package Specification

版本：0.3.14
状态：Draft

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

## 2. Minimal Task Control Plane

```yaml
baseline_ref: null # parallel_safe 时必须是 exact frozen ref；serial 按任务风险/现有规则决定

executor:
  role: bounded_worker|validator|other_authorized_role
  target_platform: <platform-or-null>
  model: <model-id>
  reasoning: <native-level-or-profile>

dispatch:
  mode: auto
  internal_delegation_allowed: false

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

此外必须有 objective、deliverables、background、scope、non-goals、allowed/forbidden evidence/files、file/resource ownership、required facts/evidence refs、dependencies、acceptance criteria、tests、constraints、blocking conditions、review requirement 和 result contract/result sink。

Delegated Task 的 minimum-complete package 可引用 durable GitHub Task，而不应把无关 conversation、files 或 history 倾倒给 child：

```yaml
package_completeness:
  required_fields: [objective, deliverables, allowed_scope, forbidden_scope, file_or_resource_ownership, required_facts_and_evidence_refs, constraints, dependencies, validation_criteria, blocking_conditions, result_contract]
  durable_source: github_task_or_other_declared_canonical_source
  thin_launcher_may_reference_durable_source: true
  thin_launcher_one_self_contained_copy_block: true
  thin_launcher_may_wrap_lines: true
  thin_launcher_must_not_duplicate_durable_package: true
  unrelated_history_dump: forbidden
```

`parallelism` 只声明本 Task 是否允许与 sibling Task 同时执行；真正的写入边界仍由本 Task 已有的 scope / allowed / forbidden files 与 dependencies 定义，不复制第二份 file ownership。

Task/Result transport 默认使用 `repository_ref`。只有正式事实源不可由执行端直接访问时才允许 `manual_content` 作为 degraded fallback；Owner 手动打开外部 Agent 属于 activation，不会把 repository-backed Task/Result 自动降级成手工内容搬运。

## 3. Executor Assignment vs Dispatch

Task 的 `executor` 表示 **谁应执行**。它由 Model Routing / project calibration / Task override 决定。

Task 不预先写死 Web/Codex 的启动方式。Active Lead 在当前会话做 Runtime Capability Probe 后，根据 `config/DISPATCH_POLICY.yaml` 自动解析：

```text
current_session
native_dispatch
external_owner_launch
blocked
```

因此同一 Task 可以在不同 Lead runtime 下选择不同合法 route，而不改变任务内容。

对 material dispatch decision，Task/Result 应分别记录 capability availability、work suitability、selected route 与 bypass reason：

```yaml
dispatch_decision:
  profile: native_delegate_preferred
  native_dispatch_available: true
  work_suitable_for_native_delegate: true
  selected_route: native_dispatch
  bypass_reason: null
```

当 native capability 已证明、work suitable、child qualified 且 profile 为 `native_delegate_preferred` 时，选择 `current_session` 必须有 bounded higher-precedence reason 或可审计 bypass；quota saving alone 无效。

External Web session 可以作为 bounded Worker/Validator；平台名称本身不授予 Lead 身份。

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

### Native

当前 Lead runtime 能直接创建已分配 executor：

```text
Lead -> native child -> 执行 <task_ref>；不要接管项目 Lead。
```

Active Lead 为自己拆分好的正式 Task 创建 child 属于 Lead orchestration。

### External

当前 Lead runtime 不能直接创建已分配 executor，但外部会话可达：

```text
Lead -> GitHub Task
Owner -> open assigned platform/model/reasoning session
Owner -> 执行 <task_ref>；已按启动卡启动；作为该 Task 的执行者，不接管项目 Lead。
Executor -> GitHub Result
Lead -> Review
```

Owner 是 Activation Relay，不是内容中转者。

## 7. Nested Delegation

`internal_delegation_allowed` 默认 false，只约束被分配的 Worker/Validator 会话。

若 Lead 已经拆出不同 qualified executor roles 的正式 Task，应分别派发这些 Task，而不是让 Worker 再重新做一遍正式模型路由。

只有单个 Task 确实需要平台内部临时并行/isolated child/challenger，且存在 material specialization、context isolation 或 elapsed-time benefit 时才显式开启。Opt-in 还必须有 parent accountability、bounded independently understandable subproblem、explicit write/resource ownership、无 unsafe shared-write conflict，并保持 scope、permissions、forbidden boundary、substantive evidence boundary 与 result sink 不扩张。禁止 convenience-only recursion、speculative fan-out、purposeless duplicate execution 和 uncontrolled recursive trees。

`BLOCKED` / `NEEDS_ATTENTION` 仅适用于缺少必要 authority、permission、fact、decision 或 capability 且没有安全的 in-scope alternative；普通搜索、首试失败、命令适配或 bounded debugging 不构成 blocker。

### 7.1 Delegated lifecycle and parent observation

```text
ROUTE_RESOLVED
-> TASK_PACKAGE_FROZEN
-> DISPATCHED
-> CHILD_RUNNING
-> PARENT_WAITING
-> COMPLETED | BLOCKED | NEEDS_ATTENTION | ABORTED
-> RESULT_READ
-> LEAD_INTEGRATION
-> VALIDATION / ACCEPTANCE
```

`CHILD_RUNNING` / `PARENT_WAITING` 期间，parent 默认不请求 unsolicited progress、不重复 substantive polling、不读取中间 patch/result 监控进度、不做 partial integration 或无例外的 mid-flight steering。优先使用 event/blocking/long event wait；无 event wait 时只可 bounded low-frequency terminal-status check，且不得获取 substantive output。只有 Owner status request、timeout、runtime abnormality/error、child blocker、safety/scope/shared-write risk 或 required interrupt/cancel/retask 才允许介入。

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

对于 `parallel_safe` Task，Parallel-Safe Gate 属于普通 preflight 的一部分；正常 PASS 不要求单独生成新 artifact。

Material delegated work 的 preflight 还必须确认 dispatch decision evidence 与 complete-minimal package；terminal handoff 前不得把 child intermediate output 当作 Result。若 accepting parent 的 material substantive mid-flight observation/steering 改变了 Validator evidence boundary，该 Validator run 不得计为 independent validation，必要时必须取得 fresh substantively independent validation。Ambient control context 单独不构成 contamination。

## 10. Handoff

普通 Task **不需要额外 Handoff artifact**。

Handoff 仅用于：

- Task 明确开启 `internal_delegation_allowed: true` 且需要额外 orchestration instructions；
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
- channel name != runtime capability；
- GitHub-first Task/Result transport；
- repository_ref preferred; manual content is degraded fallback only；
- runtime/UI completion != durable Task completion；
- durable Task contract > executor-local planning；
- Owner does not relay Task/Result bodies；
- nested delegation default false；
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
