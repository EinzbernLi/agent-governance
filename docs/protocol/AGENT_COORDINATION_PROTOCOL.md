# Agent Coordination Protocol

版本：0.3.16
状态：Accepted role and coordination owner

## 1. Core Roles

### Lead Controller

唯一正式总控，负责：架构、Task decomposition、model routing、dispatch、并行安全判断、冲突裁决、Review 与最终 PASS/REWORK/REJECT/BLOCKED。核心实现不是 Lead 的 intrinsic duty；实现类工作按 Dispatch Policy 的 route 决定由 Lead 直接执行或派给 qualified native child。

任一正式项目任务链只能有一个 active Lead Controller。多个并行 Web/Codex 会话可以同时执行不同 Task，但它们是 task-scoped Worker/Validator，不得创建同项目 sibling Lead Claim。

### Worker

只执行 Task 明确授权的范围，不得扩大 scope、修改 forbidden area、降低 tests/acceptance criteria、接管项目 Lead 或宣布最终 accepted。

### Validator

独立寻找失败、回归、边界和越权问题；只提供验证证据，不拥有最终验收权。

## 2. Standard Flow

```text
Active Lead
-> provisional restore/read local context
-> refresh durable control
-> if Lead Claim is enabled: write next parent-bound claim -> reread sink and verify uniqueness
-> fresh Runtime Capability Probe (once per Lead session, then cache)
-> complete applicable Lead activation -> ACTIVE
-> decompose work
-> classify each Task as serial or parallel_safe
-> choose Worker/Validator + reasoning
-> write GitHub Task Packages
-> route each ready Task:
     current_session
     native_dispatch
     external_owner_launch
     blocked
-> dispatched child lifecycle: CHILD_RUNNING -> PARENT_WAITING -> terminal event
-> read terminal Result
-> parallel_safe executors may run concurrently
-> executors write Results to GitHub
-> Lead verifies durable handoff
-> Lead reviews / rework / integrates
-> Lead final acceptance
```

Canonical Dispatch rules:

- `docs/protocol/DISPATCH_ROUTING_PROTOCOL.md`
- `config/DISPATCH_POLICY.yaml`

## 3. Native and External Are Delivery Routes, Not Different Governance Models

Native/current/external/blocked are delivery routes, not roles. Their selection,
capability proof and economy preference are owned by
`config/DISPATCH_POLICY.yaml`. This protocol only preserves the coordination
boundary: the active Lead dispatches; a Worker/Validator stays Task-scoped; the
Owner may relay external activation but not Task/Result content.

## 4. Runtime Capability Is Observed, Not Assumed

Runtime capability/profile precedence is owned by Dispatch Policy. Coordination
must never infer capability or authority from a Web/Codex/Desktop label.

## 5. Same-Project Parallel Workstreams

同一个项目允许多个正式 Task 并行执行，但只允许一个 Active Lead。

Task 只有在 Lead 明确标记 `parallelism.mode: parallel_safe` 后才可与 sibling Task 并发。Parallel-Safe Gate 必须同时满足：

1. 每个 Task 绑定 exact frozen baseline；
2. objective、scope、allowed/forbidden files/evidence 明确；
3. dependencies 已声明，且不存在要求先后顺序的未满足 dependency；
4. sibling Task 的**实质项目写入范围**两两不重叠；读取同一文件/证据可以重叠；
5. 实现类 Task 使用独立 branch/PR、worktree 或其他隔离写入表面；
6. 每个 executor 只写自己的 Result/PR evidence，不修改 Lead Claim 或 sibling Task authority；
7. Lead 保留 integration order、冲突裁决和最终 acceptance。

默认规则：

```text
read overlap = allowed
append-only Result comment sharing = allowed when task refs stay unambiguous
substantive write overlap = not parallel-safe by default
shared mutable state write = not parallel-safe by default
undeclared dependency = not parallel-safe
same project parallel workers != multiple Leads
```

如果两个 Task 需要修改同一项目文件、同一 schema migration、同一共享生成物或同一可变运行状态，Lead 必须改为串行，或先重新拆分到真正不重叠的写入范围。不得用“最后再解决 merge conflict”替代 Parallel-Safe Gate。

如果 sibling work 在执行期间合入了会改变本 Task write scope / dependency assumptions 的变更，executor 不得静默吸收新基线。由 Lead 决定 `rebase/replan/serialise` 后再继续集成。

若 drift 只改变 candidate merge currency，而本地 payload/evidence 对应的 factual/schema/materialization/ignore contract 未变，Lead 可以保留该本地证据并冻结 lightweight reconcile + exact-head revalidation。**stale candidate 不能 accepted；可复用 evidence 也不能赋予 candidate currency。**

Parallel workstream 不是 distributed lock、Agent Bus、第二套 Task store 或第二个 Lead authority。

## 6. Nested Delegation

Runtime-profile default：

```yaml
codex_worker: true_when_native_capability_proven
web_or_generic_worker: false
```

如果 Lead 已经把不同 qualified executor roles 拆成正式 Task，应分别派发，不让某个 Worker 再重做一遍正式模型路由。

Codex Worker child use is optional and may serve material quota preservation,
specialization, context isolation or elapsed-time benefit. Parent accountability,
qualification, scope/permission/evidence/result boundaries and explicit write
ownership remain hard. Parallel child writes are disjoint; overlap serializes or
fails. Child review is not independent validation and recursive child delegation
remains default false. Task/Lead may explicitly tighten or override the profile.

### 6.1 Delegated lifecycle and observation discipline

The delegated lifecycle, wait behavior, intervention reasons and contamination
rules are owned by `config/DISPATCH_POLICY.yaml`. This role protocol only
requires that parent accountability and Worker/Validator role boundaries remain
unchanged through that lifecycle.

## 7. GitHub Fact Source

以下长期事实必须落在 GitHub/项目唯一事实源：

- architecture/ADR；
- Task Package；
- frozen substantive evidence；
- Result；
- Review/acceptance；
- project state；
- routing/calibration changes that affect future work。

Session Runtime Capability Snapshot 默认不属于长期事实；它是当前 Lead 会话的临时 execution state，除非强审计/故障诊断要求持久化。

Parallel workstream 状态直接由各 Task / Result / PR 表达，不另建 parallel-session database。

Executor-local planning、scratch、客户端会话状态也不是 durable Task authority。它们可以帮助执行者组织工作，但不得新增 Task Gate、改变 acceptance/tests、关闭 Task 或覆盖 GitHub 最新授权。

## 8. Same-End Re-anchor and Provisional Diagnostics

同端 resume/switching 不要求某个 runtime-specific skill 或根级入口一定先加载；这些入口只提供 routing optimization。runtime-local planning、memory、session restore、IDE state、checkpoint 和 scratch 都只是 execution aid，不能覆盖 durable control、Task revision、baseline、Result 或 acceptance。

在 durable re-anchor / applicable Lead activation 完成前，允许：

- 恢复/读取 local context；
- 读取 repository/workspace/GitHub durable facts；
- 检查 runtime/tool capabilities；
- 运行已知 no-write 或隔离、offline、无 platform effect 且不触碰 source/ref/config/data/state/protected runtime 的 bounded diagnostics。

在此之前禁止 authority-bearing Task work、formal dispatch、source/ref/config/data/state mutation 及 network/platform/business action。诊断结果只能是 provisional evidence，不是 current baseline、Task PASS 或 acceptance。

对启用 Lead Claim 的项目，re-anchor 只有在“读当前控制 -> 写下一 parent-bound generation -> reread canonical sink 并验证唯一性 -> fresh probe -> ACTIVE”完整且可观察时才算完成。若没有可验证的下一 generation，上一有效 generation 保持权威；不得由 reviewer 或 local context 合成缺失 generation。

re-anchor 后，只有 exact input/baseline 与 evidence/test contract 未变化且已完成 reconcile/revalidation，才可复用 provisional evidence；发生 drift 必须 rerun。Project switch 也必须重新解析 durable project identity，旧 Project 的 local context 不得驱动新 Project 的 formal action。

## 9. Independence

Independent Validator 需要真实 substantive-evidence isolation：

```text
exact_resource
frozen_bundle
bounded_context
native_isolated_context
```

Ambient Control Context（system/developer/AGENTS/WORKFLOW/tool/safety rules）与 substantive evidence 分开；未经授权的旧分析、旧结果、额外项目事实或 timeline 才构成污染。

若 accepting Lead/parent 在 Validator terminal handoff 前进行 material substantive observation 或 steering，并改变该 Validator 的 evidence boundary，该次运行不得计为 required independent validation；Task 仍要求独立验证时必须取得 fresh substantively independent validation。仅有 ambient control context 不构成 contamination。

## 10. Failure / Escalation

执行质量失败：

```text
rework same executor if appropriate
-> raise reasoning / switch qualified executor
-> Lead takeover for architecture/core conflict
```

Parallel-safety failure：

```text
write-scope overlap / dependency drift / baseline invalidation
-> stop concurrent integration
-> Lead rebase / replan / serialise
```

Dispatch 失败：

```text
native unavailable
-> external Owner launch available? use it
-> otherwise BLOCKED
```

不要把 dispatch limitation 误判为 model capability failure。

Durable handoff 缺失：

```text
executor runtime/UI reports done
-> Lead reads declared result sink + expected remote refs
-> required Result/ref missing or inconsistent
-> INCOMPLETE_HANDOFF
-> resume same Task only to finish durable handoff when appropriate
```

不要让 Owner 诊断或复制本地 Result；Lead 从 GitHub 检查。

## 11. Audit Questions

每个正式 Task 应能回答：

1. Task 为什么存在、scope/acceptance 是什么？
2. Lead 分配给哪个 role/model/reasoning？
3. 实际 route 是 native 还是 external？
4. Result ref/commit/artifact 是什么？
5. tests/validation 做了什么？
6. 是否越过 scope/permission/evidence boundary？
7. Validator 是否独立？
8. 若并行执行，为什么 `parallel_safe`，sibling Task 是哪些？
9. 是否出现 write-scope overlap、dependency/baseline drift？
10. durable Result 是否已写入并 read-back，预期 remote mutation 是否与 Result 对账？
11. Lead 为什么 PASS/REWORK/REJECT/BLOCKED？
12. durable re-anchor/activation 是否完成并有可观察 evidence；若未完成，旧 generation 是否仍保持权威？
13. pre-anchor diagnostic 是否明确为 provisional，且 reuse/rerun 是否按 exact input/baseline/test contract 对账？

普通任务不要求回答内部每一级 child exact model identity。Worker/Validator 的 normal execution difficulty、failed first attempt、search 或 command adaptation 不是 blocker；只有缺少必要 authority/permission/fact/decision/capability 且没有安全的 in-scope alternative 才能 `BLOCKED` / `NEEDS_ATTENTION`。

## 12. Owner Interaction

正常目标：

```text
Owner starts/uses Active Lead
Lead handles decomposition + GitHub Tasks
Lead marks independent Tasks parallel_safe where justified
Lead natively dispatches what it can
Owner only launches genuinely unreachable external sessions
Executors write GitHub Results
Lead verifies durable handoff
Lead integrates and accepts
```

Owner 不承担 Git/worktree 细节、长 Prompt 搬运或 Agent 结果复制。需要外部 Web Worker 时，Owner 只负责打开会话并发送 Task ref，不负责同步 Task 内容。

Owner 说“外部 Agent 已完成”只表示 runtime execution 已停止、请 Lead 检查 durable handoff；这不是 Task PASS/accepted，也不是 Result 已存在的证明。

## 13. Durable Completion Invariant

```text
runtime completion != durable Task completion
local planning != Task authority
entry routing != durable re-anchor
missing activation generation != ACTIVE
canonical Result + read-back verification = worker handoff complete
Lead acceptance remains separate
```

Task 要求 remote mutation 时，durable handoff 还要求 Result exact ref 与实际 remote ref 一致。任一步缺失都不得进入实质 Review/Acceptance。
