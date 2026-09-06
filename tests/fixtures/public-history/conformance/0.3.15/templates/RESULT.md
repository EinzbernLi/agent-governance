# Worker / Validator Result

## Metadata

```yaml
task_id: "PROJECT-000"
task_ref: ""        # exact durable Task revision/comment/ref when applicable
result_sink: ""     # canonical durable sink
status: worker_complete|validator_complete|blocked

execution:
  assigned_role: null
  assigned_model: null
  dispatch_route: current_session|native_dispatch|external_owner_launch
  internal_delegation_allowed: false
  internal_delegation_used: false
  runtime_capability_evidence_ref: null  # optional; normally omitted

parallelism:
  mode: serial|parallel_safe
  workstream_id: null
  baseline_ref: null
  conflict_or_dependency_drift: false
  candidate_currency: current|stale|not_applicable
  reusable_payload: false

input_boundary:
  independence_required: false
  isolation_mode: null
  ambient_control_context_present: false
  authorized_substantive_evidence_only: true
  contamination: false

branch: ""
commit_or_artifact_ref: ""
pr: ""

durable_handoff:
  result_written_to_canonical_sink: false
  result_read_back_verified: false
  published_ref_required: false
  published_ref_matches_remote: null
```

## 1. Actual Work

- 

## 2. Files Changed / Artifacts

- 

## 3. Tests / Validation

| Check | Result | Evidence |
|---|---|---|
| | | |

## 4. Acceptance Criteria

- [ ] 

## 5. Deviations / Risks

- None / 

For `parallel_safe` work, explicitly report any write-scope overlap, sibling dependency drift, baseline invalidation, rebase requirement or integration-order assumption. Do not silently widen scope to follow sibling changes.

If integration/head advanced after candidate freeze, report candidate currency separately from local payload validity. A stale candidate cannot be accepted as current, but `reusable_payload: true` is allowed only when the Task/Lead can prove the relevant factual/schema/materialization/ignore contract did not change.

If an executor-local plan added a conservative stop condition that is not present in the durable Task, identify it as local conservatism. Do not report it as a Task Gate.

## 6. Scope / Safety Compliance

- unauthorized changes: no / yes
- forbidden boundary touched: no / yes
- permission expansion: no / yes
- unauthorized nested delegation: no / yes
- unauthorized cross-platform delegation: no / yes
- project Lead Claim touched by executor: no / yes
- sibling write scope touched: no / yes

## Evidence Rules

Normal Result keeps dispatch evidence compact:

```text
assigned executor + actual route + result/tests + scope/evidence compliance
```

Do not repeat the full Task contract. Do not enumerate hidden internal model/reasoning chains.

`runtime_capability_evidence_ref` is optional and normally omitted; include it only for dispatch failure, capability drift, strong audit, or model/runtime experiments.

Independent tasks distinguish Ambient Control Context from substantive evidence. Pure system/developer/AGENTS/WORKFLOW/tool/safety control reads do not by themselves create contamination.

Parallel workstream metadata is execution evidence only. It does not create a lock, Lead Claim, or second Task authority.

## Durable Handoff Rules

客户端 UI、本地 agent loop、local planning 文件显示“完成”都不是 durable Task completion authority。

在正常 repository-backed Task 中，executor 在结束前必须：

1. 把 required terminal Result 写入 `result_sink`；
2. read-back 验证 `task_ref`/required marker/body；
3. 若 Task 预期 branch/PR/artifact mutation，验证 `commit_or_artifact_ref`/PR head 与 remote observed ref 一致。

只有这些条件满足，`durable_handoff.result_*` 才能标为 true。无法写回时应明确报告 `INCOMPLETE_HANDOFF`/result-sink failure，而不是让 UI completion 代替 GitHub Result。

## Minimal BLOCKED Result

```yaml
status: blocked
task_id: <task-id>
task_ref: <exact-task-ref>
result_sink: <canonical-sink>
reason_code: <code>
evidence: <minimal-basis>
substantive_work_performed: false
project_resources_mutated: false
durable_handoff:
  result_written_to_canonical_sink: true
  result_read_back_verified: true
```

> Worker / Validator Result is evidence. Only Lead Controller may integrate sibling work and finally accept the Task.
