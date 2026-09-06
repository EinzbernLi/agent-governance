# Project Bootstrap

> 可选的新会话入口。保持短小，不复制完整项目历史；如果 repo/PROJECT_STATE 已足够冷启动，可以不创建本文件。

## Project

```yaml
project_name: ""
project_aliases: []
project_purpose: ""
current_phase: ""
active_task_ref: ""
governance_ref: ""
last_stable_checkpoint: ""
lead_claim_sink: ""
task_fact_source: github_issue_pr|file_native
```

## Natural-Language Resume

当 Owner 使用类似以下表达时：

```text
“接管 <project> 的开发，我们继续”
“切到 <project>，接着上次继续”
“这边接手 <project>”
```

若 `project_name` / `project_aliases` 能唯一解析项目，应直接进入 Bootstrap/Resume，不要求 Owner 重贴开发基线、治理准则、checkpoint ID、Task ID 或 commit SHA。

自然语言入口不是 durable authority；实际恢复仍以 repo/GitHub durable facts 为准。只含接管/继续的消息属于 `takeover_only`：`继续` 表示恢复 durable state/work 并给出下一步建议，不授权执行该建议，也不表示重新规划、新建 Task 或扩大 scope。

## Runtime-Auto-Loaded Cold-Start Guard

如果某个正式 Lead runtime 会自动加载仓库根级指令文件，项目应优先复用现有根级指令文件，在最前部放置一个极短 cold-start guard，把正式 takeover/resume 路由到本 Bootstrap。guard 是优化而不是 authority。

采用 Governance Lock schema `0.5+` 后，稳定入口语义是：

```text
new formal Lead / takeover / resume
-> read GOVERNANCE_LOCK source + exact accepted pin + update_policy
-> obey update policy:
     github_native_notify -> read downstream-local update signal if present; no signal means no upstream probe
     manual_pinned        -> no proactive upstream check
-> read LOCAL_POLICY + PROJECT_STATE + BOOTSTRAP
-> locate canonical Lead Claim sink + current control scope
-> complete Lead Activation Gate
-> ACTIVE
-> Post-Activation Work Reconciliation Gate
-> derive one RESUME_TARGET as a recommendation
-> if takeover_only: summarize current state + recommended next action
-> if takeover_only: AWAIT_OWNER_CONTINUE
-> only a later explicit Owner instruction (or separate bounded initial instruction) may authorize Task execution/dispatch/mutation
```

若本地 update signal 存在、或 Owner 明确要求检查/升级，才读取治理上游 `VERSION / GOVERNANCE_RELEASE.yaml` 和该 release 所需的最小升级材料。发现新版不等于采用新版。

要求：

- 不要为不支持自动加载的 runtime 发明 daemon、session service 或第二入口系统；
- `ACTIVE` 前只允许非权威恢复/读取与安全诊断，不得正式 Task/dispatch、项目 mutation 或业务动作；
- `takeover_only` 在 `ACTIVE` + reconciliation 后仍必须停在 `AWAIT_OWNER_CONTINUE`；不得把接管词中的“继续”重复用作执行授权；
- `GOVERNANCE_LOCK` 的 accepted source/ref 在显式 pin 更新前始终是当前治理 authority；
- `LOCAL_POLICY` 始终是 downstream 项目自己的补充规则层，不因上游更新检查被上传、覆盖或删除；
- cold-start guard 不得镜像 generation/current Task，不得成为第二 Task/Result/Claim store。

## Rule layering

```text
accepted upstream governance invariants
>
project .agent/LOCAL_POLICY.yaml
>
explicit bounded Task scope/authorization
>
runtime-local planning
```

下层可以细化或收紧上层，但不得静默弱化上层。Task 可以满足 `LOCAL_POLICY` 明确要求的 Task authorization gate，但不能删除该 local policy。上游升级若与项目 local policy 真正冲突，必须停止 adoption 做 compatibility review；当前 accepted pin 在显式更新前继续有效。

## Required Read Order

0. runtime-local context（execution aid only）
1. `.agent/GOVERNANCE_LOCK.yaml`
2. 按 `update_policy` 处理更新发现：
   - `github_native_notify`：读取 downstream-local update signal（若存在）；无 signal 不主动访问上游；
   - `manual_pinned`：普通 takeover/new Task 不访问上游；
3. `.agent/LOCAL_POLICY.yaml`
4. `.agent/PROJECT_STATE.md`（若存在）
5. 本 `.agent/BOOTSTRAP.md`
6. canonical Lead Claim sink / latest valid claim
7. latest control scope / activation evidence + Lead Activation Gate
8. latest checkpoint（若存在）
9. current/in-flight Task candidates
10. latest Result / Review / Lead Acceptance
11. directly related branch / commit / PR / CI
12. directly related ADR / contract / schema / tests
13. Post-Activation Work Reconciliation Gate -> exactly one `RESUME_TARGET`

GitHub Issue/PR-native 项目不要求维护重复 `TASK_INDEX.md` / `.agent/tasks/` 镜像。Checkpoint 与 `PROJECT_STATE` 都不能覆盖更新的 durable facts。

治理 source/update/adoption：`docs/project-adoption/GOVERNANCE_CURRENCY_PROTOCOL.md`。  
接管恢复：`docs/context-continuity/TAKEOVER_RECONCILIATION_GATE.md`。

## Governance Update Policy

接入阶段 AI 必须让 Owner 选择：

```text
github_native_notify
manual_pinned
```

- `github_native_notify`：GitHub 原生机制只负责发现新版并在当前项目留下 local signal；不自动采用；
- `manual_pinned`：固定当前 exact pin；日常开发不主动查询上游；
- 两种模式都禁止 `auto_follow_main`、自动 adoption 和 automatic pin advancement；
- Owner 明确要求升级时，AI 做 compatibility review 后才修改 `GOVERNANCE_LOCK`。

## Lead Activation Gate

启用 durable claim 的正式 Lead takeover：

```text
read canonical claim sink
-> latest valid parent + control scope
-> write next parent-bound generation
-> re-read sink
-> verify no sibling/duplicate claim
-> fresh Runtime Capability Probe
-> ACTIVE
```

无法完成则 `LEAD_ACTIVATION_BLOCKED` 并 fail closed。

## Post-Activation Work Reconciliation Gate

`ACTIVE` 后、任何新 Task / planning branch / reprioritization / formal dispatch 前：

```text
reconcile accepted governance pin + chosen update policy/local signal
-> classify PROJECT_STATE freshness
-> locate current/in-flight Task(s)
-> read latest Result / Review / Lead Acceptance
-> reconcile related branch / PR / code refs
-> classify blocker/dependency
-> derive exactly one RESUME_TARGET as a recommendation
-> if takeover_only: AWAIT_OWNER_CONTINUE
```

允许：

```text
RESUME_EXISTING_TASK
CONTINUE_ACCEPTANCE_OR_REPAIR
BLOCKED_WAITING_EXTERNAL_DEPENDENCY
NO_ACTIVE_TASK_READY_FOR_NEXT
OWNER_REPRIORITIZATION_REQUIRED
RECOVERY_AMBIGUOUS
```

`RECOVERY_AMBIGUOUS` fail closed。`PROJECT_STATE` 必须分类 `CURRENT_ENOUGH | STALE_BUT_RECONCILED | STALE_BLOCKING_RECOVERY`。

`RESUME_TARGET` 是恢复建议，不是执行授权。对 `takeover_only`，在 Owner 后续明确继续或给出其他 bounded instruction 前，不得修改 source/planning/Task work product、安装依赖、运行 Task tests、dispatch 或产生 Issue/PR/runtime/platform/business mutation。后续 Owner 指令到达后，先重新确认 durable facts、scope 和适用 gates，再执行。

## Handoff Rule

新会话不得仅凭聊天记忆继续开发。对 `takeover_only`，Lead Activation Gate + Post-Activation Work Reconciliation Gate 只允许进入 `AWAIT_OWNER_CONTINUE`；必须等 Owner 后续明确指令后，才能进入代码修改、正式 dispatch 或任务拆解。

Owner 不应成为内容搬运者；已有 durable facts 不要求 Owner 重贴。

正式 Worker / independent Validator 的 Startup Card **不在本 Bootstrap 定义**。Lead 必须按 `docs/task-package/TASK_PACKAGE_SPEC.md` 使用 canonical `templates/STARTUP_CARD_RENDER.py`，并把 renderer 已通过反向校验的输出原样作为正式启动卡；不得在这里或聊天中手写、拆分、增补另一套字段/launcher 形式。Task/route/client/placement 等语义仍由各自 canonical owner 解释。

若 exact Task 不可读、必要引用缺失、exact ref 漂移或 Task 自相矛盾，执行端必须返回 `BLOCKED` / `RECONCILIATION_REQUIRED`，不得凭 launcher 或聊天上下文猜测补齐。
