# Private Evidence Hub

版本：1.0  
状态：Candidate contract for ordinary governance 0.3.23

## 1. Purpose

Private Evidence Hub（PEH）是用户在**自己的私人 Governance fork / mirror** 中可选启用的跨项目模型证据组件。它不是第三个 public product module；公开产品模块仍然只有 Core Governance 与 optional LPRL。

PEH 只解决一个问题：

> 在用户自己的信任边界内，把多个已治理项目的 project-local model calibration 汇总成 private cross-project routing prior，从而让未来任务在已经 qualified / suitable 的候选模型与 reasoning 之间排序得更贴合该用户自己的真实历史。

PEH 不管理 Task、Result、Validator、CI、Lead Acceptance、项目 pin、LPRL state、源码或部署。

## 2. Same-repository Issue surface

PEH 不要求第二个仓库、数据库或 hosted service。私人部署只使用同一个 private Governance repository 的 Issues：

```text
[PRIVATE-EVIDENCE-HUB] Sources
[PRIVATE-CROSS-PROJECT-CALIBRATION] Derived routing prior
```

Config marker：

```text
[PRIVATE-EVIDENCE-HUB-CONFIG-v1]
```

Derived-state marker：

```text
[PRIVATE-CROSS-PROJECT-CALIBRATION-STATE-v1]
```

Config Issue 的 machine-readable JSON 最小字段：

```json
{
  "schema_version": "1.0",
  "enabled": true,
  "source_repositories": [
    "owner/project-a",
    "owner/project-b"
  ]
}
```

`source_repositories` 是 Owner 在自己私人信任边界内明确授权参与汇总的 exact repositories。Private source identity 可以在该 private fork 内保留，用于审计和真实 distinct-project proof；不得自动导出到 official public Governance。

## 3. Source facts remain authoritative

PEH 不复制项目 authority。

```text
Project Task / Result / Validator / CI / Lead Acceptance
        ↓
project-local normalized outcomes
        ↓
[PROJECT-LOCAL-CALIBRATION] derived state
        ↓ read/aggregate only
Private Evidence Hub
```

每个 source project 的 `[PROJECT-LOCAL-CALIBRATION-STATE-v1]` 必须自身满足：

```text
usable_for_routing = true
scan.complete = true
derived_cache_only = true
Task/Result/Validation/Acceptance remain authoritative
```

PEH v1 的输入是这些**已经派生的 project-local state**，而不是项目源码、workspace、业务数据或 raw Task/PR payload 的副本。

删除 PEH config/state Issues 只删除 private cross-project cache，不删除任何 source-project evidence，也不破坏 Governance Core 或 project-local calibration。

## 4. Deterministic offline aggregation

Canonical v1 aggregation helper：

```text
templates/PRIVATE_EVIDENCE_HUB_AGGREGATOR.py
```

Input example：

```text
templates/PRIVATE_EVIDENCE_HUB_INPUT.json
```

Aggregator 只读取一个本地 JSON bundle，并向 stdout 输出 derived state JSON。它：

- 使用 Python stdlib；
- 不访问 GitHub/network；
- 不写 repository / Issue；
- 不配置 token/secret；
- 对 duplicate source、missing configured source、unusable source state、schema mismatch、duplicate group 或 inconsistent model identity fail closed；
- 不产生跨 Worker/Validator/Task-class 的单一 global model score。

v1 refresh 刻意保持 agent/manual-driven：有权限的 Agent 读取 private config Issue 与各 source project 的 local calibration Issue，组成 input bundle，执行或精确复现该 deterministic aggregation，然后更新同一 private Governance repo 的 derived-state Issue。跨 repo Action/token automation 不属于 v1。

## 5. Grouping and evidence

Direct model evidence 的 group dimensions 与 project-local calibration 一致：

```text
role
+ task_class
+ risk_level
+ model_semantic_key
+ reasoning_semantic_key
```

Worker 与 Validator 始终分开。

每个 private cross-project group 至少记录：

```text
source_project_count
source_repositories
sample_count
effective_sample_count
evidence_strength
cross_project_usable
```

一个 group 只有来自至少 **2 个 distinct configured source repositories** 时才允许：

```text
cross_project_usable = true
```

只有一个来源时可以显示统计，但不得冒充 cross-project evidence。

Worker 汇总保留 first-pass、final acceptance、rework、tests、violation 等 comparable metrics；Validator 汇总保留 review completion 与 confirmed findings / false-positive / missed-defect counts。Private aggregation 使用 project-local `effective_sample_count` 作为近期 evidence 权重，不把 runtime/dispatch 当成 model identity。

## 6. Routing position

`config/MODEL_ROUTING.yaml` 仍是 model qualification / routing 的 canonical owner。

PEH 只增加一个低权限 private prior：

```text
Task Override
>
Project Local Calibration
>
Private Cross-project Calibration
>
Governance Calibration Snapshot
>
Accepted External Benchmark Evidence
>
Bootstrap Seed
```

含义：

- 当前项目自己的 comparable evidence 永远优先于跨项目 private aggregate；
- 当前项目没有足够 local evidence 时，valid PEH state 可以让该用户自己的多项目历史参与排序；
- PEH 只能 rank 已经 qualified / suitable 的候选；
- PEH 不能自动 qualify/dequalify model、改变 registry/risk ceiling、绕过 Task/Owner exact executor、safety、permission、capability、independence 或 Lead Acceptance；
- PEH 不改变 Execution Economy 或 Dispatch。

PEH 缺失、disabled、malformed、partial、duplicate-state 或 source validation 失败时，routing 直接忽略该层并继续使用 Governance prior。

## 7. Fast loop vs slow loop

PEH 支持两个不同速度的反馈循环。

Fast loop：

```text
project work
-> project-local calibration
-> private cross-project aggregate
-> future private model/reasoning ranking
```

它不需要治理版本更新。

Slow loop：如果长期 private evidence 暴露统计方法或治理规则本身的问题：

```text
PEH evidence
-> REGRESSION / METHODOLOGY finding
-> explicit governance Task
-> Worker / independent validation / Lead Acceptance
-> possible Core change
```

PEH finding **不得自动 commit 或改写 Core**。如果某个 private finding 具有通用价值，可以在 Owner 明确决定后 generalize + sanitize，再作为 public-safe proposal 进入 official Governance。

## 8. Privacy and public boundary

PEH 是 private-fork capability，不改变 ordinary public adoption 的 stateless-upstream contract。

```text
Public direct adopter
-> project-local facts stay local
-> optional anonymous aggregate only

Private fork adopter with PEH
-> exact private source identities may stay inside own private fork
-> private cross-project aggregate stays private
-> no automatic delivery to official Governance
```

禁止因为 PEH 存在而要求 official adopter registration、central telemetry、phone-home 或 public downstream credentials。

## 9. Acceptance invariants

```text
PEH present != PEH enabled
PEH enabled != new product module
PEH state != governance authority
PEH state != model qualification authority
private cross-project prior < project-local prior
private evidence volume != governance Git-tree growth
finding != automatic Core rewrite
```

PEH 的价值是让私人治理实例“更了解自己多个项目上的模型表现”，而不是把 Governance Core 变成数据仓库或控制平面服务。
