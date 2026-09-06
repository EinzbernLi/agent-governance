# Local Resource Onboarding / 本地资源接入

首次引入：ordinary governance 0.3.3
当前适用：ordinary governance 0.3.18
生命周期：Accepted supporting surface
权威边界：Project Adoption / local-resource onboarding supporting surface only；不创建新的 semantic authority owner。Local-action authority 仍由 durable Task + `LOCAL_POLICY` + current topology + applicable LPRL 共同决定；canonical semantic-owner mapping 以 accepted conformance/governance surfaces 为准。

> **First public release posture: Experimental / Preview.** LPRL has not completed sufficient real-project end-to-end validation, so production use is **not currently recommended**. The default is `disabled`; the existence of local resources alone is not permission to enable LPRL. `planning_only` and `tracking` are available only for explicit Owner-approved controlled evaluation.

## 1. Goal

把 LPRL 接到项目采用流程中，但不把“启用治理”变成自动扫描、自动部署或自动清理本机。

LPRL 规范与模板属于可选、独立 pin 的模块。启用时，项目从接受的 exact module ref 解析唯一根 `modules/local-resource-lifecycle/`，分别使用其 `docs/` 与 `templates/`；ordinary governance 升级不得静默改写旧 module pin 的路径。

首个公开版本中，LPRL 默认保持 `disabled`。只有明确参与受控评估的 Owner 才应选择后续模式；本地资源的存在本身不会自动启用 LPRL，也不构成生产采用建议。

核心原则：

```text
planning intent != local inspection
local inspection != local write
local tracking != migration/cleanup authority
project root = Owner supplied, never Agent chosen
```

## 2. Three modes

项目只使用三个本地资源模式：

```text
disabled
planning_only
tracking
```

### disabled

首个公开版本默认使用 `disabled`。项目当前没有可确认的本地开发/测试/部署资源需求，或尚未获得 Owner 的受控评估选择时，不加载 LPRL hot path。

### planning_only

项目 durable facts 已明确当前或后续会存在本地开发、测试、部署、State/Data/Evidence/Cache 等资源，因此 Lead 可以在规划层把项目分类为 `planning_only`；这不等于启用许可或生产推荐。

`planning_only` 只表示：

- LPRL 将参与后续资源规划；
- 可以在 GitHub/repo 中设计资源类型、边界和未来布局；
- 不授权读取本机目录；
- 不授权创建目录或文件；
- 不授权 clone/deploy 到任意位置；
- 不授权 migration/cleanup/retirement/reclamation。

因此，从 `disabled -> planning_only` 不需要本地文件系统能力，也不会产生本地副作用。

在首个公开版本中，`planning_only` 只表示 Owner 已明确选择受控评估范围内的规划阶段；没有该选择时继续保持 `disabled`。

### tracking

首个公开版本中的 `tracking` 只用于 Owner 明确批准的受控评估，不代表生产采用或生产安全性。

只有进入真实本地开发/测试/部署阶段，并满足以下条件后才能进入：

1. Owner 明确提供 exact project root；
2. 当前 runtime fresh probe 证明具有所需 local filesystem read/write capability；
3. runtime 对 Owner 提供的 root 做存在性/realpath/边界核验；
4. 首次本地写入得到 Owner 明确授权；
5. 所有 LPRL 本地事实只写入该 root 下的受控位置。

`tracking` 只授权项目本地事实跟踪，不授权 Controlled Migration、Retirement、cleanup 或 deletion。

## 3. Project-root authority

项目根目录是环境事实，由 Owner 指定，不由 Agent 规划。

必须满足：

```text
owner_supplied_root = required
agent_selected_root = forbidden
fallback_root = forbidden
implicit_clone_location = forbidden
write_outside_root = forbidden
```

Agent 不得因为：

- 当前工作目录；
- HOME；
- TEMP；
- 默认 workspace；
- 仓库名；
- 既有 clone 习惯；

自行选择新的项目根目录。

如果 Owner 提供的路径不存在，不得自动改用其他目录；只有 Owner 明确授权在该 exact path 创建项目根时才能创建。

## 4. Local runtime capability

本地动作按 capability 判断，不按客户端名称写死。

```text
GitHub/repo read-write only
-> 可做 planning_only
-> 不可宣称已检查本机

local filesystem read available
-> 可在 Owner 指定 root 下做已授权 read-only discovery

local filesystem write available
+ Owner 明确首次写入授权
-> 可进入 tracking 并 materialize local facts
```

在当前常用工作流中，真正的本地 inspection/write 通常由 Codex 或其他具有本地文件系统能力的 runtime 执行；Web Lead 如果没有该能力，只负责规划、Task/Result 和验收，不伪造本地执行。

## 5. Local fact location

推荐默认位置：

```text
<owner_supplied_project_root>/.local/lprl/
```

实际绝对路径属于本机事实，默认不提交到 GitHub，也不得写入中央治理仓库。

首次 materialization 前：

- 若项目使用 Git，先确保 `/.local/lprl/` 有精确 ignore 规则；
- 再创建 local LPRL facts；
- 本地 root marker 可保存 exact canonical path，但必须保持在 ignored local facts 中。

GitHub durable state最多记录：

```text
lprl_mode = tracking
project_root_status = owner_supplied_and_verified
```

不要记录用户机器的绝对路径，除非项目自己的私有政策明确要求。

## 6. Initial discovery

进入本地阶段后，第一轮默认只做资源发现和规划：

```text
Owner exact root
-> runtime capability probe
-> root verification
-> read-only inventory/discovery
-> proposed Source/Workspace/Deployment/State/Data/Evidence/Cache map
-> topology proposal
-> Lead review
-> optional local fact materialization
```

禁止把目录名直接映射为资源；继续遵守 LPRL：

```text
Task != Folder
Directory != Resource
Workspace != Deployment
Source != State
Data != Cache
```

## 7. Mutation boundary

以下动作不由 onboarding 或 `tracking` 自动授权：

- 移动/重命名既有项目目录；
- 删除或 retirement；
- cleanup/reclamation；
- 改写共享 State/Data；
- 替换 Deployment；
- 清理旧 Workspace/Cache；
- 任何 Controlled Migration。

这些动作继续进入独立 LPRL Controlled Migration 流程。

## 8. Adoption decision

项目接入治理时采用最小判断：

首个公开版本的默认结果是 `disabled`。本地资源存在、目录可见或历史上曾使用 LPRL，均不能替代 Owner 对 Experimental / Preview 受控评估的明确选择。

```text
明确没有本地开发/测试/部署资源
-> disabled

明确现在或未来会有本地开发/测试/部署资源
-> planning_only

进入真实本地阶段 + Owner 提供 exact root + local runtime 可用
-> tracking candidate
```

`planning_only` / `tracking` 只有在 Owner 明确批准受控评估时才可采用；在后续真实项目验证和明确 promotion 之前，不推荐生产采用。

不增加目录规划器、后台 daemon、自动部署器或全局 workspace manager。

## 9. Qualification

首个新项目至少验证：

1. `planning_only` 不产生任何本地 read/write；
2. Owner 未提供 root 时，本地 inspection/write fail closed；
3. runtime 不得自行选择替代 root；
4. Owner 提供 root 后，read-only discovery 只覆盖该 root；
5. 首次 local write 前再次确认授权；
6. local facts 不越出 root，绝对路径不进入公共治理仓库；
7. `tracking` 不被错误提升为 migration/cleanup authority。

第二项目只需验证正常 adoption + root confinement + 一次 read-only/local-fact tracking 路径即可。

## 10. Establishment, Reuse, and Client-Host Separation

Owner 提供的 persistent project root 与 Codex/Desktop/其他客户端自己的 Project Host 必须分开解释：

```text
client host = runtime-local container/context
persistent controlled Workspace = Owner-selected project location
```

客户端 host 可以在治理建立前已经存在并包含 planning/scratch/conversation artifacts；这些内容不需要被搬入正式项目，也不能因为“位于客户端项目目录”而获得治理 authority。现有目录只有在 Owner 明确选择 adoption 且核验通过后才成为 controlled Workspace。

建立可信 persistent controlled Source 后，正常更新优先复用已有 Git objects/refs：

```text
fetch -> freeze exact SHA -> transient worktree
```

不要为每个普通 Task 重新完整 clone/deploy。Disposable exact-SHA workspace 继续允许用于 clean-room/independent verification；它成功后也不会自动升级为 persistent Workspace。

受保护 Runtime Deployment 不是 source checkout。不得为了匹配 GitHub HEAD 对它做 reset/clean/fetch-align，也不得把 credentials、DB、State、config、logs 作为普通代码 promotion 的整目录复制物。

## 11. Ordinary Housekeeping vs Controlled Migration

`tracking` 本身仍不授权任意 cleanup。只有项目/local policy 已预先把对象明确声明为 `task_execution_only`/transient，或已经正面证明为可重建 Cache，并同时满足以下条件时，才允许由普通 Task 做 bounded housekeeping：

```text
durable Task handoff/evidence already closed
no unique Source/Data/Evidence
no protected/shared/runtime binding
no active writer
no active Task dependency
cleanup target exact and within local policy
```

任一条件 UNKNOWN，或对象属于 persistent Workspace、shared resource、State、Data、Deployment、protected resource，则继续进入 LPRL Retirement / Controlled Migration，不得把“旧、ignored、untracked、Task 命名”当删除授权。

## 12. Read-only Local Action Conformance

Before an authorized create/reuse/modify/migrate/retire action, evaluate the
exact project root, durable Task/policy and current topology through the Local
Action Gate. The decision is only `ALLOW | BLOCK` and is derived evidence.

`ALLOW` never performs the action or replaces its existing Task/Owner/LPRL
authority. cwd/HOME/TEMP/repository-name/historical/inferred roots block.
Unknown resources return an inventory/classification/reconciliation advisory;
quarantine, cleanup, migration and retirement remain separate authorized
actions. Source change never implies Deployment/State/Data/Evidence mutation.
