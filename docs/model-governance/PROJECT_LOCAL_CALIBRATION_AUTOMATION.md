# Project-local Calibration Automation

版本：0.3.13  
状态：Accepted

## 1. Goal

把已经存在于项目 durable facts 中的 Task / Result / Validator / CI / Lead Acceptance 事实，自动转换为项目本地 Model Routing prior，避免人工逐 Task 给模型打分。

该机制只生成**派生缓存**：

```text
Durable governed facts = evidence authority
Project-local calibration Issue = rebuildable routing prior cache
```

删除 calibration Issue 不会删除任何权威 evidence，也不改变 Task/Result/Acceptance 历史。

## 2. Components

中央模板：

```text
templates/PROJECT_CALIBRATION_OUTCOME.json
templates/PROJECT_CALIBRATION_EXTRACTOR.py
templates/PROJECT_CALIBRATION_UPDATE.yml
```

首次 informed adoption 只有在 Owner 选择启用 project-local calibration 且项目策略/平台能力允许时才部署：

```text
.agent/tools/project-calibration.py
.github/workflows/project-calibration.yml
```

选择关闭时不安装该 automation；Model Routing 使用 governance/global prior，不影响 Task/Result/Acceptance authority。

Workflow 维护 exactly one local Issue：

```text
[PROJECT-LOCAL-CALIBRATION] Derived model routing prior
```

Issue body marker：

```text
[PROJECT-LOCAL-CALIBRATION-STATE-v1]
```

## 3. Normalized Terminal Outcome

Terminal Lead Acceptance 在能够形成可审计事实时附加 marker：

`[PROJECT-CALIBRATION-OUTCOME-v1]`

紧随其后放置一个 JSON code block，内容遵循 `templates/PROJECT_CALIBRATION_OUTCOME.json`，例如：

```json
{
  "schema_version": "1.0",
  "task_ref": "github:owner/repo#123@task-revision",
  "revision": 1,
  "terminal": true,
  "task_class": "bounded_code_edit",
  "risk_level": "medium",
  "samples": []
}
```

这不是额外评分步骤。AI/Lead 应从已经读取的 durable Task、Worker Result、Validator Result/Review、PR/CI 与最终 Acceptance 结论生成该 JSON。

### Required event fields

```text
schema_version
task_ref
revision
terminal=true
task_class
risk_level
accepted_at
samples[]
```

每个 sample 只代表一个 formal execution role。Worker 与 Validator 必须是不同 sample，不得把两个角色合并成同一表现分数。

## 4. Worker sample

直接模型归因时至少记录：

```text
role = bounded_worker
attribution = assigned_executor
model_id
model_semantic_key
reasoning_semantic_key
rework_count
execution.dispatch_route
execution.runtime_profile
worker_outcome.accepted_first_pass
worker_outcome.final_accepted
worker_outcome.tests_passed
worker_outcome.scope_violation
worker_outcome.permission_violation
worker_outcome.safety_violation
```

`tests_passed` 在 Task 无测试或 durable facts 无法确定时允许 `null`；未知不得猜测。

## 5. Validator sample

至少记录：

```text
role = validator
attribution = assigned_executor
model_id
model_semantic_key
reasoning_semantic_key
execution.dispatch_route
execution.runtime_profile
validator_outcome.review_completed
validator_outcome.material_findings_confirmed
validator_outcome.false_positive_confirmed
validator_outcome.missed_defect_confirmed
```

`false_positive_confirmed` / `missed_defect_confirmed` 只有后续 durable evidence 足以确认时才填整数；否则保持 `null`。没有发现缺陷并不自动等于 Validator 表现差。

## 6. Semantic keys

Calibration 不用 UI display name 作为稳定身份。

推荐：

```text
model_semantic_key = <model-id>@<material model semantic revision>
reasoning_semantic_key = <model-id>:<reasoning profile/native semantics>@<revision>
```

如果平台无法提供稳定精确 revision，Lead 必须使用一个明确的 bounded semantic key，例如当前治理可确认的模型/档位语义版本；之后 material semantics 改变时创建新 key，不得覆盖旧 key。

旧 key 可以作为历史弱 prior，但不能与新 key 直接混合成当前 evidence。

## 7. Material internal delegation

如果 assigned executor 使用 material internal children，且无法可靠知道各 child 对结果的贡献：

```json
{
  "attribution": "execution_strategy",
  "strategy_key": "<bounded-strategy-key>"
}
```

该 sample 进入 `strategy_groups`，不进入 direct `model_groups`。

不可观察 child 的工作不得默认归功或归咎给入口模型。

## 8. Aggregation

Extractor 按以下 key 分组 direct model evidence：

```text
role
+ task_class
+ risk_level
+ model_semantic_key
+ reasoning_semantic_key
```

并分别输出 Worker / Validator metrics。

Worker 典型 metrics：

```text
sample_count / effective_sample_count
accepted_first_pass_rate
final_accepted_rate
mean_rework_count
tests_passed_rate
any_violation_rate
```

Validator 典型 metrics：

```text
sample_count / effective_sample_count
review_completed_rate
material_findings_confirmed
false_positive_confirmed
missed_defect_confirmed
```

近期 evidence 采用时间衰减，默认 half-life 90 days。该值是 project-local aggregation policy，可在 workflow env 中调整；调整不改写历史事实。

Extractor 只提供 evidence-strength band：

```text
insufficient
developing
established
```

它不生成跨角色、跨任务类的单一 global model score。

## 9. Duplicate / Rework semantics

同一 `task_ref` 可出现修订后的 terminal outcome：

```text
revision: 1
revision: 2
```

Extractor 只使用最高 revision；同 revision 再以最新 comment id 为准。

因此修正 machine-readable normalization 不需要删除旧 comment，也不会重复计样本。

`final_accepted=true` 与 `accepted_first_pass=false + rework_count>0` 必须同时保留。最终 PASS 不会擦除 rework evidence。

## 10. Trigger / Rebuild

Workflow 支持：

```text
issue_comment created/edited containing outcome marker
issue closed
workflow_dispatch
bounded daily schedule
```

事件触发时 extractor 仍会从 durable comments 重建 aggregate，而不是信任上一份 cache 作为 authority。

GitHub Search 最多按当前模板处理 1000 个 matching Issue/PR。若 total 超限、Search 返回 incomplete、或出现 malformed terminal outcome：

```text
usable_for_routing: false
```

不得悄悄用 partial scan 作为当前 prior。

需要超过该 bound 的大型项目应在未来扩展 sharded/checkpoint scan；在扩展被验收前保持 fail closed。

## 11. Local policy

`LOCAL_POLICY.model_calibration` 可控制：

```yaml
model_calibration:
  enabled: true
  automatic_outcome_extraction: true
  upstream_export: false
  automatic_upstream_delivery: false
```

`enabled` 和 `upstream_export` 是首次 informed adoption 中两个独立选择：本地学习可以开启而上游分享保持关闭。`upstream_export=true` 只允许明确准备/提交匿名 aggregate；`automatic_upstream_delivery` 在 ordinary Core 中保持 false。

Workflow 已被安装但 local policy 显式 `enabled: false` 时，state Issue 保留但标记不可用于 routing。

以下任一项优先于启用建议：

- Owner 在首次/后续配置中选择关闭；
- 项目禁止 GitHub Actions；
- 项目更严格 local policy；
- 当前平台无法满足 workflow 权限。

## 12. Permissions / Privacy

Workflow 最小权限：

```yaml
permissions:
  contents: read
  issues: write
```

它使用 downstream repository 自己的 `github.token`。

明确禁止：

```text
write repository contents
write governance upstream
send project/task/model facts upstream
adopter registration
required usage telemetry
required token/cost collection
central DB / hosted daemon
```

完整 raw calibration outcome、Task/Issue/PR/SHA、project/repository identity、local path、business/personal facts 和 LPRL/project state 都留在 downstream。Latency/cost 只有 durable facts 本来已经以 coarse bucket 可用时才可加入本地 sample；不存在时保持 `null`。

## 13. Routing consumption

Model Routing 只在：

```text
state marker/schema valid
+ scan.complete = true
+ usable_for_routing = true
```

时读取 project-local calibration。

它只能：

- 在 already-qualified/suitable candidates 间提供 project-local prior；
- 为 reasoning choice 提供 recent comparable evidence；
- 提醒 Lead 关注 rework/violation/validator-quality 历史。

它不能：

- 自动把未 qualified model 变为 production qualified；
- 绕过 Task override / safety / capability / independence；
- 改写 Execution Economy；
- 自动改变中央 `CALIBRATION_SNAPSHOT.yaml`。

State 不可用时：

```text
ignore local cache
-> Governance Calibration Snapshot
-> Bootstrap Seed
```

## 14. Optional upstream feedback

`templates/PROJECT_ROUTING_FEEDBACK.yaml` 只用于 Owner/治理维护者**明确 opt-in** 的匿名化 aggregate export。

Local calibration workflow 不调用该 export，不把 state Issue 发往上游，也不因 governance update discovery 触发 feedback。Export 只能由 downstream 侧先聚合/去身份：不得包含 raw samples、project/repository/Task/Issue/PR/SHA/path/business/personal facts，也不得创建 stable adopter pseudonym/hash 作为中央 source identity。

匿名 aggregate 没有稳定项目身份时，不得被中央当作 `min_distinct_project_sources` 的 machine proof；它可以作为补充 evidence，但不能单独 auto-promote/auto-demote global qualification/default。

## 15. Acceptance invariant

```text
facts first
normalization second
local derived cache third
routing prior fourth
Lead final authority always remains outside the cache
```

如果无法从 durable evidence 确定某字段，写 `null` / omit according to schema；不要为了填满 calibration sample 猜测事实。
