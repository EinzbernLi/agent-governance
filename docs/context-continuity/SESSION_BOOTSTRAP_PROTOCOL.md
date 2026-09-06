# Session Bootstrap Protocol

版本：0.3.4  
状态：Draft

## 1. Goal

新的正式 Lead 会话应能从项目 durable facts 恢复最小充分上下文，并在任何 authority-bearing Task 执行、派发或项目修改前完成 durable re-anchor、Lead activation 与 fresh Runtime Capability Probe。对 takeover-only 消息，还必须在 reconciliation 后进入 `AWAIT_OWNER_CONTINUE`，等待 Owner 后续明确指令。Runtime-local planning、memory、session restore、IDE state、cached notes、checkpoint 和 scratch 都只是 execution aid：默认非权威、在 re-anchor 前只能作为 provisional context。不要根据 Web/Codex/Desktop 名称猜 dispatch、本地文件系统或其他执行能力。

本协议支持自然语言接管/恢复，例如：

```text
“接管 <project> 的开发，我们继续进行”
“切到 <project>，接着上次继续”
“这边接手 <project>”
```

当项目能够唯一解析时，Owner 不需要提供 checkpoint ID、Task ID、开发基线或重复粘贴治理规则。

## 2. Four-Layer Continuity Model

```text
Natural-language Takeover / Resume
        ↓
Bootstrap / Recovery
        ↓
Lead Activation + control-scope recovery
        ↓
Checkpoint / Task / latest durable facts reconciliation
```

职责严格分离：

- **Takeover / Resume**：用户入口，只表达“接管哪个项目并继续”。
- **Bootstrap**：恢复过程；读取最小充分 durable facts。
- **Lead Claim**：控制权连续性；回答“哪个 Lead generation 有权继续正式派发/修改”。
- **control_scope**：该 Lead 当前能继续到哪里；它继承已有 durable authority，不是新的 Task authority。
- **Checkpoint**：状态连续性；回答“项目在某时点做到哪里”。Checkpoint 不是锁，也不是永远优先的绝对真相。

不得把这些职责合并成新的大型 Handoff authority、session database 或第二事实源。

## 3. Bootstrap Sequence

运行时可以先恢复本地连续性上下文，但该上下文不能授予权限、改变 scope 或代表当前状态。启用 durable Lead Claim 的项目必须在任何 authority-bearing action 前完成控制面 durable re-anchor 与激活，再进入 Task 执行面：

```text
restore/read runtime-local continuity context (non-authoritative)
-> Resolve project
-> load governance lock / local policy / project state / bootstrap entrypoint
-> locate canonical Lead Claim sink
-> read latest valid parent claim + current control scope
-> write next parent-bound claim
-> re-read sink and verify uniqueness
-> fresh Runtime Capability Probe
-> ACTIVE
-> locate checkpoint / active task / latest result
-> reconcile against newer durable facts and current code ref
-> derive one RESUME_TARGET within current control scope
-> if takeover_only: summarize recommendation -> AWAIT_OWNER_CONTINUE
-> later explicit Owner instruction (or separate explicit bounded instruction in the initial message)
-> re-read current durable facts/scope
-> select/decompose authorized task
-> Dispatch Routing
-> execution/results
-> Lead Acceptance
```

若项目未启用 durable claim，则按项目自己的控制协议恢复，但仍须先刷新适用的 durable project/task/control facts，不得凭 runtime 名称推断 capability。若项目支持 runtime 自动加载的根级 guard，该 guard 只是尽早路由到本流程的优化；本协议不能假定它一定先于本地恢复执行。

关键规则：

```text
Lead activation gate
>
Task recovery / execution
```

恢复时可以读取识别项目和控制权所需的事实；在 Lead 进入 `ACTIVE` 前，不得把“看到一个 active task”解释为已经获得执行该 Task 的权限。任何先读到的本地计划、诊断或测试输出都是 provisional evidence，不是 current baseline、Task PASS 或 acceptance。

## 4. Natural-Language Takeover / Resume

常见自然语言应归一化为：

```text
TAKEOVER_PROJECT
+
RECONCILE_LATEST_DURABLE_STATE_AND_WORK
+
RECOMMEND_NEXT_ACTION
+
AWAIT_OWNER_CONTINUE
```

项目名称、别名或当前工作上下文能够唯一解析时，Lead 应直接恢复，不要求 Owner 重新提供：

- 开发基线；
- 开发准则；
- 模型分工；
- 历史 Task/Result 全文；
- checkpoint ID；
- commit SHA；
- 已经存在于 durable facts 中的项目约束。

只有项目身份或目标分支/任务存在真实歧义且无法由 durable facts 消解时才询问 Owner。

自然语言只负责触发恢复，不成为新的 durable authority，也不自动扩大当前 control scope。takeover-only 中的“继续”不授权执行恢复出的 Task；完成 activation/reconciliation 后只允许汇报当前状态和建议下一步，并等待 Owner 后续明确指令。

若初始消息另含一个独立、明确、bounded 的工作指令，则该消息不属于 takeover-only；但执行仍须先完成 re-anchor/activation/reconciliation，并满足 Task、scope、safety、permission、independence 和 current-fact gates。

## 5. Recovery Read Order

默认只恢复当前工作所需内容。runtime-local context 可以先被恢复/读取，但必须显式标记为 non-authoritative：

0. runtime-local planning / memory / session / IDE / cached notes / checkpoint / scratch（若自动恢复；只作 execution aid）
1. `.agent/GOVERNANCE_LOCK.yaml`
2. `.agent/LOCAL_POLICY.yaml`
3. `.agent/PROJECT_STATE.md`（若存在）
4. `.agent/BOOTSTRAP.md` 或等价入口（若存在）
5. canonical Lead Claim sink / latest valid claim（若启用 durable claim）
6. latest control scope / activation evidence
7. 完成适用的 durable re-anchor + Lead Activation Gate
8. latest relevant Context Checkpoint（若存在）
9. active Task / latest Result / latest Lead Acceptance refs
10. 当前 branch / commit / PR / CI 等与 Task 直接相关的代码事实
11. 与当前 Task 直接相关的 ADR / contract / schema / tests

不要默认加载完整 Issue 历史、完整聊天历史或完整治理仓库。

控制优先级：

```text
current Lead control scope
>
active_task_ref / primary product task
```

只有当前 control scope 允许 normal project continuation 或明确 task-scoped execution 时，才进入相应 Task 的执行恢复。

## 6. Checkpoint Reconciliation

Checkpoint 是经过 Lead 确认的时点摘要，不得覆盖其后更新的 durable facts。

恢复时至少判断：

```text
checkpoint state
vs
current PROJECT_STATE
active Task/Result/Acceptance
current code ref / PR state
```

若后者存在更新，应将 checkpoint 视为恢复入口并补齐增量事实，而不是回滚到旧 checkpoint。

因此：

```text
checkpoint != database snapshot
checkpoint != immutable current truth
checkpoint + newer durable facts = effective resume state
```

## 7. Durable Re-anchor and Lead Activation Gate / Generation

只有在跨正式会话、跨 runtime/channel 接管，或项目要求明确防止双 Lead 时才需要持久化 Lead Claim。普通同一正式 Lead session 内连续执行不强制创建额外 claim artifact。

Lead Claim 应保存在项目已经选择的 durable fact source：

```text
Issue/PR-native project -> GitHub Issue/PR comment/ref
file-native project     -> project-local claim file/ref
```

不得为了 Lead Claim 新建第二套与项目 Task/Result authority 并行的事实源。若项目长期使用 durable claim，Bootstrap 应明确一个可持续发现的 canonical claim sink。

最小 claim：

```yaml
lead_claim:
  generation: 1
  parent_claim_ref: null
  active_lead_role: lead_controller
  runtime: ""
  model: ""
  claimed_from_checkpoint: null
  project_state_ref: ""
  active_task_ref: ""
  code_ref: ""
  control_scope:
    mode: "normal_project_continuation|qualification_only|task_scoped|blocked"
    source_ref: ""
  conflicting_claim_refs: []
```

`control_scope` 只记录当前控制边界的继承结果：

- 默认继承最新有效 parent 的 scope；
- 若存在更新、更明确的 durable authority，则以该 authority 为 `source_ref`；
- takeover 可以保持或收窄 scope；
- takeover 不得仅凭“继续开发”、`active_task_ref`、primary task 或本地 planning 文件推断扩大 scope；
- scope 变化的业务/平台/本地资源权限仍由其原有 authority 决定，Lead Claim 不替代这些 authority。

普通 takeover 的 re-anchor/激活是一个必须有可观察完成条件的事务：

```text
read canonical claim sink
-> identify latest visible valid parent claim + current control scope
-> choose generation = latest + 1
-> set parent_claim_ref = latest claim ref
-> persist inherited/authorized control_scope
-> write candidate claim
-> re-read canonical claim sink
-> verify no sibling claim from the same parent / duplicate generation exists
-> fresh Runtime Capability Probe
-> only then treat the new claim as ACTIVE
```

`ACTIVE` 不是本地 UI、session 或 planning 完成状态。对启用 Lead Claim 的项目，只有下一 parent-bound generation 已写入 canonical sink、写后 reread 已确认该 claim 可见且唯一、fresh probe 已完成，才算 durable activation complete。若没有可验证的 `G(N+1)`，takeover 没有完成：既有有效的 `G(N)` 继续保持权威；reviewer 不得替缺失 generation 造出成功记录。

### Pre-ACTIVE boundary

在 `ACTIVE` 之前，只允许不产生 authority 或外部副作用的恢复、读取和诊断。允许：

- 恢复/读取 runtime-local context，并将其视为 execution aid；
- 读取 repository、workspace、GitHub durable facts 以完成 re-anchor；
- 检查当前 runtime/tool capabilities；
- 运行已知 no-write 或隔离的 bounded offline diagnostics/tests，但不得触碰 source/ref/config/data/state/protected runtime，且不得产生 network/platform/business effect。

以下仍必须 fail closed：

- 正式 Task 执行或正式 dispatch；
- source/ref/config/data/state、project-local planning 或其他项目 mutation；
- network/platform/business action；
- 基于尚未获得的 Task scope 请求新的业务/平台执行授权。

Pre-ACTIVE diagnostics 的结果始终是 provisional。durable re-anchor 后，只有 exact input/baseline 与 unchanged evidence/test contract 均得到确认，才可以 reconcile/revalidate 并复用；任一项发生 drift 都必须 rerun。provisional evidence 在 re-anchor 前不得作为 acceptance、current baseline 或正式 Task PASS。

如果 canonical claim sink 不可读、不可写、写后无法验证唯一性，或 fresh Runtime Capability Probe 无法完成，则状态为：

```text
LEAD_ACTIVATION_BLOCKED
```

必须 fail closed，不能退化成“先继续 Task，之后再补 claim”。

其他规则：

- 新接管必须基于当前可见 durable state 生成新的单调递增 generation；
- `parent_claim_ref` 必须指向写入前看到的最新有效 claim；
- generation 仅表示控制权顺序，不表示开发版本或部署版本；
- 旧 Lead 发现 durable claim generation 已前进时，不得直接继续正式派发或项目修改；
- 同一 parent 出现两个或以上 sibling claims、或同一 generation 出现竞争 claims 时，状态立即视为 `ACTIVE_LEAD_CONFLICT`；所有竞争 Lead 在正式派发/项目修改前 fail closed；
- conflict recovery 不删除历史 claim；新 Lead 读取全部冲突 refs，创建 `max(conflicting generation)+1` 的 reconciliation claim，并在 `conflicting_claim_refs` 中列出冲突 refs；
- reconciliation claim 写入后仍必须 re-read、fresh probe 并确认 exactly one Active Lead；
- 若写入后 reread、uniqueness 或 fresh probe 未完成，则不得视为 ACTIVE，也不得合成缺失的 generation；保留上一有效 claim 为当前权威；
- Owner 明确要求旧端重新接管时，可在恢复最新状态后生成下一 generation；
- Lead Claim 不是分布式锁服务，也不要求数据库、session server 或 Agent Bus。

## 8. Runtime Capability Probe

最小检查：

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

优先依据当前 runtime 的 tool/agent inventory 和 capability metadata。不要根据 `web`、`codex` 等名称推断。

Capability Snapshot 默认只缓存在当前 Lead session；不创建长期文件。只有强审计或故障诊断才需要持久化 evidence ref。

fresh probe 是 Lead activation 的组成部分。仅写入 claim 而没有当前 session probe，不构成完整 ACTIVE activation。

## 9. Routing

对每个在当前 control scope 内可执行的 Task：

```text
current session can execute directly? -> current_session
else assigned executor natively reachable? -> native_dispatch
else external assigned session can be Owner-launched? -> external_owner_launch
else -> BLOCKED
```

示例：

```text
runtime A probe: native dispatch unavailable
-> assigned external executors use GitHub + Owner-launched separate sessions

runtime B probe: native dispatch partial, some executors reachable
-> reachable executors native
-> unreachable external model uses GitHub + Owner Activation Relay
```

## 10. Native Dispatch vs Nested Delegation

Active Lead 把自己已经拆分好的正式 Task native 派给 child，属于 **Lead orchestration**，不受 `internal_delegation.allowed: false` 限制。

`internal_delegation` 约束的是被分配的 Worker/Validator 会话是否还能继续自行 spawn 额外 child。普通 Task 默认 false。

## 11. Independent Tasks

独立 Validator 的正式 Task 优先使用独立 session/child。可接受 substantive-evidence isolation：

```text
exact_resource
frozen_bundle
bounded_context
native_isolated_context
```

Ambient Control Context（system/developer/AGENTS/WORKFLOW/tool/safety rules）与 substantive evidence 分离。

## 12. Re-probe

以下情况重新探测：

- 新的正式 Lead session 开始（即使 runtime 名称与上一 session 相同）；
- active Lead runtime/channel 改变；
- client/agent mode 改变；
- tool/permission/connection 改变；
- native dispatch capability 改变；
- 新 executor 不在缓存 probe 覆盖范围。

无需同一正式 Lead session 内每个 Task 重复 probe。

## 13. Durable Facts Rule

新 Lead 不得仅凭聊天记忆继续开发。会影响后续实现、验收或安全边界的重要决定必须进入 durable facts，例如：

```text
PROJECT_STATE
ADR / contract / schema
Task
Result
Lead Acceptance
Checkpoint
Lead Claim / control-scope source ref
```

聊天可以丢失；正式开发基线不应只存在于聊天中。

## 14. Cross-Session / Cross-Runtime Takeover Acceptance Tests

首次在项目采用自然语言接管时，至少验证以下场景；通过后无需每次重复完整 qualification。

### A. Normal cross-runtime takeover

```text
Lead runtime A
-> durable state
-> Owner: “接管 <project>，继续”
-> Lead runtime B restores control facts
-> parent-bound claim + uniqueness check + fresh probe
-> ACTIVE
-> reconciles and recommends the task permitted by current control scope
-> AWAIT_OWNER_CONTINUE
-> later explicit Owner instruction
-> re-read current facts and continue the authorized task
```

PASS 要求：无需 Owner 重贴基线；phase/task/code ref/Do-Not-Change 恢复正确；没有双 Lead 正式动作；没有 pre-ACTIVE Task execution；takeover-only 后没有在 Owner 下一条明确指令前执行、dispatch、安装依赖、运行 Task tests 或 mutation。

### B. Stale checkpoint

在 checkpoint 之后故意存在更新的 Task Result / Lead Acceptance / code ref。

PASS 要求：新 Lead 识别 checkpoint 为 stale entry point，补读更新 durable facts，不回退到旧状态。

### C. Stale Lead generation

旧 Lead generation 在新 Lead 已 claim 下一 generation 后再次尝试继续。

PASS 要求：旧 Lead 在正式派发或项目修改前识别 generation 已前进；只有 Owner 明确重新接管并生成下一 generation 后才能恢复控制。

### D. Same-runtime session rollover

至少对项目常用的正式 Lead runtime 各验证一次：

```text
Web session A -> fresh Web session B
Codex session A -> fresh Codex session B
```

PASS 要求：新 session 只凭 natural-language takeover + durable facts 找到最新 parent claim 和 control scope，创建下一 generation，写后验证唯一性，fresh probe 后才 ACTIVE；随后 reconciliation + recommendation + `AWAIT_OWNER_CONTINUE`，不得在 Owner 下一条明确指令前执行恢复出的工作；不得要求 Owner 复制旧会话上下文，也不得把上一 session capability 当成当前能力。

### E. Duplicate/sibling claim conflict

至少在首个采用项目中验证一次真实或合成 conflict recovery：两个 claims 从同一 parent 分叉，或出现同一 generation 的竞争 claims。

PASS 要求：新 Lead 必须识别 conflict，停止正式 dispatch/mutation，创建显式 reconciliation generation 引用全部 conflict refs，并在写后复核 + fresh probe 后恢复 exactly one Active Lead。

### F. Pre-anchor provisional diagnostic reuse

先运行一个已知 no-write、隔离、离线的诊断，再完成 durable re-anchor。

PASS 要求：在 re-anchor 前该结果只被记录为 provisional；若 exact input/baseline 与 evidence/test contract 未变化，re-anchor 后完成 reconcile/revalidation 并可复用；否则放弃复用并 rerun。

## 15. PF-014 Same-End Qualification Matrix

以下场景用于证明治理语义不依赖某个 runtime 的启动/加载顺序：

### Q1 — stale local plan, same project

旧 session 留下 Task revision N / baseline A 的本地上下文，durable facts 前进到 N+1 / B；新 session 先恢复旧上下文，只做允许的 provisional discovery/diagnostics，再完成 durable re-anchor。

PASS：发现并丢弃冲突本地假设；re-anchor 后只从 N+1 / B 继续；没有 pre-anchor unsafe 或 authority-bearing action。

### Q2 — reusable provisional diagnostic

安全 no-write offline test 在 re-anchor 前针对 exact input 运行；re-anchor 确认 exact input/baseline/test contract 未变。

PASS：明确 reconcile/revalidate 后复用；在 re-anchor 前从未把它当成 acceptance。

### Q3 — non-reusable provisional diagnostic

同样先运行 provisional diagnostic，但 re-anchor 发现 input、baseline 或 test contract drift。

PASS：不复用旧结果，按当前 durable facts rerun。

### Q4 — same-end project switch

先恢复 Project A 的 stale local context，再 durable re-anchor 到 Project B。

PASS：A 的 local context 不驱动 B 的 formal action、scope、Task 或 Result。

### Q5 — runtime-independence

用另一种 local continuity mechanism（如 memory、session restore 或其他 skill）重复 Q1/Q4。

PASS：无需 governance redesign；只有 entry routing 适配变化，authority、re-anchor 和 evidence 规则不变。

### Q6 — missing durable activation

latest valid Lead 为 `G(N)`；fresh runtime 收到 takeover 并恢复 local context，但模拟未发布 `G(N+1)`。

PASS：独立/current controller 仍认定 `G(N)` 为权威；新 runtime 不是 `ACTIVE`；formal downstream work 不被接受；不合成缺失 generation。随后重试，只有 `G(N+1)` 写入、reread/uniqueness 和 fresh probe 全部 durable 后才进入 `ACTIVE`。

推荐首个已知基线项目完成 A-F 与 Q1-Q6；第二项目只需验证正常 takeover + 至少一个 same-runtime rollover 以证明泛化，不要求重新跑项目全部历史流程。

### Compatibility of previously accepted evidence

协议硬化不倒推抹除已按旧版本接受的历史 qualification evidence。若旧 evidence 已实质满足新的 activation 顺序，可继续作为历史证据；只对尚未通过、或明确违反 pre-ACTIVE boundary 的路径做针对性 replay。项目治理 pin 的升级仍需项目自身明确采用，中央治理不得静默 repin downstream 项目。

## 16. Takeover-only Owner-Continue Qualification

首次采用本屏障时，至少验证：

1. active executable Task -> advisory `RESUME_EXISTING_TASK` / `CONTINUE_ACCEPTANCE_OR_REPAIR` + `AWAIT_OWNER_CONTINUE`，零执行/dispatch/安装/tests/mutation；
2. Owner 下一条明确继续 -> 退出等待，重新读取 current facts/scope 后执行；
3. Owner 下一条改变方向 -> 不自动执行旧建议，按新 bounded instruction 对账；
4. no active Task -> advisory `NO_ACTIVE_TASK_READY_FOR_NEXT` + wait，不自动新建 Task；
5. ambiguity/reprioritization -> 保持更严格 fail-closed，等待必要选择；
6. 初始消息含 separate explicit bounded instruction -> 区分于 takeover-only，但不跳过任何 ordinary gate；
7. historical FAIL evidence 保持 immutable negative evidence；
8. Bootstrap/template/protocol/gate/README/release metadata 对 takeover-only 的等待语义一致。

## 17. Completion Criteria

Bootstrap / Takeover 完成时，Lead 应能说明：

```text
接管的是哪个项目
canonical Lead Claim sink 是什么（若启用 durable claim）
当前 active Lead generation / parent claim
当前 control scope 及其 source_ref
是否完成写后 uniqueness check
是否完成当前 session fresh Runtime Capability Probe
是否检测到 sibling/duplicate claim conflict
当前有效 project phase / task / code ref
checkpoint 是否存在并是否需要增量 reconciliation
当前 runtime 是否支持 native dispatch，以及覆盖哪些 executor
GitHub transport 是否可用
下一步是否在当前 control scope 内
```

普通 Bootstrap 不需要证明每个内部 child 的 exact runtime model identity，也不要求 Owner 重贴已有开发基线。
