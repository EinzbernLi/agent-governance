# Local Project Resource Lifecycle (LPRL)

版本：0.2.5-pilot
状态：Replay Candidate（Facts-profile revision；未修改的 decision/action artifact 可继续使用 v0.2.2-compatible schema）

## Public-release maturity

For the first public release, LPRL is **Experimental / Preview**. Its technical model is internally defined, but sufficient real-project end-to-end validation has not yet completed; production use is **not currently recommended**. Public adoption is disabled by default unless the Owner explicitly opts into controlled evaluation. LPRL-only base operation does not require Core Governance.

## 1. Purpose

LPRL 治理项目本地 Source / Workspace / Deployment / State / Data / Evidence / Cache 的身份、保护、生命周期、退役与空间回收。它不把目录名、Task ID、Git 命令或某个客户端写成全局规则。

目标是在不丢失唯一价值、不破坏运行状态、不误伤共享拓扑的前提下，识别并安全退出可重建的 Workspace/Cache/旧 Deployment 等资源。

## 2. Core invariants

```text
Task != Folder
Directory != Resource
Workspace != Deployment
Source != State
Data != Cache
Evidence != Full Workspace Backup
Deployment Identity != Task Identity
Source Identity != Physical Location
Source Origin != Controlled Workspace Identity
Deployment Definition != Runtime Deployment
Equality Check Hash != Provenance / Artifact Authority
Measurement Basis != Measurement Confidence
Unknown != Reconstructable
Candidate != Retirable
Apparent Bytes != Reclaimable Bytes
Registry Facts != Gate Verdict
Requested Retirement != Authorized Retirement
Stale Snapshot != Valid Authorization
Held != Complete
Same Snapshot != Same Scope
Non-null Ref != Valid Proof
```

## 3. Resource model

七类资源：`source | workspace | deployment | state | data | evidence | cache`。

必须区分：

- logical resource；
- component；
- physical location；
- non-resource physical/container scope；
- storage object；
- topology edge。

一个目录可以包含多个逻辑组件；一个逻辑资源可以跨多个物理位置。一个物理/container scope 也可以只是 topology endpoint，而不是逻辑资源。禁止为了让 edge 可解析而伪造 Workspace，也禁止 whole-folder heuristic。

Source 身份、Source 来源关系、机器本地 Location、受控开发 Workspace 和 Runtime Deployment 必须分别记录。路径相同/相似、目录名相同、同一上游代码族，均不能自动证明它们是同一 logical subject。

### 3.1 Persistent source reuse is compatible with isolation

Persistent controlled Source/Workspace 与 transient Task Workspace 是不同 lifecycle role，可以同时存在：

```text
persistent controlled source
-> fetch refs/objects
-> exact frozen Task baseline
-> transient isolated worktree
```

Persistent source 的长期复用不允许把 transient worktree、verifier scratch 或客户端 Project Host 自动提升为新的 persistent Workspace。反过来，clean-room verifier 使用 disposable exact-SHA workspace 也不意味着普通 Task 必须 repeated clone。

Runtime Deployment 继续与 Source/Workspace 分离。受保护 Deployment 不得为了匹配 Source HEAD 被 reset/clean/fetch-align；Deployment generation 更新也不默认复制 credentials/config/DB/State/logs 形成新的 Task-named full folder。

## 4. Authority model

只允许四个层次，但只有三个决策/授权权威：

```text
Facts
  Resource Registry / State-Data / Deployment / Evidence / Storage measurement
        ↓
Frozen Control Snapshot
        ↓
Canonical Evaluator Result
  LPRL_VALIDATION_RESULT.yaml
        ↓
Technical eligibility
  Gate Bundle
        ↓
Action authorization
  Retirement Manifest / Controlled Migration batch
        ↓
Reconciliation closeout
```

`LPRL_VALIDATION_RESULT` 是机器关系校验的唯一输出合同，但**不是新的 action authority**。它只证明某个 subject 在指定 frozen snapshot、exact scope 和 ruleset 下是否满足规则。

不得复制同一 verdict 到多个 artifact 作为独立权威。

Source provenance、Location operational role、deployment definition 和 equality observation 都属于 Facts；它们不能自动提升 reconstructability、lifecycle、Gate 或 action authorization。

## 5. Canonical evaluator contract

所有机器判定使用：

- `modules/local-resource-lifecycle/templates/LPRL_VALIDATION_RULES.yaml`；
- `modules/local-resource-lifecycle/templates/LPRL_VALIDATION_RESULT.yaml`。

Validation Result 必须输出：

- subject ref + decision-input digest；
- frozen snapshot ref/digest；
- resolved resource/component/exact-target set；
- topology edge set；
- protected/shared-owner closure；
- Storage/State/Data/Deployment/Evidence applicable refs；
- per-rule PASS/BLOCKED/FAIL/NOT_APPLICABLE；
- missing/extra refs；
- reference graph + cycle result；
- explicit residual human decisions；
- overall PASS/BLOCKED/FAIL。

`PASS` 只在 scope closure、same snapshot、acyclic graph、全部 required rules 及 human-decision closure 同时满足时有效。

## 5.1 Canonical structured digest profile

LPRL structured artifacts use the named deterministic profile `lprl-cjson-v1`.
The protocol, rather than a Python implementation, is authoritative:

1. Parse source YAML with a safe parser into a JSON-compatible value model and
   reject duplicate mapping keys before projection.
2. Mapping keys in a digest projection are strings. Allowed scalar values are
   exactly `null`, boolean, integer and string. Reject custom YAML tags,
   timestamp/date objects, binary, set, NaN, Infinity and all floating-point
   values. A future profile may define another numeric contract; this profile
   does not coerce one.
3. A projection removes excluded paths; it never replaces them with `null`.
   Paths use dot notation, `[*]` for every array element, and `$` for the
   complete parsed record.
4. Canonical bytes are UTF-8 bytes of compact JSON with mapping keys sorted,
   Unicode preserved without normalization, separators `,` and `:`, and
   `allow_nan=false` semantics. No trailing newline is added.
5. Arrays preserve authored semantic order. They are not sorted unless a
   schema later defines that particular field as order-insensitive.
6. SHA-256 over those bytes is encoded as lowercase 64-character hexadecimal.
   A digest-bearing field is excluded from its own projection.
7. Comments, indentation, line endings, whitespace and mapping-key order in
   source YAML do not change the digest when the parsed projected value is the
   same.

The equivalent reference encoding is:

```python
json.dumps(projected_value, sort_keys=True, ensure_ascii=False,
           separators=(",", ":"), allow_nan=False).encode("utf-8")
```

### 5.2 Normative named projections

Every authority-bearing digest uses exactly one projection below. `include`
lists the complete field paths retained from the parsed record; `exclude`
lists paths removed before encoding. A projection marked `$` retains the
complete current record except for its explicitly listed exclusions.

| Projection | Include | Exclude | Output field |
|---|---|---|---|
| `topology_inventory` | `topology_inventory.*` | `topology_inventory.inventory_digest` | `registry.topology_inventory.inventory_digest` |
| `registry_facts` | `schema_version`, `project_id`, `topology_inventory.*`, `physical_containers`, `resources[*].*`, `topology_edges` | `digests`, `registry_status`, `last_verified`, `verification_basis`, `resources[*].lifecycle_status`, `resources[*].accepted_gate_bundle_ref`, `topology_inventory.inventory_digest` | `registry.digests.fact_digest` |
| `registry_full_record` | `$` | `digests.full_record_digest` | `registry.digests.full_record_digest` |
| `state_data_manifest` | `$` | `manifest_digest` | `manifest_digest` |
| `deployment_manifest` | `$` | `manifest_digest` | `manifest_digest` |
| `evidence_facts` | `$` | `manifest_digest`, `status`, `acceptance` | `evidence_manifest.manifest_digest` |
| `storage_measurement` | `schema_version`, `ledger_id`, `measurement.*`, `objects`, `measurement_summary` | `measurement.measurement_digest`, `ledger_status`, `derived_reclaimable`, `validation`, `rules` | `measurement.measurement_digest` |
| `storage_derivation_inputs` | `schema_version`, `ledger_id`, `measurement.measurement_digest`, `derived_reclaimable.control_snapshot_ref`, `derived_reclaimable.control_snapshot_digest`, `derived_reclaimable.gate_bundle_refs`, `derived_reclaimable.contributing_storage_object_ids`, `derived_reclaimable.currently_safe_reclaimable_bytes`, `derived_reclaimable.derivation_ref` | `derived_reclaimable.derivation_digest`, `derived_reclaimable.derived_at` | `storage_ledger.derived_reclaimable.derivation_digest` |
| `control_snapshot_inputs` | `schema_version`, `snapshot_id`, `governance`, `scope`, `topology_inventory_ref`, `topology_inventory_digest`, `bound_inputs`, `fact_window`, `drift_policy` | `status`, `created_at`, `frozen_at`, `frozen_by_role`, `freeze`, `invalidated_reason`, `supersedes_snapshot_ref`, `notes` | `freeze.snapshot_digest` |
| `gate_validation_inputs` | `schema_version`, `control_snapshot_ref`, `control_snapshot_digest`, `resource_ids`, `component_ids`, `exact_physical_target_refs`, `checks`, `required_checks`, `blockers` | `gate_bundle_id`, `validation_input_digest`, `status`, `validation_rules_ref`, `validation_result_ref`, `accepted_by_role`, `accepted_at`, `gate_bundle_digest` | `gate_bundle.validation_input_digest` |
| `gate_full_record` | `$` | `gate_bundle_digest` | `gate_bundle.gate_bundle_digest` |
| `validation_result` | `$` | `result_digest` | `validation_result.result_digest` |
| `retirement_validation_inputs` | `schema_version`, `retirement_id`, `status`, `control_snapshot_ref`, `control_snapshot_digest`, `resource_ids`, `component_ids`, `exact_physical_target_refs`, `technical_gate_bundle_ref`, `evidence_manifest_refs`, `storage_ledger_ref`, `physical_storage_impact`, `owner_summary`, `authorization`, `holds`, `restore`, `buffer`, `purge`, `validation.rules_ref`, `blockers`, `notes` | `retirement_manifest_digest`, `validation_input_digest`, `validation.validation_result_ref` | `retirement_manifest.validation_input_digest` |
| `retirement_full_record` | `$` | `retirement_manifest_digest` | `retirement_manifest.retirement_manifest_digest` |
| `migration_batch_validation_inputs` | `batch_id`, `status`, `control_snapshot_ref`, `control_snapshot_digest`, `retirement_manifest_ref`, `resource_ids`, `component_ids`, `exact_targets`, `authorization_refs`, `expected_mutations`, `expected_storage_effect_ref`, `abort_conditions`, `restore_procedure_ref`, `post_verification_checks`, `pre_action_revalidation` | `validation_input_digest`, `validation_result_ref`, `post_action` | embedded batch `validation_input_digest` |
| `reconciliation_validation_inputs` | `schema_version`, `reconciliation_id`, `trigger`, `trigger_ref`, `recorded_at`, `recorded_by_role`, `resources_touched`, `transient_workspaces`, `caches`, `evidence_closure`, `storage_delta`, `recurring_growth`, `status`, `completion_semantics`, `notes` | `validation_input_digest`, `validation_result_ref`, `accepted_by_role` | `reconciliation.validation_input_digest` |

The Registry fact projection intentionally excludes topology inventory's own
digest because that digest is independently bound by `topology_inventory`.
The Evidence projection is `evidence_facts`, not `full_manifest`: excluding
`status` and the complete `acceptance` object breaks the cycle between
`manifest_digest` and `acceptance.validation_result_ref`. Evidence acceptance
is a later validated state and never rewrites the facts digest consumed by a
Snapshot. Gate decision-input status means each `checks[*].status`; the
top-level Gate `status` is derived and excluded. Migration batch `status` is
included because `MIGRATION_BATCH_READY` validates readiness itself.

### 5.3 Digest field inventory and non-authority hashes

The current authority-bearing fields map one-to-one to the named projections:

```text
registry.topology_inventory.inventory_digest -> topology_inventory
registry.digests.fact_digest -> registry_facts
registry.digests.full_record_digest -> registry_full_record
state_data_manifest.manifest_digest -> state_data_manifest
deployment_manifest.manifest_digest -> deployment_manifest
evidence_manifest.manifest_digest -> evidence_facts
storage_ledger.measurement.measurement_digest -> storage_measurement
storage_ledger.derived_reclaimable.derivation_digest -> storage_derivation_inputs
control_snapshot.freeze.snapshot_digest -> control_snapshot_inputs
gate_bundle.validation_input_digest -> gate_validation_inputs
gate_bundle.gate_bundle_digest -> gate_full_record
validation_result.result_digest -> validation_result
retirement_manifest.validation_input_digest -> retirement_validation_inputs
retirement_manifest.retirement_manifest_digest -> retirement_full_record
migration_batch.validation_input_digest -> migration_batch_validation_inputs
reconciliation.validation_input_digest -> reconciliation_validation_inputs
```

`source_identity.artifact_digest`, evidence `local_artifacts[*].hash`, and
Registry `equality_observations[*].digest` are informational artifact hashes,
not LPRL structured decision authority. Storage
`derived_reclaimable.derivation_digest` is the authority digest for the
`storage_derivation_inputs` projection, separate from the measurement facts
digest. Snapshot/Gate/Retirement
`*_digest` references and revalidation observed digests are equality references
to the corresponding authority field, not additional digest constructions.
Their external construction must be recorded as provenance and cannot replace
the named projections above.

## 6. Resource Registry and topology inventory

Controlled Migration 前必须建立项目本地 Resource Registry。Registry 保存事实，不保存独立 retirement authorization。

Registry 必须包含 canonical `topology_inventory`：

```text
inventory_id
observed_at
discovery scope
discovery methods
edge_ids
protected/shared owner refs
coverage_complete
unresolved_regions
inventory_digest
```

Registry 还必须允许声明非逻辑资源的 physical/container scopes，使 topology edge 的 `from_ref` / `to_ref` 能解析到：

```text
resource
component
physical location
physical/container scope
```

container endpoint 本身不因此成为 Workspace/Source/Deployment logical resource。

### 6.1 Scoped topology completeness for Gate evaluation

`discovery_scope_resource_ids` 与 `discovery_scope_component_ids` 是
`coverage_complete` 的 topology discovery seed/scope。它们定义本次
Registry Facts 要证明的边界；声明的 scope 不是隐含的 whole-project assertion，
除非声明的 scope 本身就是 whole project。

`coverage_complete: true` 只有在该声明 scope 的 discovery 完整，并且所有从
该 scope 可达、会影响 mutation side effects 的 topology edge 与
protected/shared-owner endpoint 都已解析并闭合时才有效。有效的 complete
inventory 必须同时有 `unresolved_regions: []`。`edge_ids` 是该声明 scope
的完整比较集；Registry 可以包含 scope 外资源或边，但无关的 out-of-scope
edge 不会仅因存在于 Registry 就成为 Gate topology 输入。

Writer custody、Source unique value、State/Data recovery/retention/rollback、
runtime Deployment、Evidence acceptance 与 storage measurement 是独立的
Facts/Gate 维度。它们只有在实际阻止 topology edge 或 owner discovery 时才
使 topology coverage incomplete；否则仍由各自规则 fail-closed，而不是被
作为 topology unresolved region 代入。

Gate/Snapshot scope 中的每个 resource、component 和 exact target 必须分别
落在 discovery scope，并对所有 applicable touching/reachable edge 与
protected/shared-owner closure 做集合相等校验；prose-only 的完整性声明不构成
证明。`coverage_complete: false` 的 Registry 仍使 topology Gate BLOCKED。

### 6.2 Snapshot-bound topology facts

Snapshot 可以冻结一个精确 scoped Facts 集，即使当时 topology coverage 尚未
完整；这只记录决策输入，不表示 technical eligibility。Gate topology PASS
更严格：Snapshot 绑定的 Registry topology facts 必须对 Gate 声明的 discovery
scope 给出 complete discovery。若 Snapshot 绑定了 `coverage_complete: false`，
该 Snapshot 下 Gate 必须 BLOCKED；之后发现的新 topology 不能作为未绑定的
side proof 注入。必须刷新 Registry Facts/digests，并冻结新的 Snapshot。

这保留 `one_frozen_snapshot_per_decision_chain`、
`same_scope_must_be_proven_not_assumed` 与 `stale snapshot != valid authorization`。

`all relevant edges checked` 这种 prose 声明不是证明。Topology Gate 只能基于 canonical inventory 做集合闭包比较；missing/extra edge 或 owner authorization 必须机器可见。

### 6.3 Source provenance, deployment definitions, equality observations

Source 的 `source_identity` 与 `source_provenance` 分开：

- identity：当前记录的 repository/store/commit/tree/artifact subject；
- provenance：它从哪个 origin 而来、与 origin 的关系（canonical/upstream/fork/mirror/vendor/deployment-copy/generated/unknown）。

`controlled_project_source` 只能说明项目是否把该 Source 当作受控开发来源，不能单独证明 reconstructability、retirable 或 action authority。

Source/config 的 deployment definition 必须能结构化保存，但：

```text
deployment definition present
!=
runtime Deployment observed
```

只有独立观察到 runtime subject 后才允许创建 Deployment Manifest；Runtime Deployment 可引用其 definition facts，但不得反向用 definition 推断 runtime 存在。

Equality-only hash 必须以 `equality_check_only` 语义记录。它只能证明被比较 refs 在该观察下相等，不能代替 `artifact_digest` provenance、Evidence acceptance、Source unique-value proof、reconstructability、lifecycle 或 action authority。

## 7. Source unique-value proof

Source/Workspace 退役前逐项检查 tracked、staged/uncommitted、untracked、ignored、local refs、unpushed commits、non-Git content 与 unresolved unique Source/Data/Evidence。

任一维度未检查或 unresolved count 非 0，Gate BLOCKED。

Source provenance 或 equality observation 不能替代该 proof。

## 8. Writer/quiescence

Writer PASS 必须针对**同一个 scoped resource/component/target set**解析 writer custody proof，并要求 CLEAR + observation + revalidation + fencing。`NOT_APPLICABLE` 必须有 exact-scope 证明。

不能拿资源 A 的 CLEAR proof 给资源 B 通过 Gate。

## 9. State / Data

State/Data Manifest 保存 owner/custodian、unique-copy、physical locations、consumers/bindings、version、recovery、retention、migration、rollback 与 retirement policy facts。

`STATE_DATA_GATE_PASS` 必须：

- 解析 exact applicable manifest set；
- 拒绝 UNKNOWN unique-copy/rollback；
- recovery required 时要求 verified backup + procedure；
- 审核 retention/audit hold；
- 禁止 exact target 隐式删除 protected/unique State/Data；
- 如 State/Data 自身要退休，必须在后续 Retirement action authority 中另有明确授权。

## 10. Deployment

Deployment identity 独立于 Task/目录名，至少记录 deployment_id / slot / generation_id / Source identity / State bindings / health / previous generation / rollback facts。

Source/config deployment-definition metadata 属于 Source Facts，而不是 runtime Deployment。Deployment Manifest 只能代表已观察到的 runtime Deployment subject；可引用 Registry 的 deployment-definition refs 作为声明来源，但 definition 不得创建 runtime identity。

`DEPLOYMENT_ROLLBACK_GATE_PASS` 必须：

- 解析 exact applicable deployment set；
- 禁止 required-current deployment 进入 retirement target；
- required-previous 必须保留或有 validated replacement；
- State bindings 与 rollback compatibility 不得 UNKNOWN/BLOCKED；
- 需要 rollback 时必须有 procedure。

稳定 Deployment slot（例如 `live/canary/staging`）与 generation 比 Task-named runtime folder 更符合该模型。代码 Source generation 变化本身不授权复制/迁移 State/Data/credentials/config/logs，也不授权把现有 protected Runtime 当成普通 Git Workspace 更新。

## 11. Evidence

Evidence `accepted` 只有在 completeness、unresolved-items、Lead acceptance、
`evidence_facts` manifest digest 和 canonical validation result 全部满足时
有效。Evidence 是事实/provenance，不是 retirement authority；acceptance
metadata 不进入 `evidence_facts`。

Equality observation 本身不是 Evidence acceptance，也不因存在 digest 而自动获得 provenance authority。

## 12. Storage Ledger

Storage Ledger 分离 apparent / exclusive physical / shared physical bytes。它还必须把 `measurement_basis` 与 `measurement_confidence` 分离记录：

```text
measurement_basis: apparent_only | exclusive_physical | mixed | unknown
measurement_confidence: unknown | low | medium | high | verified
```

`apparent_only` 可以是高一致性的目录表观测量，但仍不能因此被解释为 exclusive/shared physical bytes；basis 与 confidence 互不替代。

Control Snapshot 只绑定 measurement digest，不绑定 post-Gate derived reclaimable fields。

Storage measurement validation and storage derivation validation are separate:
`measurement_validation_result_ref` validates the measurement facts, while
`derivation_validation_result_ref` validates the derived reclaimable decision
under `storage_derivation_inputs`. The latter digest binds the snapshot,
Gate Bundle refs, contributing object set, and derived safe-reclaimable value;
post-validation linkage and timestamps do not rewrite it.

Safe reclaimable 只能由规则派生，并且 contributing storage-object set 必须与 evaluator resolved scope 一致。共享字节只有所有 scoped owners 在同一 snapshot 下可释放才计入。仅 `apparent_only` basis 不得产生 safe reclaimable bytes。

## 13. Frozen Control Snapshot

Control Snapshot 必须有非空 resource scope，并解析 component/exact target、shared-owner dependencies、canonical topology inventory，以及所有 applicable fact inputs。

Freeze 前必须通过：

- digest scope；
- scope closure；
- topology inventory closure；
- unresolved blockers empty。

这里的 `topology_inventory_validated` 表示 inventory ref、digest、声明 scope
及其引用闭包已被绑定和校验，不等同于 `coverage_complete: true`。因此，若
Facts 没有其他 unresolved blocker，Snapshot 可以记录一个
`coverage_complete: false` 的精确 scoped Facts 集；这不构成 topology Gate
eligibility，Gate 必须在 `TOPOLOGY_SCOPE_CLOSURE` 中 BLOCKED。

任一 bound fact/topology/source/writer/state-data/dependency drift 使 snapshot invalid。

## 14. Gate Bundle

Gate Bundle 只承担 technical eligibility。它的 `status: PASS` 只有 `GATE_BUNDLE_PASS` 能使其有效。

Gate 的 validation-input digest 不包含 derived status、validation_result_ref 或 acceptance metadata，以避免 evaluator/result 循环。

Gate PASS 要求：

- same snapshot；
- exact scope closure；
- canonical evaluator PASS；
- required checks 全部 PASS 或有 proof 的 NOT_APPLICABLE；
- State/Data 与 Deployment 专用规则 PASS；
- blockers empty；
- Lead acceptance metadata。

## 15. Reference graph and cycle rejection

规则定义 canonical forward dataflow。Validation Result 必须枚举实际 ref graph 并执行 cycle check。

任何 authority/dataflow cycle BLOCKED，例如：

```text
Gate verdict -> Registry fact digest -> Snapshot -> Gate verdict
Retirement authorization -> Gate input facts -> Retirement authorization
Reconciliation -> earlier action authorization -> Reconciliation
```

非 authority evidence backlink 可以存在，但必须声明 relation，不能改变上游事实或授权。

## 16. Retirement Manifest

Retirement 是 action authority。它必须绑定同一 frozen snapshot、same exact target set、Gate/Evidence/Storage、owner-visible consequence、holds、restore 和 action authorizations。

状态机是 machine-gated：

- `approved`：buffer-entry holds clear；
- `buffered`：还必须有 `_delete` ref + entered_at + inventory hash；
- `purge_authorized`：还必须有 purge approval + buffer evidence；
- `purged`：还必须有 completed_at + purge record。

protected/shared-owner authorization set 必须精确覆盖 evaluator resolved owner set。

## 17. Reconciliation is a hard completion gate for LPRL lifecycle actions

进入 LPRL retirement/validation/migration action chain 的 lifecycle task、LPRL validation 或 migration batch，收尾必须形成 Reconciliation。

`held` 只表示**未完成、等待处理**。它不能满足 LPRL lifecycle task complete、migration verified 或 rolled_back 的 finalization semantics。

缺少 complete Reconciliation：该 LPRL lifecycle action `BLOCKED`，不是 warning。

这条规则**不把所有普通开发 Task 或已预先证明为 disposable 的 scratch/worktree 自动升级为完整 LPRL action chain**。普通 Task 的 durable completion 使用 Task/Result/Lead Acceptance；只有资源生命周期风险需要 LPRL retirement authority 时才进入本节。

## 18. Controlled Migration

真实本地变化是独立高风险阶段。每个 batch 必须绑定 frozen snapshot + approved/buffered Retirement Manifest + exact targets + authorizations + pre-action revalidation + restore + abort conditions。

Mutation 前任一 drift：`ABORT_AND_REEVALUATE`。

`verified` 或 `rolled_back` 只有 complete Reconciliation 后才是最终状态。

## 19. Owner operability

Owner report 只展示：必须保留、当前活动、待技术判定、原则候选未授权、可安全释放、已进入 buffer 等待 purge。

Owner 不判断 Git/topology/State/Data/Deployment/digest/evaluator 技术安全性。

## 20. Default reclaim priority

技术 Gate 与 action authorization 全通过后，默认优先：

```text
Cache -> retired/retirable transient Workspace -> old Deployment generations -> proven-reconstructable generated Data
```

不得自动清理 active State、non-reconstructable Data、current Deployment、active Workspace、unresolved Evidence、protected/held resources。

### 20.1 Ordinary housekeeping fast path

为了避免对明确 disposable 资源过度设计，以下对象可以在**现有 project/local policy 已预声明 cleanup authority**时走 ordinary bounded housekeeping，而不创建 Snapshot/Gate/Retirement/Reconciliation artifact：

- 明确 `task_execution_only` / transient 且其 Task durable handoff/evidence 已关闭的 worktree/scratch；
- 正面证明可重建、非 authority、无 unique value 的 Cache/build output。

同时必须全部已知为真：

```text
exact target known
no unique Source/Data/Evidence
no protected/shared/runtime binding
no active writer
no active Task dependency
cleanup within predeclared local policy
```

任一字段 UNKNOWN，或对象属于 persistent Workspace、State、Data、Deployment、protected/shared resource，则 fast path 不适用，回到完整 LPRL retirement/Controlled Migration。

```text
old != deletable
untracked != deletable
ignored != deletable
Task-named != disposable by name
```

## 21. Replay requirement

A representative/project-local Facts materialization replay may be required before an applicable LPRL adoption or repin. It must remain identity-neutral and prove:

- a non-resource container endpoint can be machine-resolved without fabricating a logical Workspace;
- deployment-definition facts remain distinct from runtime Deployment;
- `measurement_basis: apparent_only` remains distinct from measurement confidence;
- an equality-check-only hash does not become artifact/provenance authority;
- upstream-derived deployed/reference Source and controlled-fork Workspace remain separately representable.

A replay PASS may support later explicit LPRL adoption/repin or a separate materialization Task. It does not authorize local-file creation, Snapshot/Gate/Retirement, cleanup, migration or reclamation.

Later Controlled Migration still requires replay against applicable frozen evidence. An older replay cannot automatically validate a materially changed candidate.

A factual payload may be carried forward only when Facts meaning/schema remains unchanged and applicable `lprl-cjson-v1` digest preparation/revalidation succeeds. Carry-forward must not turn UNKNOWN/BLOCKED facts into PASS or authorize lifecycle action.
