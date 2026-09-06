# Task Package

## Metadata

```yaml
task_id: "PROJECT-000"
title: ""
status: draft
risk_level: low
created_by_role: lead_controller
baseline_ref: null # parallel_safe 时必须是 exact frozen ref

executor:
  role: bounded_worker
  target_platform: null
  model: null
  reasoning: null

dispatch:
  mode: auto
  internal_delegation_allowed: false

parallelism:
  mode: serial # serial|parallel_safe
  workstream_id: null
  sibling_task_refs: []

independence:
  required: false
  substantive_evidence_isolation: null  # exact_resource|frozen_bundle|bounded_context|native_isolated_context
  ambient_control_context_allowed: true

transport:
  task: repository_ref
  result: repository_ref

preflight_recording: inline_final
review_requirement: lead_controller
result_location: ""  # canonical durable result sink
```

## 1. Objective

完成后必须产生什么结果。

## 2. Background

只写完成本任务所需背景，不复制完整项目历史。

## 3. Scope

- 

## 4. Non-goals

- 

## 5. Files / Evidence Allowed / Forbidden

Authorized substantive evidence:
- 

Allowed write files / paths:
- 

Forbidden write files / paths:
- 

Forbidden substantive evidence:
- 

Ambient control context allowed:
- system/developer/platform instructions
- repository AGENTS.md / WORKFLOW.md when used only as execution/process/safety controls

## 6. Dependencies

- 

## 7. Parallel Workstream

默认：

```yaml
parallelism:
  mode: serial
  workstream_id: null
  sibling_task_refs: []
```

只有 Active Lead 可以将本 Task 标记为 `parallel_safe`。若为 `parallel_safe`，本 Task 必须同时满足：

- `baseline_ref` 为 exact frozen ref；
- sibling Task refs 已列出；
- 本节第 5 部分的**实质项目 write scope** 与 sibling Task 两两不重叠；
- dependencies 不要求与 sibling 串行；
- 实现类 Task 使用独立 branch/PR、worktree 或等价隔离写入表面；
- 不写共享 mutable runtime/state/schema migration；
- executor 不创建/修改项目 Lead Claim，不集成 sibling work，不宣布最终 accepted。

读取相同 source/evidence 可以并行；多个 Task 也可以在同一 GitHub Issue 追加可明确归属的 Result comment。写同一项目文件默认不能并行。

若发现 overlap、dependency drift 或 sibling merge 使本 Task baseline assumptions 失效，停止扩大修改范围并写回 deviation，等待 Lead 决定 `rebase/replan/serialise`。

若 drift 只使 tracked candidate 不再 current，而已经生成的本地 payload/evidence 与 factual/schema/materialization/ignore contract 均未变化，允许 Result 标记它为 reusable；**不得**把 stale candidate 当 current-head accepted。由 Lead 冻结新的 reconcile/revalidation，而不是默认重做全部本地 materialization。

## 8. Acceptance Criteria

- [ ] 

## 9. Tests

```text
command:
expected:
known_allowed_failures:
```

## 10. Dispatch Rules

`executor` 是 Lead/Model Routing 已做出的正式执行分配；`dispatch.mode: auto` 表示当前 Active Lead 根据本会话 Runtime Capability Probe 自动选择：

```text
current_session | native_dispatch | external_owner_launch | blocked
```

Task 不把 Web/Codex 写死成某种 dispatch mode。Web 会话也可以是 bounded Worker；平台名称不授予 Lead 身份。

若走 `external_owner_launch`，Owner 新开 Task 指定的平台/模型/reasoning 会话，并只发送：

```text
执行 <task_ref>；已按启动卡启动；作为该 Task 的执行者，不接管项目 Lead。
```

若走 `native_dispatch`，Active Lead 直接向 child 发送：

```text
执行 <task_ref>；作为该 Task 的执行者，不接管项目 Lead。
```

两者都从 GitHub 读取完整 Task，并直接把 Result 写回 result sink。

Task/Result transport 默认 `repository_ref`；只有事实源在目标执行端不可达时，才允许显式降级到 `manual_content`。Owner 手动启动客户端不等于手工搬运 Task/Result 内容。

## 11. Nested Delegation

```yaml
internal_delegation_allowed: false
```

约束的是**被分配的执行会话**不能自行继续创建额外子代理；不限制 Active Lead 为不同正式 Task 创建 native child。

只有 Task 明确设置 `true` 时，执行会话才可在本 Task scope 内做平台内部临时 delegation。不得扩张 scope、权限、forbidden boundary、evidence boundary 或 result sink，也不得未经 Lead 重新路由跨平台。

## 12. Independence / Context

独立性约束 substantive evidence，不要求平台绝对零 ambient control reads。

未经授权的旧结果、旧分析、额外项目事实或 timeline 属于污染；纯 system/developer/AGENTS/WORKFLOW/tool/safety 控制内容本身不是 substantive evidence。

Runtime-local planning、memory、session restore、IDE state、checkpoint 和 scratch 只是 execution aid，不是 Task/Lead authority。若执行会话在 durable re-anchor 前恢复了 local context，只能读取非权威上下文、repository/GitHub durable facts 和 runtime capabilities，并运行已知 no-write/隔离/offline 的 bounded diagnostics；不得进行 authority-bearing Task work、dispatch、source/ref/config/data/state mutation 或 network/platform/business action。此类 diagnostic evidence 必须标为 provisional。

Durable re-anchor 后，只有 exact input/baseline 与 evidence/test contract 未变化且已完成 reconcile/revalidation，才可复用 provisional evidence；发生 drift 必须 rerun。没有可验证的 durable activation completion 时，不得把 local/UI/planning 完成当成 `ACTIVE`、Task PASS 或 acceptance。

## 13. Constraints

- 不得扩大 scope 或弱化 acceptance/tests。
- 不得越过 forbidden/permission boundary。
- 不得接管项目 Lead 或修改 Lead Claim sink。
- `parallel_safe` Task 不得写 sibling Task 的实质项目 write scope。
- 不得把 Owner 变成 Task/Result 内容中转者。
- 只有 Lead Controller 可以集成 sibling work 并最终 accepted。
- Durable Task 正文/最新授权 comment 是 substantive contract；executor-local planning 只是 execution aid。
- local plan 可以为安全保守停止，但不得新增 durable Gate、不得把本地条件冒充 Task requirement。
- local plan、恢复上下文或 provisional diagnostic 不得覆盖最新 durable Task/Lead facts；适用的 durable re-anchor/activation 未完成时，必须保持 fail-closed。

## 14. Expected Result

使用 `RESULT.md`。记录实际 dispatch route、实际工作、tests、scope/evidence compliance 和必要的异常信息；若为 `parallel_safe`，额外记录 `workstream_id`、`baseline_ref`、candidate currency/reusable payload（适用时）以及是否发生 conflict/dependency drift。若使用 pre-anchor provisional diagnostic，记录 exact input/baseline、evidence/test contract、reconcile/revalidation 和 reuse/rerun 结论；正常路径不重复完整控制面。

即使结果是 BLOCKED / REVISE_REQUIRED、或 preflight 在 substantive mutation 前停止，只要 Task 要求 durable Result，就必须写入 `result_location`。

Executor 只有在 Result 已写入 canonical sink，并能 read-back 确认 Task ref/revision + required marker/body 后，才可声称 durable handoff 完成。若 Task 要求 branch/PR/artifact mutation，还必须确认 Result 中 exact published ref 与 remote observed ref 一致。

```text
local/UI done != durable Task done
missing durable Result = INCOMPLETE_HANDOFF
```
