# Lead Controller Acceptance Protocol

版本：0.3.16
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
16. Dispatch Policy 要求的 route、terminal handoff、observation 与 nested-delegation evidence 是否完整；
17. `BLOCKED` / `NEEDS_ATTENTION` 是否确有必要 authority/permission/fact/decision/capability 缺失且无安全 in-scope alternative；
18. Validator evidence boundary 是否保持独立，污染后是否取得 fresh validation。

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
- Dispatch、provider/runtime 与 reasoning 约束是否仍由各自 canonical owner 满足。

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

Delegated lifecycle and parent observation are owned by `config/DISPATCH_POLICY.yaml`.
Acceptance only verifies the resulting terminal evidence; it does not redefine
dispatch behavior. Child Result and self-check never replace final acceptance or
required independent validation.

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

When enabled, terminal acceptance may append
`[PROJECT-CALIBRATION-OUTCOME-v1]` using
`templates/PROJECT_CALIBRATION_OUTCOME.json` and
`docs/model-governance/PROJECT_LOCAL_CALIBRATION_AUTOMATION.md`.
Only durable facts may be normalized: terminal highest revision wins, Worker and
Validator samples remain separate, rework remains visible, and unknown evidence
is omitted or null rather than guessed. Material internal delegation uses
strategy-level attribution when direct model attribution is not supportable.

## 9. Calibration Does Not Become Authority

Project-local calibration is a rebuildable prior/cache. It cannot override
Task/Result/Validator/Acceptance facts, promote an unqualified model, bypass
scope/safety/capability/independence, or change execution economy.

## 10. Hard Rules

One active Lead owns final acceptance from current GitHub/repository facts.
Worker/Validator/UI/cache evidence is not acceptance; stale candidates are not
current; rework remains visible; unknown facts are never guessed.

## 11. Conformance Before Relevant Acceptance

For governance releases and Tasks that can affect governance/module currency or
local deployment/resource actions, the Lead must read the exact-candidate
conformance Result before acceptance. `CONFORMANT` is necessary where the Task
requires it, but never sufficient: scope, tests, independent validation and all
existing acceptance gates remain mandatory. `RECONCILIATION_REQUIRED` or
`BLOCKED` cannot be waived by Worker self-report or optional Governance Console
display.

The conformance Result is derived evidence, not Lead acceptance, action
authority, pin adoption or a second workflow state.
