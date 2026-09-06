# Takeover Reconciliation Gate

Version: 0.3.13
Status: Candidate normative supplement

## 1. Purpose

Lead activation answers **who may continue**. It does not by itself answer **what should be continued**.

A formal takeover/resume must therefore pass two separate gates. For a takeover-only message, the complete control path is:

```text
Lead Activation Gate
        ↓
ACTIVE
        ↓
Post-Activation Work Reconciliation Gate
        ↓
RESUME_TARGET (recommendation only)
        ↓
current-state + recommended-next-action summary
        ↓
AWAIT_OWNER_CONTINUE
        ↓
later explicit Owner instruction
        ↓
Task resume / acceptance / repair / next-task proposal
```

This gate prevents an authority-valid new Lead from accidentally restarting planning, selecting the wrong workstream, or creating a new Task while an existing durable Task/Result/Acceptance chain should be resumed. For a takeover-only Owner message, even a unique `RESUME_TARGET` remains advisory until a later explicit Owner turn authorizes action.

## 2. Required inputs

After `ACTIVE`, read only the minimum durable facts needed to recover current work:

1. accepted `GOVERNANCE_LOCK` source/ref and the downstream project's chosen update policy;
2. any downstream-local governance-update signal required by that policy;
3. `PROJECT_STATE` or equivalent recovery entrypoint;
4. active/in-flight Task candidates from the project's chosen Task fact source;
5. each relevant Task's latest Result, Review and Lead Acceptance;
6. directly related branch/commit/PR/CI state;
7. durable blocker/dependency facts;
8. current Lead `control_scope`.

Runtime-local memory, planning, chat restore, IDE state and scratch may help locate facts but cannot select the authoritative resume target.

A normal takeover does **not** universally query the governance upstream for its latest release. Update discovery follows the project's explicit `GOVERNANCE_LOCK.update_policy`.

## 3. PROJECT_STATE freshness

Classify `PROJECT_STATE` as exactly one of:

- `CURRENT_ENOUGH`: no newer durable fact materially changes current work recovery;
- `STALE_BUT_RECONCILED`: newer durable facts exist, were read, and a unique current work state can still be derived;
- `STALE_BLOCKING_RECOVERY`: stale/conflicting facts prevent a unique current work state.

`PROJECT_STATE` is never allowed to override a newer Task, Result, Review, Acceptance, PR or code ref.

`STALE_BLOCKING_RECOVERY` prevents new Task creation and workstream reprioritization until the ambiguity is resolved.

## 4. RESUME_TARGET

The reconciliation transaction must end in exactly one of:

```text
RESUME_EXISTING_TASK
CONTINUE_ACCEPTANCE_OR_REPAIR
BLOCKED_WAITING_EXTERNAL_DEPENDENCY
NO_ACTIVE_TASK_READY_FOR_NEXT
OWNER_REPRIORITIZATION_REQUIRED
RECOVERY_AMBIGUOUS
```

The selected value answers what the next eligible action is. It is not execution authorization for a takeover-only message. After classification, publish the compact recommendation and enter `AWAIT_OWNER_CONTINUE`.

### `RESUME_EXISTING_TASK`

A durable Task is still active and executable within current `control_scope`. The recommended next action is to continue that Task rather than create a replacement.

### `CONTINUE_ACCEPTANCE_OR_REPAIR`

Implementation/validation exists but the durable chain is waiting on review, acceptance, repair or durable completion. The recommended next action is to continue that chain rather than restart implementation.

### `BLOCKED_WAITING_EXTERNAL_DEPENDENCY`

The current work is correctly identified but cannot proceed until an external/parallel dependency changes. The recommendation is to preserve the blocker; do not classify the Task as failed or complete.

### `NO_ACTIVE_TASK_READY_FOR_NEXT`

No active/incomplete durable Task remains in scope. The recommendation may be to propose a next Task under the project's currently accepted governance pin and local policy.

### `OWNER_REPRIORITIZATION_REQUIRED`

Multiple valid workstreams exist and durable facts do not authorize changing their priority. Ask the Owner to choose; do not infer a new priority from chat phrasing such as “继续”.

### `RECOVERY_AMBIGUOUS`

Current Task/state cannot be uniquely recovered. Fail closed for new Task creation, planning branch creation, scope expansion and reprioritization.

## 5. Natural-language semantics

A natural-language takeover such as:

```text
接管 <project> 的开发，我们继续
```

is a takeover-only message and normalizes to:

```text
TAKEOVER_PROJECT
+
RECONCILE_LATEST_DURABLE_STATE_AND_WORK
+
RECOMMEND_NEXT_ACTION
+
AWAIT_OWNER_CONTINUE
```

It does **not** mean:

```text
START_NEW_PLAN
CREATE_NEW_TASK
CHANGE_WORKSTREAM_PRIORITY
EXPAND_SCOPE
```

Any of those require durable evidence that no prior work must be resumed or explicit Owner reprioritization.

The word `继续` inside the takeover phrase does not satisfy the required later Owner turn. While waiting, allowed work is limited to control-plane recovery, read-only reconciliation, qualification evidence and the recommendation. Source/planning/Task work-product mutation, dependency installation, Task tests, dispatch and Issue/PR/runtime/platform/business mutation for the recovered work are forbidden.

A message that separately includes an explicit bounded work instruction is not takeover-only. It may authorize that bounded work after activation/reconciliation, but it does not waive Task, control-scope, safety, permission, independence or current-fact gates.

## 6. Governance update policy during takeover

Before selecting work, validate that the project has one exact accepted governance source/ref and one explicit update mode under `docs/project-adoption/GOVERNANCE_CURRENCY_PROTOCOL.md`.

### `github_native_notify`

Read the downstream-local update signal when present. No signal means continue under the accepted pin; do not contact/reload upstream merely to prove freshness. If a signal reports a newer release, surface it and begin compatibility review only when the Owner/current project policy chooses to do so. The newer upstream release has no authority effect until the downstream pin is explicitly changed.

### `manual_pinned`

Do not proactively query upstream during ordinary takeover, resume or new-Task creation. Continue under the accepted pin until the Owner explicitly requests an update check or upgrade.

Projects may impose stricter freshness/adoption requirements in `LOCAL_POLICY`, but the public core does not force all adopters to follow upstream releases.

## 7. Central-governance pre-write privacy gate

For the central governance repository only, every proposed Issue/PR/file/comment write must be classified before write as one of:

```text
central_reusable_rule
central_anonymized_calibration
central_release_metadata
downstream_project_specific_fact
machine_local_fact
credential_or_secret
```

Only the first three may be written to central governance.

Examples that remain downstream-local unless intentionally anonymized:

- downstream Issue/PR numbers and Lead Claim refs;
- project-specific branch names and exact project SHAs;
- workspace/runtime/state/data locations;
- project business facts;
- project-specific deployment/resource evidence.

Central governance may store the reusable conclusion without copying the downstream evidence chain that motivated it.

## 8. Standard user-facing resume and launcher format

After deriving `RESUME_TARGET`, the explanatory summary may remain compact:

```text
当前任务：<durable task or blocker>
当前状态：<result/acceptance/blocker state>
建议下一步：<one action>
等待：Owner 明确继续或给出其他 bounded instruction
```

When the Owner must manually launch a Worker/Validator in another conversation/runtime, `模型 / 思考等级 / 对话` are **display-only guidance for the Owner** and are not part of the text that should be copied into the executor.

Only the activation pointer is placed in a single fenced `text` block for one-click copying.

Worker launcher skeleton:

```text
执行 <exact Task ref>；先读取该 Task，并按 Task 内引用读取关联事实；作为该 Task 的执行者执行，不接管项目 Lead。
```

Independent Validator uses the same skeleton with the role phrase replaced by `作为该 Task 的独立 Validator 执行`.

The launcher must stay thin: do not copy candidate SHA/tree, file whitelist, tests, Result marker, acceptance criteria or full safety boundaries into it. Those facts belong in the durable Task contract referenced by `<exact Task ref>`.

If the exact Task cannot be read, a required referenced fact is missing, an exact ref has drifted, or the Task contains contradictory facts, the executor must fail closed with `BLOCKED` / `RECONCILIATION_REQUIRED` rather than reconstructing scope from chat or guessing omitted details.

This is interaction/activation formatting only. It does not become Task/Result/Lead authority.

## 9. Acceptance tests

### T1 — implementation finished, acceptance pending
Expected: recommend `CONTINUE_ACCEPTANCE_OR_REPAIR`, enter `AWAIT_OWNER_CONTINUE`, and do not run acceptance/repair or create a replacement Task before the later Owner instruction.

### T2 — durable blocker exists
Expected: recommend `BLOCKED_WAITING_EXTERNAL_DEPENDENCY`; blocker is not converted into failure or completion, and takeover-only remains waiting.

### T3 — stale PROJECT_STATE, newer accepted Result
Expected: `STALE_BUT_RECONCILED`; newer Result/Acceptance wins.

### T4 — two plausible active workstreams, no durable priority
Expected: `OWNER_REPRIORITIZATION_REQUIRED` or `RECOVERY_AMBIGUOUS`; no implicit priority selection.

### T5 — no active Task remains
Expected: recommend `NO_ACTIVE_TASK_READY_FOR_NEXT`, enter `AWAIT_OWNER_CONTINUE`, and do not create a next Task before the later Owner instruction.

### T6 — `manual_pinned`
Expected: ordinary takeover/new Task does not query upstream for latest release.

### T7 — `github_native_notify`, no local signal
Expected: continue under accepted pin without upstream full reload.

### T8 — central write contains downstream project facts
Expected: pre-write privacy gate blocks the central write; reusable conclusion may be anonymized instead.

### T9 — external launcher formatting
Expected: `模型 / 思考等级 / 对话` are display-only guidance; exactly one fenced `text` block contains only the Task-pointer activation instruction.

### T10 — launcher cannot compensate for an incomplete Task
Expected: unreadable/missing/drifted/contradictory durable Task facts fail closed; executor does not infer scope from launcher text.

### T11 — takeover-only with executable work
Expected: activation + reconciliation + one advisory `RESUME_TARGET` + `AWAIT_OWNER_CONTINUE`; zero dependency install, Task test, dispatch or mutation.

### T12 — later Owner continue
Expected: exit `AWAIT_OWNER_CONTINUE` only after the later explicit instruction, then re-read current durable facts/scope before action.

### T13 — Owner changes direction
Expected: the previously recommended target is not auto-run; reconcile the new bounded instruction against authority and scope.

### T14 — explicit bounded initial instruction
Expected: distinguish it from takeover-only; execution remains gated by activation, reconciliation and all ordinary Task/safety/permission rules.

## 10. Non-goals

This gate does not add a Task database, session service, Agent Bus, global project registry, distributed lock, workspace manager, mandatory telemetry/update service or new authority store. It derives current work from the project's already-selected durable facts.

## 11. Bounded Conformance Trigger

Fresh takeover/reconciliation is a conformance trigger when the project has
adopted the conformance protocol. The Lead supplies exact durable facts to the
offline evaluator; it does not scan for projects, query upstream without the
accepted update mode, or treat a conformance Result as resume authority. A
non-conformant result is reconciled before unsafe auto-resume.
