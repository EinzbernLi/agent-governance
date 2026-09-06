# Context Checkpoint

> Checkpoint 是经过 Lead Controller 确认的**时点状态摘要**，用于恢复项目上下文；它不是锁、不是 Lead authority，也不是永远优先于后续 durable facts 的数据库快照。

## Metadata

```yaml
checkpoint_id: "CP-YYYY-MM-DD-00"
created_at: ""
created_by_role: lead_controller
project_phase: ""
code_ref: ""
active_task_ref: ""
latest_result_ref: ""
latest_acceptance_ref: ""
```

## 1. 当前架构状态

- 

## 2. 已稳定完成

- 

## 3. 当前活跃任务

- 

## 4. 当前阻塞项

- 无 / 

## 5. 下一步

- 

## 6. Do Not Change / 当前不可擅自改变

- 

## 7. Known Risks / 已知风险

- 

## 8. 相关 ADR / Contract / Schema

- 

## 9. Recovery / Reconciliation Rule

新会话应把本 checkpoint 视为“该时点经过 Lead Controller 确认的项目状态摘要”，但恢复时必须与以下较新的 durable facts 对账：

```text
latest PROJECT_STATE
active Task
latest Result / Lead Acceptance
current branch / commit / PR / CI state
```

若 checkpoint 之后已有新的 durable facts，则：

```text
checkpoint + newer durable facts = effective resume state
```

不得因 checkpoint 较旧而回退已经完成/验收的工作，也不得把 checkpoint 当作控制权锁。

## 10. Lead Control Note

当前谁有权继续正式派发/项目修改由独立的 Lead Claim generation（若项目启用）表达，而不是由 checkpoint 表达。

自然语言“接管 <project>，继续”可以自动找到本 checkpoint；Owner 不需要手工复制 checkpoint ID。
