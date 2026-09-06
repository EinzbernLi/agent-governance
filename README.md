# Agent Governance

> 面向长期、多模型、多代理开发的轻量治理层。  
> A lightweight governance layer for long-running, multi-model and multi-agent software development.

**GitHub / repository durable facts are the technical authority; chat is the interaction surface.**  
This README is navigation and onboarding; it is not a normative protocol.  
本 README 只负责公开介绍、AI 接入和导航，不重新定义规范。机器可检查的语义归属见 `config/CONFORMANCE_POLICY.yaml`。

## 首次公开版本状态

- Core Governance：**0.3.25**，默认治理能力。
- LPRL：**0.2.5-pilot · Experimental / Preview · 默认关闭**。
- Governance Console：随仓库提供的 **optional read-only tooling**，不是产品模块，也不是治理 authority。
- Private Evidence Hub（PEH）：可选的 private-fork capability；通用方法/模板可公开，用户自己的私有 evidence/config/source list 不公开。
- License：Apache-2.0。

> [!WARNING]
> **LPRL 仍处于测试和真实项目验证阶段。当前不推荐普通用户启用，也不推荐生产依赖。**  
> 除非你明确是在参与测试、评估或验证，否则请保持 LPRL 关闭，等待后续经过更多真实项目端到端验证的版本。

## 30 秒 AI 接入

正常接入不要求你手工复制治理文件，也不要求先理解整个协议体系。把下面这段话交给一个**能够读取治理仓库和你的目标项目、并具备所需仓库写权限的 AI**：

```text
读取 EinzbernLi/agent-governance，
将其中的治理规则接入当前项目。
保留当前项目已有规则，并按治理仓库的 Informed Adoption 流程执行。
```

AI 应先读取治理仓库和目标项目，再只向你展示一次真正会改变项目行为或隐私边界的选择：

```text
1. 治理更新检测
   - github_native_notify（推荐）
   - manual_pinned

2. 项目本地模型校准
   - 启用（推荐，数据留在当前项目）
   - 禁用

3. 匿名模型反馈
   - 不分享（默认）
   - 明确允许生成/提交匿名 aggregate
   - “允许”不等于自动上传

4. LPRL
   - 不启用（默认，推荐）
   - 明确启用 Experimental / Preview 测试模块
```

你确认或调整一次后，AI 只把选择写入已有治理状态：

```text
.agent/GOVERNANCE_LOCK.yaml
.agent/LOCAL_POLICY.yaml
独立 module pin/state（仅在显式启用模块时）
```

不会再创建 `ADOPTION_PROFILE`、wizard state、feature-management DB、中央 adopter registry 或第二套 Task/Result authority。

**Core Governance 本身不是一个可关闭的 checkbox。** 一旦采用 Core，Task / Result / Lead Acceptance、exact-pin anti-drift、安全/权限边界、独立验证和 Conformance 等核心不变量按其规范生效。

详细接入规范：

- `docs/project-adoption/PROJECT_ADOPTION.md`
- `docs/project-adoption/GOVERNANCE_CURRENCY_PROTOCOL.md`
- `templates/GOVERNANCE_LOCK.yaml`
- `templates/LOCAL_POLICY.yaml`

## 接入后怎么用

### 接管 / 继续项目

```text
接管 <project> 的开发，我们继续。
```

这是 takeover / continuity 入口。Lead 应恢复并对账 durable state，给出当前状态和建议下一步；takeover-only 场景不会仅凭这句话自动执行恢复出来的工作，后续 mutation 仍需要符合现有 Task、scope、safety、permission 与 continuity gate。

### 正式启动 Worker / Validator

正式 Startup Card 不在 README 手写。Lead 必须使用 `templates/STARTUP_CARD_RENDER.py` 生成并校验卡片，并把 renderer 输出原样作为正式启动卡展示；README 不复制字段、launcher 或 Task 包。Exact presentation contract 只由 `docs/task-package/TASK_PACKAGE_SPEC.md` 定义，完整 Task authority 仍留在 GitHub durable facts。

### OWNER 正常只需要做什么

```text
OWNER gives intent
-> Lead reads durable facts and freezes bounded Task when needed
-> Lead executes directly or dispatches to a suitable executor
-> executor writes durable Result
-> Lead reviews / validates / integrates / accepts
```

OWNER 不需要在不同会话之间搬运完整 Task、Result、SHA 或项目历史。

## Runtime：按能力，不按客户端品牌

治理不会因为客户端名字叫“Codex”“Web”“Desktop Agent”就推断它拥有什么能力。

```text
runtime/client name != runtime capability
```

正式派发依据当前 Runtime Capability Probe。现有 profile 名称只是兼容标识：

```text
web_interactive
= 当前目标执行路径上不能主动 native-dispatch 子代理的交互式 runtime

codex_native_subagents
= 当前目标执行路径上已证明具备 native subagent dispatch 的 agent runtime
```

因此“Codex 模式”在文档中只是对 **native-subagent-capable Agent 客户端** 的历史/兼容称呼，不绑定某一家产品；“Web 模式”表示 **non-native-delegating interactive runtime**，也不绑定具体网页产品。

一般偏好是：

```text
native-subagent-capable Lead
-> native_delegate_preferred

non-native interactive Lead
-> lead_direct_preferred
```

只有在 Web/non-native Lead **已经确定必须外派**之后，才考虑外部执行面的 placement：需要本机文件系统、workspace、CLI、软件、测试或 artifact 环境的 Task 优先交给 local-capable Agent；纯远程 GitHub/文档验证优先交给独立 Web conversation/session（当独立性或 Task contract 要求时）。

**这条 Web-only placement 不会重分类 native-agent Lead。** native-agent Lead 为了调用自身 native child 覆盖之外的软件而使用 external transport 时，仍保留原来的 native profile，不重新执行 Web placement，也不会被“弹回 Web”。

Canonical dispatch：`config/DISPATCH_POLICY.yaml`。

## 核心架构

```text
ONE Active Lead Controller
        ↓
Durable project state + Model Routing
        ↓
Runtime Capability Probe
        ↓
Task Package
        ↓
Dispatch Policy
 current_session | native_dispatch | external_owner_launch | blocked
        ↓
Worker / Validator durable Result
        ↓
Lead Review / Integration / Final Acceptance
```

普通治理只保留少量明确 authority：

```text
GitHub / project durable state -> facts
Model Governance              -> who is suitable
Task Package                  -> what may be done
Dispatch Policy               -> how executor is reached
Lead Acceptance               -> whether result is accepted
```

Parallel workstream、local planning、client project host、Console display 都不会成为新的 authority。

## Durable completion

客户端 UI 显示“完成”不等于治理意义上的完成：

```text
runtime/UI completion
!= durable Task completion
!= Lead acceptance
```

正式 Worker/Validator 结果必须写回 Task 指定的 durable sink，并能按 exact Task revision / commit / PR / artifact 对账。OWNER 说“外部 Agent 已完成”只触发 Lead 去读取 durable Result，不替代 Result 本身。

## Core Governance

Core 是默认且可独立使用的治理层，不依赖 LPRL。它包含/约束的主要方面包括：

- durable Task / Result / Lead Acceptance；
- exact pin / anti-drift / update adoption boundary；
- Lead continuity 与 takeover；
- model routing / reasoning adapter / project-local calibration；
- runtime capability probe 与 dispatch；
- independent validation；
- offline/read-only Governance Conformance；
- stateless-upstream / downstream-local privacy boundary。

普通使用不需要把所有协议一次性加载进上下文。Hot path / cold path 和 canonical owner map 由 `config/CONFORMANCE_POLICY.yaml` 管理。

## LPRL（可选，仍在测试）

**Local Resource Lifecycle（LPRL）是第二个可选产品模块，但目前仍然是 Experimental / Preview。**

```text
Core Governance requires LPRL: false
LPRL loaded by default: false
module exists != module must be loaded
```

LPRL 用于 Source / Workspace / Deployment / State / Data / Evidence / Cache 等本地资源生命周期边界，但真实项目端到端验证仍不足。

**当前建议：不要把 LPRL 用于普通开发依赖或生产资源治理。** 只有当你明确愿意参与测试/评估，并理解其 Preview 状态时才应显式启用。否则保持关闭，等后续经更多真实项目验证后的版本。

规范入口：`modules/local-resource-lifecycle/docs/LPRL_SPEC.md`。

## Governance Console（可选工具）

仓库包含 `console/`，它是一个 derived read-only operator view：

```text
Console display
!= Task authority
!= Lead authority
!= acceptance
!= adoption state
```

Console 不是第三产品模块，不是普通 AI 接入的必问项，也不是运行 Core 的前置条件。没有 Console，Core 仍完整工作。

## Private Evidence Hub（可选 private-fork capability）

PEH 允许用户在**自己的私有治理 fork**中，把多个项目已经可用的 project-local calibration 聚合为跨项目 routing prior。

公开仓库可以包含：

```text
通用协议
统计/聚合方法
模板
离线 aggregator
```

但用户自己的以下内容应保持私有：

```text
source repository allowlist
private project identity
private calibration evidence
private Hub Issues / derived state
```

PEH 默认关闭，不是第三产品模块，不授予模型 qualification，不自动改写 Core，也没有中央 adopter database / daemon / telemetry sender。

规范入口：`docs/model-governance/PRIVATE_EVIDENCE_HUB.md`。

## 更新与隐私

被治理项目只认一个明确的 `governance source + exact accepted pin`。更新发现不等于采用：

```text
update discovered != update adopted
```

`github_native_notify` 只在 downstream 自己的 GitHub 中维护 update signal；`manual_pinned` 不做主动检查。两者都不会自动 follow main 或自动推进 pin。

上游治理保持 stateless-upstream：正确使用本仓库不要求 adopter 注册、usage telemetry、项目事实回传或 downstream credential。项目名、业务数据、raw model outcomes、LOCAL_POLICY、PROJECT_STATE、Task/Issue/PR/branch/SHA 等项目事实留在 downstream。

## Conformance

`templates/GOVERNANCE_CONFORMANCE_CHECK.py` 是 offline、read-only evaluator。它只从显式输入检查 accepted facts：

```text
accepted facts
-> read-only evaluation
-> CONFORMANT | RECONCILIATION_REQUIRED | BLOCKED
```

Conformance Result 是 evidence，不是 action authority，也不是 Lead Acceptance。

详细规范：`docs/conformance/GOVERNANCE_CONFORMANCE_PROTOCOL.md`。

## 文档导航

- 项目接入：`docs/project-adoption/PROJECT_ADOPTION.md`
- 治理更新：`docs/project-adoption/GOVERNANCE_CURRENCY_PROTOCOL.md`
- Task Package / Startup Card：`docs/task-package/TASK_PACKAGE_SPEC.md`
- Dispatch：`config/DISPATCH_POLICY.yaml`
- Model Routing：`config/MODEL_ROUTING.yaml`
- Lead Acceptance：`docs/acceptance/LEAD_CONTROLLER_ACCEPTANCE_PROTOCOL.md`
- Conformance：`docs/conformance/GOVERNANCE_CONFORMANCE_PROTOCOL.md`
- PEH：`docs/model-governance/PRIVATE_EVIDENCE_HUB.md`
- LPRL：`modules/local-resource-lifecycle/docs/LPRL_SPEC.md`
- Community：`CONTRIBUTING.md`
- Security：`SECURITY.md`

## Public release boundary

公开发行使用 clean public seed：不会把 private Governance Lab 的 `.agent/**`、`.publicization/**`、private `CHANGELOG.md` 或 private Git history 带入公开仓库。公开仓库从 fresh root/history 开始。

当前首个公开发布身份：

```text
repository: EinzbernLi/agent-governance
Core: v0.3.25
LPRL: 0.2.5-pilot (Experimental / Preview, disabled by default)
license: Apache-2.0
```

Release identity 以根目录 `VERSION` 与 `GOVERNANCE_RELEASE.yaml` 为准。
