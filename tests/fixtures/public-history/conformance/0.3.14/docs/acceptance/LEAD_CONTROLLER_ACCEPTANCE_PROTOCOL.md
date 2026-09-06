# Lead Controller Acceptance Protocol

版本：0.3.14
状态：Accepted

## 1. Purpose

本协议规定 Lead Controller 如何对 Worker / Validator 的交付进行最终验收。目标是避免“执行者自报 PASS 即视为完成”，并将最终正确性责任固定在唯一 active Lead Controller。

只有 Lead Controller 可以把正式 Task 状态设为 `accepted`。Worker、Validator、CI、benchmark 和 project-local calibration 都只能提供 evidence / prior，不能替代最终验收。

## 2. Durable Handoff Gate

在实质 Review/Acceptance 前，Lead 必须确认：

1. Task 声明的 canonical result sink 中存在 required terminal Result；
2. read-back 能确认 exact Task ref/revision、required marker/body；
3. Task 要求 remote mutation 时，Result 的 commit/branch/PR/artifact exact ref 与实际 remote ref 一致；
4. local UI completion、Owner 转述“完成”、local planning done 均不得替代以上 evidence。

缺少任一项时状态是 `INCOMPLETE_HANDOFF`；Lead 应先补齐 durable handoff，而不是对不存在/不可对账的 Result 做 PASS/REWORK 判断。

若任务来自 takeover/resume，还必须先满足 applicable durable re-anchor / Lead Claim activation / fresh Runtime Capability Probe。

```text
runtime completion != durable Task completion
durable handoff != final acceptance
```

## 3. Minimum Acceptance Checks

Lead 至少检查：

1. Task Package 是否完整且仍 current；
2. 实际修改/动作是否超出 scope；
3. 是否触碰 forbidden files/boundaries；
4. 是否符合既有 ADR / contract / schema；
5. required tests/validation 是否真实执行；
6. 失败/跳过是否完整披露；
7. 是否通过降低阈值、删除断言或弱化 contract 获得表面 PASS；
8. 是否引入未授权架构耦合、兼容性或隐式语义变化；
9. RESULT 描述是否与代码、remote refs、logs、PR/CI 一致；
10. acceptance criteria 是否逐项满足；
11. executor-local planning 是否被错误当成 Task authority；
12. candidate/head 是否仍与 acceptance-relevant frozen/current baseline 一致；
13. runtime-local memory/checkpoint/scratch 是否仅为 execution aid；
14. stale/provisional evidence 是否按 exact input/baseline 与 unchanged evidence/test contract 完成 reconcile/rerun；
15. same-end project switch 是否重新确认项目身份。
16. material dispatch decision 是否分别记录 capability availability、work suitability、selected route 与 bounded bypass reason；native-preferred 下的 direct bypass 是否有效。
17. delegated lifecycle 是否经过 terminal/exception handoff，parent 是否遵守 event/blocking/long wait 与无 substantive progress inspection 的默认规则。
18. `BLOCKED` / `NEEDS_ATTENTION` 是否确有必要 authority/permission/fact/decision/capability 缺失且无安全 in-scope alternative；普通执行困难不得伪装成 blocker。
19. nested delegation 是否为 explicit opt-in，且 parent accountability、bounded purpose、material benefit、ownership 与 boundary preservation 均有证据。
20. 若 Validator evidence boundary 被 material substantive mid-flight observation/steering 改变，是否撤销 independent-validation credit 并取得 fresh validation。

Candidate stale 时不得 current-head accepted。Reusable payload/evidence 不会自动赋予 candidate currency。

## 4. Core / High-risk Extra Checks

涉及核心代码、关键 schema、权限、安全或不可逆操作时还应检查：

- 修改是否确有必要；
- 是否存在更小实现；
- 是否改变公开接口/数据语义/数学物理含义；
- 是否需要 ADR/migration；
- 是否完成 independent validation / regression；
- 是否存在权限或 scope expansion；
- 是否需要 fail-closed / rollback path。
- native dispatch capability 已证明、work suitable 且 profile 为 `native_delegate_preferred` 时，若走 `current_session` 是否存在合法 bounded bypass reason；quota saving alone 不合格。
- provider/runtime-specific executor 或 reasoning ladder 是否被写入 ordinary governance core；provider mapping 必须留在 adapter/config 层。

## 5. Final Dispositions

### PASS / accepted

Task 达到验收标准，可进入 merge/后续阶段。

### REWORK

总体方向可接受，但存在必须修复的问题。Lead 应明确 failed acceptance item、rework boundary、是否需要新 Task、是否调整 executor/reasoning。

### REJECT

方向错误、严重越权、结果不可验证或与架构冲突，不应继续在当前结果上修补。

### BLOCKED

依赖缺失、设计冲突或环境不可用，当前无法完成；由 Lead 重新决策。

`INCOMPLETE_HANDOFF` 属于进入上述判断前的交付状态，不等于 BLOCKED/REWORK。

## 3.1 Delegated execution observation

Lead 只能在 terminal/exception handoff 后读取 delegated substantive Result，并随后执行 integration、risk-based validation 与 final acceptance。`CHILD_RUNNING` / `PARENT_WAITING` 期间默认不请求 unsolicited progress、不重复 substantive polling、不读取 intermediate patch/result 监控进度、不做 partial integration 或无例外 steering。无 event/blocking wait 时，bounded low-frequency terminal-status check 不能获取 substantive output。

允许的介入仅包括 Owner status request、timeout、runtime abnormality/error、child `BLOCKED` / `NEEDS_ATTENTION`、safety/scope/shared-write risk 或 required interrupt/cancel/retask；先读 compact status，只有必要时才做 bounded diagnostic read。

Child Result 永远不能替代 Lead final acceptance。Worker/Validator self-check 也不能替代 required independent validation。

## 6. Independent Validation

High / critical risk 优先使用独立 Validator。独立性约束 substantive evidence，不是名字或 UI session 标签。

Validator 应主动寻找：

- boundary / regression；
- implicit interface change；
- numerical/semantic instability；
- unauthorized modification；
- missing path/error handling；
- compatibility/performance degradation。

Worker self-check、internal child review 或 Lead 自审可以是执行证据，但不能自动获得 governance-level independent-validation credit。

Material substantive mid-flight observation/steering that changes the Validator evidence boundary contaminates that run for required independent-validation purposes. The run cannot receive independent-validation credit; obtain a fresh substantively independent validation when the Task still requires one. Ambient control context alone is not contamination.

## 7. Final Review Record

Final Review/Acceptance 应 durable 记录：

- task ref / task chain ref；
- reviewed commit/PR/artifact；
- Worker/Validator Result refs；
- key checks/tests；
- risk judgment；
- final disposition；
- REWORK/REJECT/BLOCKED 原因；
- merge authorization 是否存在。

Lead 必须依据仓库/GitHub durable facts，而不是模糊聊天记忆。

## 8. Project-local Calibration Outcome

当项目启用 0.3.12 project-local calibration，**terminal** Lead Acceptance 应在 durable evidence 足够时自动附加 marker：

`[PROJECT-CALIBRATION-OUTCOME-v1]`

紧随其后放一个 JSON code block。Schema 示例：`templates/PROJECT_CALIBRATION_OUTCOME.json`；完整协议：`docs/model-governance/PROJECT_LOCAL_CALIBRATION_AUTOMATION.md`。

例如：

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

这不是要求 Owner/Lead 人工给模型打分。Lead/AI 只把本次 Acceptance 已经确定的事实规范化，例如：

```text
role / task_class / risk
model_semantic_key / reasoning_semantic_key
accepted_first_pass / final_accepted
rework_count
tests/CI
scope / permission / safety violation
Validator confirmed finding / false positive / missed defect when auditable
dispatch/runtime covariates
optional coarse latency/cost bucket
```

如果字段不能从 durable evidence 确定，应使用 schema 允许的 `null` 或不生成该可选事实；不得猜测。

### 8.1 Terminal and revision

只有 `"terminal": true` 的 outcome 才进入 calibration。

如果后续发现 machine-readable normalization 写错，但 authoritative Acceptance 本身未改变，可发布更高 `revision`。Extractor 对同一 `task_ref` 只使用最高 revision；这避免重复采样。

### 8.2 Worker / Validator separation

一个 terminal Acceptance 可以包含多个 `samples[]`，例如一个 Worker sample + 一个 independent Validator sample。

Worker 与 Validator 必须分别聚合。禁止把它们压成同一全局 model score。

### 8.3 Rework is durable evidence

最终 accepted 不得把返工抹平：

```json
{
  "accepted_first_pass": false,
  "final_accepted": true,
  "rework_count": 2
}
```

与 first-pass accepted 是不同 outcome。

### 8.4 Validator negative evidence

`false_positive_confirmed` / `missed_defect_confirmed` 只有后续 durable evidence 真的确认时才填写。没有发现问题并不是 missed defect。

### 8.5 Internal delegation

如果 material internal delegation 使 direct model attribution 不可靠，应使用 `"attribution": "execution_strategy"` 并给出 bounded `strategy_key`。不得把不可观察 child 的结果静默归给入口 model。

## 9. Calibration Does Not Become Authority

Project-local calibration Issue/cache：

- 不能覆盖 Task/Result/Validator/Acceptance facts；
- 不能把未 qualified model 自动升级成 production qualified；
- 不能绕过 Task/safety/capability/independence；
- 不能改变 Execution Economy；
- 缺失/损坏时只回退到 Governance Calibration Snapshot；
- 可以删除并从 durable outcomes rebuild。

## 10. Hard Rules

```text
one active Lead
Worker/Validator evidence != final acceptance
runtime/UI completion != durable completion
stale candidate != current accepted candidate
project calibration != Task/Result/Acceptance authority
project calibration != global automatic promotion
final PASS after rework != first-pass PASS
unknown calibration fact != guessed value
GitHub/repository durable facts > chat/memory/cache
```
