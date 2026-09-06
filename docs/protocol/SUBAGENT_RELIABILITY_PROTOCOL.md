# Subagent Reliability Principles

版本：0.3.16
状态：Non-authoritative principles appendix

普通任务的流程 authority：

- coordination/roles: `AGENT_COORDINATION_PROTOCOL.md`
- dispatch: `DISPATCH_ROUTING_PROTOCOL.md`
- task contract: `TASK_PACKAGE_SPEC.md` / `templates/TASK.md`
- final acceptance: `LEAD_CONTROLLER_ACCEPTANCE_PROTOCOL.md`

This is a non-authoritative principles appendix. It does not own dispatch,
delegated lifecycle, observation, coordination, Task, Result, validation or
acceptance semantics; the canonical surfaces above control.

## Principles

```text
one active Lead Controller
probe current runtime before routing
prefer native dispatch when assigned executor is actually reachable
otherwise use GitHub + Owner Activation Relay
Owner relays activation, not Task/Result content
Lead native dispatch is not Worker nested delegation
role-stable Worker/Validator session reuse is normal after durable re-anchor
fresh session is required only by the Task/evidence contract
Codex Worker internal children are default-allowed when capability is proven; Web/generic default false
internal child review is not independent validation
independence isolates substantive evidence
ambient control context is not automatically contamination
ordinary tasks do not depend on hidden model-identity metadata
fail closed only on decision-relevant scope/evidence/permission/safety failures
record minimal sufficient evidence on normal PASS
Lead Controller owns final acceptance
```

## Session reuse and bounded internal delegation

正式 Task 默认不要求 fresh conversation。完成 durable re-anchor 后，角色稳定的 Worker/Validator session 可以继续使用；Lead 或 Owner 只在有帮助时给出 `reuse_existing`、`recommend_new` 或 `must_be_fresh` 短建议。只有 Task/evidence contract 明确要求 fresh-session 或 identity isolation 时，fresh 才是硬要求。

Codex Worker may optionally use qualified native children for a bounded
independently understandable subproblem when quota preservation,
specialization, context isolation or elapsed time is materially beneficial.
Web/generic Worker remains default false. Parent scope, permission, evidence,
write ownership, integration and terminal Result accountability remain intact;
parallel child writes are disjoint, overlap serializes/fails, child review is not
independent validation, and child recursion remains default false.

Delegated lifecycle and observation are not repeated here; load
`config/DISPATCH_POLICY.yaml` when a delegated Task is triggered.

`BLOCKED` / `NEEDS_ATTENTION` 仅适用于缺少必要 authority、permission、fact、decision 或 capability 且没有安全的 in-scope alternative；普通搜索、首试失败、命令适配或 bounded debugging 不构成 blocker。若 Validator 被 material substantive mid-flight observation/steering 改变 evidence boundary，该运行失去 independent-validation credit，需要时取得 fresh substantively independent validation。

Executor self-check 可以作为执行证据，但不等于治理级 independent review。正式 independent validation 需要 substantively independent 的 Validator；除非 freshness 属于 Task contract，否则不要求新建 conversation。不同 child 身份本身不产生独立验证资格。

## Anti-patterns

- 根据 `Web/Codex/Desktop` 名称写死 dispatch；
- 为每个 Task 重复创建 capability artifact；
- 同时维护 GitHub Issue Task 与 `.agent/tasks/` 镜像作为双 authority；
- 让 Worker 在 Lead 已经分好正式 Worker/Validator Task 后再次重做模型路由；
- 因客户端不暴露内部 exact model/reasoning 而阻断普通工程任务；
- 把普通 Task 的 session reuse 误当作必须新建 conversation；
- 把 Worker internal child 当成 Lead、正式 Task 或 independent Validator；
- 为追求审计完整度复制 Task/Handoff/Result 相同字段。

> Reliable governance should remove predictable failure modes, not create new ones.
