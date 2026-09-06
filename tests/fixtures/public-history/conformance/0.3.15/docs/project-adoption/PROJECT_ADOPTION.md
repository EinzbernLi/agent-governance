# Project Adoption / 项目接入规范

版本：0.3.12  
状态：Accepted

## 1. Goal

项目接入中央治理时只保留**项目特有且长期有价值**的信息，不复制中央协议，也不因为治理而制造第二套项目管理系统。

正常接入是 AI-first：Owner 让 Web/Codex/其他有能力的 AI 阅读治理仓库和目标项目，AI 自动推导可确定内容，只对无法安全推导的选择询问 Owner。

项目应支持在 durable facts 足够时通过简单自然语言恢复，例如：

```text
“接管 <project> 的开发，我们继续”
```

Owner 不需要重复粘贴开发基线、治理准则或既有 Task/Result。

## 2. Minimal Project State

推荐最小结构：

```text
.agent/
├── GOVERNANCE_LOCK.yaml   # required: source + exact accepted governance version/ref + update mode
├── LOCAL_POLICY.yaml      # required: project-specific boundaries/tests/risk rules
└── PROJECT_STATE.md       # recommended: current stable project/phase state
```

按需添加：

```text
BOOTSTRAP.md          # PROJECT_STATE + repo structure 不足以冷启动，或启用 durable Lead Claim 时
ROUTING_BASELINE.yaml # 项目启用 project-local model calibration 时
checkpoints/          # 仅在 Lead/channel handoff、长任务或稳定恢复点需要时
decisions/            # 仅保存真正长期 ADR/decision
feedback/             # 仅保存显式 opt-in export/其他项目本地派生数据；默认不回传上游
```

当 `GOVERNANCE_LOCK.update_policy.mode=github_native_notify` 时，AI 额外安装：

```text
.github/workflows/governance-update-check.yml
```

其来源是治理仓库 `templates/GOVERNANCE_UPDATE_CHECK.yml`。`manual_pinned` 不安装该主动检查器。

当 accepted governance release 支持 project-local calibration、目标项目使用 GitHub Issue/PR durable facts、GitHub Actions 可用，且 `LOCAL_POLICY` / Owner 没有 opt-out 时，新项目默认启用 local-only calibration，无需再增加一个 Owner onboarding 问题。AI 安装：

```text
.agent/ROUTING_BASELINE.yaml              <- templates/ROUTING_BASELINE.yaml
.agent/tools/project-calibration.py       <- templates/PROJECT_CALIBRATION_EXTRACTOR.py
.github/workflows/project-calibration.yml <- templates/PROJECT_CALIBRATION_UPDATE.yml
```

该 workflow 只读同一项目 durable facts，并只维护一个 downstream-local `[PROJECT-LOCAL-CALIBRATION]` Issue cache；它不写 source tree、不回传上游、不注册 adopter，也不改变 Task/Result/Acceptance authority。已有项目策略、Owner 显式 opt-out、禁用 GitHub Actions 或权限不足时，不得强行安装/启用。

Lead Claim 使用中央 `templates/LEAD_CLAIM.yaml` 作为 payload schema，但持久化位置必须服从项目已经选择的事实源：

```text
Issue/PR-native -> GitHub Issue/PR comment/ref
file-native     -> project-local claim file/ref
```

长期使用 durable claim 的项目，应在 Bootstrap 中声明一个可持续发现的 `lead_claim_sink`。不得把已完成的临时 qualification Task 当成隐式长期 sink，也不得为了 claim 新建第二套与项目 Task/Result authority 并行的状态系统。

## 3. Natural-Language Takeover / Resume

项目名或 alias 可唯一解析、GitHub/repo durable facts 可访问时，新 Lead 应把自然语言“接管/继续”解释为：

```text
resolve project
-> restore latest durable state
-> locate canonical Lead Claim sink when enabled
-> reconcile latest checkpoint with newer facts
-> claim next Lead generation when needed
-> write -> re-read -> verify uniqueness
-> fresh Runtime Capability Probe
-> derive exactly one RESUME_TARGET as a recommendation only
-> report concise current state + recommended next action
-> AWAIT_OWNER_CONTINUE
-> only a later explicit Owner turn may authorize execution / dispatch / mutation
```

上述等待屏障适用于 takeover-only 消息。接管短语中内嵌的“继续”只表达控制连续性，不是屏障之后所需的 later Owner authorization；`RESUME_TARGET` 只回答下一步建议恢复什么，不授予执行权限。

如果同一条初始消息另含独立、明确、bounded 的工作指令，则它不是 takeover-only。任何后续动作仍必须先完成 activation/reconciliation，并继续满足既有 scope、authority、Task、safety 与 permission gates；不得从聊天措辞推断 scope expansion。

不得要求 Owner 重贴已经存在于 durable facts 中的：

- project baseline；
- architecture decisions；
- development rules；
- Task/Result bodies；
- checkpoint ID；
- commit SHA。

只有真实歧义无法由 durable facts 消解时才询问 Owner。

## 4. Checkpoint vs Lead Claim

职责必须分离：

```text
Checkpoint = 状态连续性：项目做到哪里
Lead Claim = 控制权连续性：当前哪个 Lead generation 有权继续
Bootstrap  = 恢复过程
Takeover   = 用户入口
```

Checkpoint 不得充当锁；Lead Claim 不得复制项目状态。

Checkpoint 恢复必须对账更晚的 `PROJECT_STATE / Task / Result / Lead Acceptance / code ref`。如果 checkpoint 已 stale，应补齐更新事实，不得回滚实际项目状态。

Durable Lead Claim 使用 read -> write -> re-read：同一 parent 的 sibling claims 或同 generation 的竞争 claims必须 fail closed，并用下一 generation 显式 conflict recovery。

## 5. Do Not Duplicate Task/Review State

项目必须选择一个正式 Task/Result/Review 事实源：

### Issue/PR-native（推荐给已使用 GitHub 工作流的项目）

```text
GitHub Issue/PR = Task / Result / Review / Acceptance refs
.agent/ does NOT mirror full Task/Result bodies
```

### File-native

只有项目无法使用 Issue/PR 作为正式事实源时，才使用 `.agent/tasks/`、`.agent/reviews/`、`TASK_INDEX.md` 等文件。

```text
Issue-native XOR file-native
```

禁止为了治理同时维护两套内容相同、都声称 authoritative 的 Task/Result 状态。

Project-local calibration Issue 不是第二 Task/Result store；它是可删除并从上述 durable facts 重建的 routing-prior cache。

## 6. Do Not Copy Central Protocols

项目侧不复制并私自修改中央：

- Agent Coordination；
- Dispatch Routing；
- Task Package Specification；
- Lead Acceptance；
- Session Bootstrap；
- Model Qualification / Reasoning / Adaptive Routing；
- LPRL core lifecycle rules。

项目特有规则进入 `LOCAL_POLICY.yaml`；中央治理版本由 `GOVERNANCE_LOCK.yaml` 指向。启用独立模块时，模块版本/ref 也由 lock 明确 pin。

## 7. Optional Local Resource Lifecycle (LPRL)

LPRL 是可选且独立 pin 的模块。启用时，按项目接受的 exact module ref 解析唯一模块根：

```text
modules/local-resource-lifecycle/
├── docs/
└── templates/
```

模块的 `VERSION` 位于 `modules/local-resource-lifecycle/VERSION`。ordinary governance 升级不得静默 repin LPRL；保留旧 module pin 时，项目继续使用该 pin 有效的历史 root/version 路径。

LPRL 不是所有项目的默认 hot path。项目接入时只做最小判断：

```text
明确没有本地开发/测试/部署资源
-> disabled

明确现在或未来会有本地开发/测试/部署资源
-> planning_only

进入真实本地阶段
+ Owner 提供 exact project root
+ current runtime 具有所需 local filesystem capability
-> tracking candidate
```

`planning_only` 可以依据 durable project facts 自动选择，因为它不读取或修改本机。它只表示未来需要本地资源规划。

本地 inspection/write 不按 Web/Codex 名称写死，而按 runtime capability 判断；没有 local filesystem capability 的 Lead 只能规划和签发本地 Task，不能声称已执行本地检查。

项目根目录必须由 Owner 明确提供。Agent 不得根据当前工作目录、HOME、TEMP、默认 workspace、仓库名或历史习惯自行选择 clone/deploy/root 位置，也不得在 root 不可用时自动改用替代目录。

绝对 project root 属于本机事实，默认不进入中央治理仓库或公共 GitHub 状态。具体规则见：

`docs/project-adoption/LOCAL_RESOURCE_ONBOARDING.md`

`tracking` 只授权本地资源事实跟踪，不授权 migration/cleanup/retirement/reclamation；后者继续走独立 LPRL Controlled Migration。

## 8. AI-first Governance Source / Update Adoption

项目只采用一个明确治理上游：

```text
governance.repository + protocol_version + pinned_ref
```

该上游是否来自官方仓库、Fork 或独立兼容发行版，不是 downstream 的额外模式。

正常接入流程：

```text
Owner: “将 <governance repo> 的治理规则接入当前项目”
-> AI 读取治理仓库
-> AI 读取目标仓库现有结构/规则
-> 保留或创建最小 .agent 状态
-> 只询问一次更新发现方式：
     github_native_notify (recommended)
     manual_pinned
-> 按 update mode 部署所需组件
-> 若 release 支持且项目未 opt-out，自动部署 local-only calibration 组件
-> 验证 cold-start / takeover
```

Project-local calibration 的默认启用不增加新的 Owner 选择，因为它是 local-only derived cache；Owner/project policy 随时可以显式关闭。治理更新发现方式仍然是 onboarding 中唯一必问的治理选择。

### `github_native_notify`

AI 把 `templates/GOVERNANCE_UPDATE_CHECK.yml` 安装到目标项目：

```text
.github/workflows/governance-update-check.yml
```

该 workflow 从 `.agent/GOVERNANCE_LOCK.yaml` 读取治理 source、accepted version/pin 和 mode，不维护第二份配置。它只在 downstream 自己的 GitHub Issue 中维护 `[GOVERNANCE-UPDATE-SIGNAL]`。

### `manual_pinned`

不安装 proactive checker。普通 takeover/new Task 继续使用 accepted exact pin，只有 Owner 明确要求检查/升级时才访问上游。

两种模式都满足：

```text
update discovered != update adopted
no auto-follow main
no automatic pin advance
LOCAL_POLICY stays downstream-local
```

发现新版/不同版本后：

```text
read release metadata
-> compatibility review
-> reconcile LOCAL_POLICY / active work
-> explicit downstream pin update
-> validation / acceptance
```

完整规范：`docs/project-adoption/GOVERNANCE_CURRENCY_PROTOCOL.md`。

## 9. Cold Start / Takeover Test

一个没有聊天上下文的新 Lead，应仅依赖 repo/GitHub 正式事实源恢复：

```text
project goal/current phase
current active Lead generation（若启用 claim）
architecture and protected boundaries
active task/result refs
current stable code state
next action
```

推荐验收方式是让 Owner 只发送一句自然语言，例如：

```text
“接管 <project> 的开发，我们继续”
```

若新 Lead 仍需要 Owner 大量重贴历史，优先改善 durable facts，不用长期靠人工复制聊天历史。

同 runtime 的新正式 session 也属于 takeover qualification：Web->Web、Codex->Codex 都必须从 durable facts 找到最新 parent claim，创建下一 generation，并 fresh probe。

## 10. Runtime Capability Is Session State

Web/Codex/Desktop 是否能 native dispatch、是否有 local filesystem read/write 都不写成永久客户端能力结论。

每个新的正式 Lead session 按 `DISPATCH_ROUTING_PROTOCOL.md` 自动 Runtime Capability Probe，并把结果默认只缓存在当前 session。

项目只在确有长期兼容性限制时记录 capability constraint；不要把某一次客户端观测永久化。

新正式 session 必须 fresh probe，即使 runtime 名称与上一 session 相同。

## 11. Local Policy

`LOCAL_POLICY.yaml` 只定义项目特有内容，例如：

- protected paths；
- Worker 默认可修改区域；
- 必须执行的 tests；
- domain-specific safety/quality rules；
- high-risk independent validation requirements；
- project-specific data/state boundaries；
- 可选 Execution Economy override；
- project-local model calibration enable/opt-out 与更严格 privacy/workflow constraints；
- 可选 LPRL mode、root authority 和本地 mutation 边界。

不要重复中央通用 dispatch/model/resume/LPRL core rules。

接入/升级治理时，已有 `LOCAL_POLICY` 必须保留；上游只能被显式 compatibility review 证明兼容后更新 pin，不得静默删除、覆盖或弱化项目更严格规则。

## 12. Model Routing / Calibration

新项目可从中央 Calibration Snapshot 获得弱先验；项目本地 durable outcomes 可自动形成 local prior：

```text
Task Override
> Project Local Calibration
> Governance Calibration Snapshot
> Bootstrap Seed
```

0.3.12 的默认 local-only 闭环：

```text
Task + Worker Result + Validator/Review + CI facts
-> terminal Lead Acceptance
-> [PROJECT-CALIBRATION-OUTCOME-v1] factual normalization
-> downstream-local GitHub workflow
-> exactly one [PROJECT-LOCAL-CALIBRATION] derived Issue cache
-> future Model Routing prior
```

该 cache 只有在 marker/schema 正确、scan complete、terminal outcomes 可解析且 state Issue cardinality 恰为 1 时才可用于 routing。缺失、重复、malformed、search incomplete 或超出当前 scan bound 时 fail closed：忽略 local cache，回退到 Governance Calibration Snapshot；不会阻断 Task authority。

Worker 与 Validator evidence 分开聚合；直接模型归因至少按 role + task class + risk + model semantic key + reasoning semantic key 分组。最终 PASS 不会抹掉 rework；material internal delegation 无法可靠归因时只进入 strategy-level evidence。Dispatch/runtime 只能作为 covariate，不能充当 model identity，也不能改写 Execution Economy。

项目局部结果不能单独自动改变中央全局 qualification/default。模型语义或 reasoning 语义 material revision 创建新 key，旧 key 只作为独立历史弱 prior。

模型反馈默认是 project-local derived evidence。外部 adopter 的项目名、源码、私有路径、业务数据、Task 事实和模型表现不会因为采用治理而自动回传治理上游。`PROJECT_ROUTING_FEEDBACK.yaml` 仅是 Owner/治理维护者明确 opt-in 后的匿名化 export 模板；ordinary local calibration workflow 从不自动调用它。

完整规范：`docs/model-governance/PROJECT_LOCAL_CALIBRATION_AUTOMATION.md`。

## 13. Explicit Non-Goals

Natural-language takeover、AI-first adoption、project-local calibration 与 LPRL onboarding 不引入：

- persistent session database；
- distributed lock service；
- cross-platform Agent Bus；
- runtime capability database；
- duplicated Handoff graph；
- Owner content relay；
- global workspace manager；
- automatic clone/deployment location selection；
- background filesystem daemon；
- automatic cleanup/migration；
- central adopter registry；
- required usage telemetry / phone-home；
- required token/cost accounting；
- central project-calibration database/daemon；
- automatic governance adoption / pin advancement；
- project-local calibration auto-promotion into global model qualification。

只使用现有 repo/GitHub durable facts + optional checkpoint + optional lightweight Lead Claim；本地 calibration 只使用项目自己的 durable GitHub facts；本地资源阶段只在 Owner 提供的 exact root 下由具备本地能力的 runtime 执行。

## 14. Principle

```text
central governance = reusable rules
governance source = one configured upstream repository
GOVERNANCE_LOCK = exact accepted source/version/ref + update mode
project .agent = minimal project-specific state
LOCAL_POLICY = downstream-local supplementary rules
GitHub Issue/PR or files = one chosen Task/Result fact source
update detector = downstream-local convenience, not authority
project-local calibration Issue = rebuildable routing prior, not authority
checkpoint = resumable state summary
lead claim = optional control-generation payload in the chosen fact source
LPRL planning_only = local intent, no local side effect
project root = Owner-supplied local fact
chat = interaction, not durable authority
```

治理接入如果要求项目维护大量与现有 GitHub 工作流重复的文件，说明治理本身需要继续做减法。

## 15. Persistent Workspace Establishment and Reuse

客户端或 Agent 产品自己的项目目录只是 runtime-local host/container fact，**不决定项目放在哪里**。例如 Codex Project Host 可以承载对话、planning、scratch 或启动信息，但它不因此成为受控开发 Workspace，也不拥有项目身份或治理 authority。

Persistent controlled Workspace 的物理位置必须由 Owner 指定或明确采用：

```text
client project host != persistent controlled Workspace
pre-existing folder != controlled Workspace by implication
OWNER-selected root -> verify -> establish/adopt -> controlled Workspace
```

Owner 可以给出 exact path，也可以明确授权在某个父目录下创建约定的项目目录；Agent 不得根据当前工作目录、客户端默认项目目录或历史 planning 路径自行决定长期位置。机器绝对路径继续作为本机事实，GitHub durable state 优先记录 alias + repo/ref/identity proof。

建立 trusted persistent controlled Source/Workspace 后，普通开发默认**复用**它：

```text
GitHub authoritative source/history
-> persistent controlled source (establish once)
-> fetch refs/objects
-> exact frozen Task baseline
-> transient isolated worktree for bounded implementation
-> disposable exact-SHA verifier when stronger isolation is required
```

`fresh full clone` 是 clean-room、无可信 persistent source、身份不可验证/损坏或 Task 明确要求时的例外，不是每个 Task 的默认动作。不得用 blind `git pull latest` 改变已冻结 Task baseline。

Runtime Deployment 与开发 Workspace 分离。Deployment identity 不以 Task ID 命名或推导；适用项目优先使用稳定 slot（例如 `live/canary/staging`）+ generation。更新 Source 不等于重建 Runtime，代码 generation promotion 也不应默认复制一整套 credentials/config/DB/State/logs 到新的 TASK 文件夹。

## 16. Project Conformance Gate

Adoption establishes facts; conformance evaluates them. A downstream project
should run the offline checker with its exact Owner-supplied/confirmed root and
explicit lock, local-policy, project-state, Lead/Task, module and topology refs.

```text
project runs != project is governed and conformant
```

The evaluator is read-only derived evidence. It must not discover the project,
query upstream during normal takeover, create authority files, advance a pin,
upload project facts or perform a local action. Missing/stale/conflicting facts
fail closed under `docs/conformance/GOVERNANCE_CONFORMANCE_PROTOCOL.md`.
