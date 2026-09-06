# Dispatch Routing Protocol

版本：0.3.16
状态：Non-authoritative reference guide

## 1. Purpose

This is a non-authoritative reference guide for the machine-owned rules in
`config/DISPATCH_POLICY.yaml`. It provides examples and explanation only; it is
not a second dispatch authority. If any prose here differs from the policy, the
policy controls and conformance requires this guide to be reconciled.

Model qualification remains owned by `config/MODEL_ROUTING.yaml`, Task scope by
`docs/task-package/TASK_PACKAGE_SPEC.md`, role coordination by
`AGENT_COORDINATION_PROTOCOL.md`, and final acceptance by the Acceptance
Protocol. The detailed sections below are guidance over those owners.

Current policy first resolves execution surface: local checkout/files/worktree/
software/tests/artifacts default to Codex, while remote-only durable-fact,
reconciliation and review work prefers Web. Explicit role, qualification,
independence, safety, permission, proven capability and Task-specific needs still
win. Placement is preference, never authority.

```text
Task / Safety / Role / Independence define WHAT IS REQUIRED
Model Routing chooses WHO is qualified/suitable
Runtime Capability Probe determines WHAT IS REACHABLE NOW
Execution Economy chooses WHICH COMPLIANT EXECUTION SHAPE TO PREFER
Dispatch Routing chooses HOW TO REACH IT
Lead Acceptance decides WHETHER THE RESULT IS ACCEPTED
```

Execution Economy 只是合规选择之间的偏好层。它不能覆盖 Task 明确分配、安全/权限、模型资格、本地软件能力、独立验证或当前 runtime 的真实 capability。Lead 的核心实现不是 intrinsic duty；只有 route 解析为 `current_session` 或更高优先级的 bounded exception 成立时，Lead 才直接实现。

## 2. One Active Lead

任一正式项目任务链只有一个 active Lead Controller。

- Web/interactive Sol 是 active Lead 时，Lead 可以在当前工具与权限足够的前提下直接完成更多 bounded work。
- Codex/native-subagent-capable Sol 是 active Lead 时，可以把适合的 bounded work 原生派给 qualified child，从而保留 Lead context/quota 给架构、集成、高风险判断和最终验收。
- 多个 Web/Codex session 可以同时作为不同正式 Task 的 Worker/Validator，但它们不是并行 Lead。
- 切换 Lead channel 前先按 Lead continuity 规则接管；不得同时存在两套正式 Task decomposition authority。

Execution Economy 永远不改变以上 authority 关系。

### 2.1 Lead core contract

Lead 的 runtime-independent core 由 `config/DISPATCH_POLICY.yaml` 的
`lead_core_responsibilities` 唯一机器可读地定义。它包含架构、Task
decomposition/freeze、scope/permission/high-risk judgment、Worker/Validator
coordination、sibling integration、exception/re-anchor/replan 与最终 Lead
Acceptance；它也明确 delegation 不转移 Lead authority 或 terminal
accountability。Web/Codex profile 只能引用该 contract 并改变已经合规选择之间
的 direct-vs-delegate preference，不能复制或改写这些职责。

## 3. Runtime Capability Probe

每个新的 Lead 会话在首次派发前自动检查当前会话实际能力，而不是根据 `web`、`codex`、`desktop` 等名称推断。

最小快照：

```yaml
runtime_capabilities:
  native_subagent_dispatch: available|partial|unavailable|unknown
  native_reachable_executors: []
  native_reasoning_selection: available|partial|unavailable|unknown
  native_isolated_context: available|unavailable|unknown
  github_read: available|unavailable|unknown
  github_write: available|unavailable|unknown
  external_owner_activation: available|unavailable|unknown
```

### Evidence priority

优先使用：

1. 当前 runtime 暴露的 tool/agent inventory；
2. 当前 runtime capability metadata；
3. 本会话已成功发生的 native dispatch；
4. 明确标记为 hint 的历史能力记录。

不要为了形式审计每次都创建测试 child。只有 capability 仍为 unknown、没有可靠合规路径、且低成本 probe 能实质改变路由时，才做非破坏性 live probe。

Capability Snapshot 默认是**会话级临时状态**，不是新的长期事实文件；只有强审计或故障诊断需要时才持久化 evidence ref。

## 4. Execution Economy

Execution Economy 在 Model Routing 和 Runtime Capability Probe 已经排除不合规选项后，决定剩余选择中更偏向：

```text
lead_direct_preferred
native_delegate_preferred
balanced
```

### 4.1 Higher-precedence constraints

以下约束全部高于 economy profile：

1. Task 明确的 executor / role / runtime requirement；
2. safety、permission、forbidden boundary；
3. model qualification 与 material suitability；
4. 本地文件系统、软件、artifact 等 Task-required capability；
5. independent validation / distinct formal role / evidence isolation；
6. 当前 Runtime Capability Probe 的事实。

因此 Economy 不允许把“不合规”变成“更省额度所以合规”。

### 4.2 `lead_direct_preferred`

当 active Lead 本身允许作为该 bounded work 的执行 session、工具和权限足够，并且不存在 distinct-role / independence / local-runtime / materially-better-qualified-executor 要求时，优先 `current_session`。

典型 Web/interactive 工作方式：

```text
Web Sol (Lead)
├─ architecture / Task design                 -> current session
├─ GitHub metadata / docs / bounded core edit -> current session when compliant
├─ local-only test requiring unavailable FS   -> dispatch
└─ independent validation                     -> distinct formal Validator
```

不得仅仅为了减少 Lead 工作量或 quota，就要求 Owner 额外打开 external Worker；如果 Lead-direct 已合规，`external_owner_launch` 不能只以“省额度”为理由发生。Task 或 Owner 显式要求不同 executor 的情况除外。

### 4.3 `native_delegate_preferred`

当 Runtime Capability Probe 已证明 native subagent dispatch 可用，并且有 qualified child 满足 Task 时，优先把适合的 bounded work 原生派发出去，例如：

- bounded implementation；
- mechanical repository work；
- tests / replay；
- 满足独立性合同的正式 validator work。

典型 Codex 工作方式：

```text
Codex Sol (Lead)
├─ architecture / decomposition -> Sol
├─ bounded implementation       -> qualified native child
├─ mechanical tests / replay    -> qualified native child
├─ independent Validator Task   -> qualified isolated/native Validator when contract permits
└─ integration / acceptance     -> Sol
```

Lead 继续保留 architecture、Task decomposition、integration、high-risk judgment、exception handling 和 final acceptance。`native_delegate_preferred` 下，适合且可达的 bounded implementation 通常应 native dispatch；Lead 直接执行 material bypass 必须记录 bounded、可审计的 bypass reason。该 profile 的目的之一是节省昂贵 Lead quota 并隔离探索性 context；派生 child 后反复读取 substantive intermediate output 不满足这一隔离目的。

`native_delegate_preferred` **不等于**“Codex 标签证明 native dispatch”。若 probe 显示 unavailable/unknown，则不得虚构 reachability，必须退回下一条合规路径。对于极小 atomic step，如果 orchestration overhead 明显高于执行成本，可以保留 current-session 执行。

### 4.4 `balanced`

不施加强 direct/delegate 偏好，保留原先 capability/suitability-first 的常规行为。

### 4.5 Profile resolution

Profile 可以来自：

1. Task 在允许范围内显式指定的 route preference；
2. 项目 `LOCAL_POLICY.execution_economy.profile`；
3. Owner 或当前 runtime 的显式 policy；
4. runtime-mode hint；
5. fallback `balanced`。

默认 advisory hints：

```text
web_interactive          -> lead_direct_preferred
codex_native_subagents   -> native_delegate_preferred
unknown_or_other         -> balanced
```

这些名称只是 profile hint，**不是 capability proof，也不是 model qualification proof**。如果 hint 与 probe 冲突，以 probe 为准。

## 5. Routing Algorithm

Lead 完成 Task decomposition、Model Routing、Capability Probe 和 Economy resolution 后，对每个正式 Task 独立解析。

通用算法：

```text
1. Apply Task/safety/model/local-runtime/independence constraints.
2. Determine compliant route candidates from actual runtime capabilities.
3. Resolve execution-economy profile.
4. Order only the remaining compliant candidates by that profile.
5. For a material decision, record capability availability, work suitability, selected route and any bounded bypass reason as separate evidence.
6. Dispatch through the first compliant route; otherwise DISPATCH_BLOCKED.
```

Profile 的 route preference：

```text
lead_direct_preferred:
  current_session -> native_dispatch -> external_owner_launch -> blocked

native_delegate_preferred:
  native_dispatch -> current_session -> external_owner_launch -> blocked

balanced:
  current_session -> native_dispatch -> external_owner_launch -> blocked
```

这里的顺序只对**仍然合规且可达**的 route 生效。例如 Task 已明确分配给 distinct Validator 时，Lead `current_session` 根本不是 candidate；本地软件要求超出 Web capability 时，Web `current_session` 也不是 candidate。

### Current session

条件：当前 Lead session 可合法承担该 bounded Task，并满足 scope、role、capability、model、independence 等全部高优先级约束。

### Native dispatch

条件：当前 runtime 已证明能够直接创建/到达 Task 所需的 qualified executor。

Lead native dispatch 属于 **Lead orchestration**，不是 Worker/Validator 的 nested delegation。Native child 只需收到薄启动指针：

```text
执行 <task_ref>；先读取 Issue/指定 comment；作为该 Task 的执行者，不接管项目 Lead。
```

完整 Task 合同仍在 GitHub。

如果需要给执行者会话建议，只能使用短指针：`reuse_existing`、`recommend_new` 或 `must_be_fresh`。只有 Task/evidence contract 明确要求 fresh-session 或 identity isolation 时，`must_be_fresh` 才是硬要求。

### External Owner launch

当 distinct external Agent 确实是合规要求，或更优本地/native route 不可用/被 Task 或 Owner 显式绕过时，才进入 external Owner activation。

Owner 只负责连接或打开指定平台/模型/reasoning，并发送薄启动指针。Owner 不复制 Task 正文、不搬运 Result、不人工解释 Agent 技术上下文。

`lead_direct_preferred` 下，如果 current-session 已合规，不得仅为了 quota-saving 强制 Owner relay。

## 6. Native Reachability Can Be Partial

不要把 native dispatch 简化为 true/false。

例如：

```yaml
native_subagent_dispatch: partial
native_reachable_executors:
  - qualified_worker_A
  - qualified_validator_B
```

同一 Lead 可以对不同 Task 解析出不同 route。Economy profile 只在 probe 证明的 reachability 内排序，不会扩大 native executor 集合。

## 7. Same-Project Parallel Dispatch

Dispatch 可以并发发生，但只有 Task Package 已由 Active Lead 标记为：

```yaml
parallelism:
  mode: parallel_safe
```

并且普通 preflight 已证明：

- exact frozen baseline；
- explicit scope / allowed / forbidden write boundary；
- dependencies 已声明且无 unmet ordering dependency；
- sibling Task 实质项目写入范围两两不重叠；
- 实现类 Task 有独立 branch/PR、worktree 或等价隔离写入表面；
- 不存在 shared mutable state/schema migration 多写者。

Economy profile 可以让 Codex Lead 更愿意原生并发派 bounded siblings，也可以让 Web Lead 自己完成更多串行 bounded work，但它不改变 parallel-safety 条件。

多个 Task 可读取相同 source/evidence，也可在同一 GitHub Issue 追加可明确归属的 Result comment；这不等于实质项目多写者。

不允许：

```text
Project Lead A + Project Lead B
Task A writes x.py + Task B writes x.py concurrently
Worker edits Lead Claim sink
Worker merges sibling Task on its own
```

如果 sibling merge 导致 baseline、dependency 或 write-scope assumption 失效，停止并发集成，返回 Lead 决定 `rebase/replan/serialise`。Merge conflict 不是协调协议。

## 8. Nested Delegation

必须区分：

```text
Lead dispatching assigned Tasks != assigned Worker spawning additional children
```

Codex Worker 在 native capability 已证明时默认可选用 qualified child；Web/
generic Worker 默认 false。Task/Lead 可显式收紧或覆盖。Quota preservation、
specialization、context isolation 和 elapsed time 都可构成 material benefit，
但不能绕过 qualification、safety 或 parent accountability。

Child subproblem 必须 bounded 且 independently understandable；write/resource
ownership 明确，parallel writes 两两 disjoint，overlap serializes/fails；scope、
permissions、forbidden/evidence boundary 与 result sink 不扩张。Child recursion
默认 false，uncontrolled recursive trees 禁止。

Internal child：

- 不继承 Lead authority，不扩大 scope、权限、forbidden boundary 或 result sink；
- 默认不需要独立 durable Task identity；
- child review 不因 child 身份不同而获得 governance-level independent-validation credit；
- 只有收到 distinct durable role/Result contract 时，才提升为正式 Worker/Validator。

Economy profile 不改变这些限制。

### 8.1 Delegated lifecycle and parent observation

所有 delegated execution 使用同一生命周期：

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

`CHILD_RUNNING` / `PARENT_WAITING` 期间，parent 默认不做 substantive progress inspection：不请求 unsolicited summary，不重复 substantive polling，不读取 intermediate patch/result 监控进度，不做 partial integration，也不在无例外时 mid-flight steering。优先使用 terminal event、blocking wait 或 long event wait。

若 runtime 没有 event/blocking wait，只允许 bounded low-frequency terminal-status checks，且不得获取 substantive output。Owner status request、timeout、runtime abnormality/error、child `BLOCKED` / `NEEDS_ATTENTION`、safety/scope/shared-write risk 或 required interrupt/cancel/retask 才允许介入；先读 compact status，只有必要时才做 bounded diagnostic read。

## 9. Independent Validation

独立性约束的是 substantive evidence，不是 Agent 标签。

可用方式：

```text
exact_resource
frozen_bundle
bounded_context
native_isolated_context
```

平台/system/repository 自动加载的纯控制指令属于 Ambient Control Context；未经授权的旧结果、旧分析、额外项目事实等才属于污染。

Executor self-check 是有效执行证据，但不是 independent review。治理级独立验证要求 substantively independent 的正式 Validator identity/session。Worker 自己的 internal child review 也不满足该独立性要求。

`native_delegate_preferred` 可以偏好一个**满足独立验证合同的正式 native Validator**，但不能把 Worker 的自检或 internal child review 重新命名成独立验证。若 accepting parent 对 Validator 做 material substantive mid-flight observation/steering 并改变 evidence boundary，该 run 失去 required independent-validation credit；需要时必须取得 fresh substantively independent validation。Ambient control context 单独不构成 contamination。

## 10. What Does Not Need a Separate Layer

普通任务不需要额外建立：

- parallel Lead store；
- Agent Bus / session database / distributed lock；
- token/accounting database；
- central usage telemetry；
- 每个 child 的 exact-model attestation chain；
- reasoning self-proof；
- Reachability artifact；
- Dispatch Handoff artifact；
- session capability file；
- standalone PASS preflight comment。

Execution Economy 也不是新的 Task/Result/Lead authority store。它可以记录 material profile choice，但普通 Task 不强制持久化 quota/token 数据。

## 11. Re-probe Conditions

以下变化后重新做 capability probe：

- active Lead runtime/channel 改变；
- client/agent mode 改变；
- tool/permission/connection 改变；
- native dispatch capability 改变；
- 新目标 executor 不在当前 probe 覆盖范围。

Profile 变化本身不能制造 capability；如果 profile 切到 `native_delegate_preferred` 而 native capability 未知，仍必须按 probe 规则解析。

## 12. Minimal Evidence

正常任务最终只需要能够回答：

```text
Task ref 是什么？
分配给谁？
走 current/native/external 哪条 route？
若 economy profile 对 route 选择具有实质影响，使用了哪个 profile？
若 parallel_safe，workstream/baseline 是什么，是否发生 conflict/drift？
Result 在哪里？
是否满足 scope / tests / acceptance criteria？
Lead 是否 accepted？
```

只有异常路径才展开 capability、activation 或内部 delegation 细节。普通任务不要求记录 token 数或精确成本。

## 13. Invariants

```text
one_active_lead
parallel_workers != parallel_leads
parallel_safe => exact_baseline + declared_dependencies + disjoint_write_scope + isolated_write_surface
write_overlap => serialise_or_replan
probe_before_route
channel_name != runtime_capability
channel_name != model_qualification
model_routing != execution_economy != dispatch_routing
execution_economy_only_orders_compliant_choices
capability_probe > runtime_hint
Task/safety/model/local-runtime/independence > economy_profile
lead_direct_preferred => no_owner_relay_for_quota_only_when_direct_compliant
native_delegate_preferred => native_only_when_proven_reachable_and_qualified
lead_native_dispatch != worker_nested_delegation
owner_activation_relay != owner_content_relay
one_formal_task_one_assigned_session_by_default
role_stable_session_reuse_default
fresh_session_only_when_task_requires
bounded_worker_internal_delegation_below_governance
self_check != independent_validation
GitHub = Task/Result fact source
Lead = architecture + integration + final acceptance (core implementation is route-dependent)
```
