# Adaptive Routing & Cross-Project Feedback

版本：0.3.13  
状态：Accepted

## 1. Purpose

利用真实 governed work 持续校准 **executor selection + reasoning**，但不把 dispatch/runtime mechanics 错当成模型能力，不要求人类逐 Task 打主观分，也不把外部项目数据自动送回中央治理。

核心链路：

```text
Task
+ Worker Result
+ Validator Result / Review
+ Lead Acceptance
+ PR / CI durable facts when applicable
        ↓
normalized factual calibration outcome
        ↓
Project Local Calibration
        ↓
future Task routing prior
```

最终 Task/Result/Validation/Acceptance 的 authority 不变。Calibration 只是可重建的派生 prior。

### Evidence-acquisition front end

在进入既有 calibration loop 前，Model Routing 可对下一次安全、客观、可验证且 comparable 的机会执行一次确定性的 evidence-deficit preference：只有已通过 Task override、registry role/task/risk ceiling、能力可达性、independence、material suitability 与 safety/permission/side-effect gates 的候选才可参与；`insufficient` / `developing` comparable evidence 视为 under-evidenced，`established` 不再获得该 preference。更少发展的 challenger 优先，完全相同适配度时才使用既有 routing prior tie-break。

该 preference 不随机、不按百分比分配、不创建 bandit 或全局模型分数，并且不改变资格或权限边界：candidate 仍仅能 shadow / qualification / evidence acquisition，provisional 仍不得超出 registry ceiling。优先使用低/中风险 read/review/navigation/shadow 工作；高/critical risk、real-write、不可逆或 separately gated 工作不得仅为采样而使用。未实际执行的 challenger 不获得 sample credit，也不受 quality penalty。

## 2. Calibration Layers

```text
Task Override
> Project Local Calibration
> Governance Calibration Snapshot
> Bootstrap Seed
```

中央 Calibration Snapshot 是弱先验；项目本地 calibration 可以更快适应，但只能影响本项目已合格候选的 routing prior。单项目数据不得自动改变中央 qualification / preferred default。

Execution Economy 与 calibration 分离：

```text
Model Routing / Calibration = WHO is suitable
Runtime Capability Probe    = WHAT is reachable now
Execution Economy           = direct/native route preference among compliant equivalents
Dispatch                     = HOW to reach the selected execution route
```

`dispatch_route`、runtime profile、client/channel 都只能是 covariate，不是 model identity。

## 3. No Manual Model Scores

不要求 Owner/Lead 输入 `8/10`、星级、主观满意度或一个全局 model score。

Terminal Lead Acceptance 可根据已经存在的 durable facts 自动生成：

`[PROJECT-CALIBRATION-OUTCOME-v1]`

其 JSON schema 见 `templates/PROJECT_CALIBRATION_OUTCOME.json`。

它只规范化事实，例如：

- role / task class / risk；
- model semantic key / reasoning semantic key；
- final accepted vs rejected/abandoned；
- accepted first pass vs accepted after rework；
- rework count；
- tests/CI outcome；
- scope / permission / safety violation；
- Validator confirmed material findings；
- 在后续 durable evidence 足够时可审计的 false positive / missed defect；
- dispatch/runtime covariates；
- 只有在本来就可获得时才记录 coarse latency/cost bucket。

Lead Acceptance 本身仍然是最终判断；calibration block 只是把已经形成的 durable结论转成机器可读事实，不新增一层 authority。

## 4. Worker and Validator Are Separate

禁止把所有角色压成一个“模型总分”。

Worker 最少保留：

```text
first-pass success
final acceptance
rework burden
tests/CI
scope/permission/safety violations
```

Validator 最少保留：

```text
review completed
confirmed material findings
confirmed false positives when later evidence makes this auditable
confirmed missed defects when later evidence makes this auditable
```

“没有发现问题”本身不是 Validator 失败。只有后续 durable evidence 能证明 false positive / missed defect 时才计入对应负面事实。

## 5. Calibration Key / Semantic Revision

直接 model attribution 的最小 group key：

```text
role
+ task_class
+ risk_level
+ model_semantic_key
+ reasoning_semantic_key
```

模型版本、行为语义或 reasoning 语义发生 material revision 时必须使用新 key。

```text
new semantic key != overwrite old key
old key = separate / weak historical prior
new key = current direct evidence starts fresh
```

不得因为显示名相同就把两个语义版本的样本硬合并。

## 6. Internal Delegation Attribution

普通 Task 没有 material internal delegation 时，可以把结果归因给正式 assigned executor。

如果实际工作由不可观察或多模型 internal children 实质完成：

```text
attribution = execution_strategy
```

此样本进入 strategy-level aggregate，不直接计入入口模型的质量 prior。

这样可避免：

```text
entry model receives credit/blame for unobserved child work
```

## 7. Recency and Rework

近期 comparable evidence 权重高于旧 evidence。默认 project-local extractor 使用时间衰减，只输出事实聚合和 evidence-strength band，不产生一个跨角色/跨任务类的全局 scalar score。

最终 PASS 不能抹掉返工：

```text
accepted_first_pass = true
```

与：

```text
accepted_first_pass = false
final_accepted = true
rework_count > 0
```

必须是不同的 outcome。

同理，一次成功或一次失败不能自动造成中央 preferred/degraded 变更。

## 8. Downstream-local Automation

实现规范：`docs/model-governance/PROJECT_LOCAL_CALIBRATION_AUTOMATION.md`。

模板：

```text
templates/PROJECT_CALIBRATION_OUTCOME.json
templates/PROJECT_CALIBRATION_EXTRACTOR.py
templates/PROJECT_CALIBRATION_UPDATE.yml
```

首次 informed adoption 只有在 Owner 选择启用 project-local calibration 且项目能力/策略允许时才部署；选择关闭时不安装该 local automation，Model Routing 回退到治理 prior，不影响 Task authority。

推荐 downstream 安装位置：

```text
.agent/tools/project-calibration.py
.github/workflows/project-calibration.yml
```

Workflow 使用项目自己的 `github.token`：

- 读取同一 repository 的 Issue/PR durable comments；
- 读取本项目 `LOCAL_POLICY`；
- 维护一个固定的 downstream-local `[PROJECT-LOCAL-CALIBRATION]` Issue；
- 不修改 source tree；
- 不向治理上游写入；
- 不要求 central DB、daemon、adopter registry、hosted telemetry。

Calibration Issue 是 derived cache only。删除后可从 durable comments rebuild。

## 9. Fail-closed State Quality

Project-local calibration 只有在以下条件满足时才可参与 routing：

```text
scan complete
+ terminal outcomes parse successfully
+ exactly one local calibration state Issue
+ state marker/schema recognized
```

以下状态必须标记 `usable_for_routing: false`：

- GitHub search incomplete / 超过当前 search bound；
- malformed terminal outcome；
- 重复 state Issues；
- extractor failure。

Calibration cache 失效不会让项目 Task authority 失效。Model Routing 应忽略该 cache 并回退到 Governance Calibration Snapshot / Bootstrap Seed。

## 10. Privacy / External Adopters

默认：

```text
external project local calibration -> local only
required upstream telemetry        -> NONE
required project registration      -> NONE
required cost/token accounting     -> NONE
```

`templates/PROJECT_ROUTING_FEEDBACK.yaml` 仅作为 **explicit opt-in anonymized aggregate export** 的结构模板。安装治理、运行本地 calibration 或发现新版治理都不会自动触发该 export。

Upstream export 必须先在 downstream 边界完成聚合和匿名化。禁止发送 project/repository identity、Task/Issue/PR/SHA/path/business/personal facts、raw sample rows、原始模型 outcome/evidence，或为了证明来源多样性而创建稳定 adopter pseudonym/hash。`LOCAL_POLICY.model_calibration.upstream_export=true` 只表示允许明确准备/提交这种 aggregate；它从不授权 automatic cross-repository delivery。

中央/global calibration 可以使用：

- 治理维护者自己控制且来源可审计的 pilot / benchmark；或
- Owner 明确 opt-in、已在 downstream 侧匿名化聚合的 external-adopter evidence，作为补充 evidence。

## 11. Central Promotion / Demotion

中央调整继续服从 `config/CALIBRATION_SNAPSHOT.yaml`：

- 最低样本量；
- 多项目来源；
- recent evidence；
- 与 qualification/benchmark 不冲突；
- Lead Controller review；
- 单项目不得 auto-promote / auto-demote global defaults。

没有稳定项目身份的匿名 external-adopter aggregate 不得被机械计作 `min_distinct_project_sources` 的 proof。不得为了满足该门槛而引入 adopter registry、stable pseudonym 或 hash。匿名 aggregate 可支持人工 review、hypothesis、qualification/matched-trial priority 等低权限用途，但不能单独自动 promote/demote global qualification/default。

Project-local cache 不是绕过中央 promotion gate 的渠道。

## 12. Decision Loop

```text
Task features + risk + required capabilities
+ global prior
+ usable project-local calibration
-> Model Routing ranks qualified candidates
-> Runtime Probe resolves reachability
-> Execution Economy chooses direct/native preference among compliant equivalents
-> Dispatch reaches the execution session
-> execution + validation
-> Lead Acceptance
-> normalized factual calibration outcome
-> local derived calibration rebuild
-> future local routing prior
```

> Learn which qualified executor/reasoning works for which comparable task in this project; never confuse transport, runtime availability, or one final PASS with a universal model score.
