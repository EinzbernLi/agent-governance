# LPRL Paper Pilot Contract

版本：0.2.2-pilot  
状态：Template

## 1. Metadata

```yaml
pilot_id: "LPRL-PILOT-000"
mode: paper_migration
risk_level: medium
lead_controller: null

# Optional generic project/governance context. Omit or set this block to null
# for standalone/base operation; absence must not block the Paper Pilot solely
# because Core context is missing. If supplied, repository and revision must
# be exact/auditable in the surrounding project context. This field never
# implies or auto-loads Core Governance.
governance_ref:
  repository: "<governance-repository>"
  revision: "<exact-commit>"

project_ref:
  repository: "<project-repository>"
  # Optional generic project governance-lock context. Omit or set null for
  # standalone/base operation; if supplied, it must be exact/auditable in the
  # project context and must not trigger automatic Core Governance loading.
  project_governance_lock: "<project-governance-lock-ref>"

frozen_project_snapshot_ref: null
```

## 2. Hard Safety Boundary

Paper Pilot 必须非破坏性。禁止移动、重命名、删除、purge、`_delete` 写入、Git/worktree topology mutation、Source/Deployment/State/Data/config/credential/runtime mutation、permission/ownership mutation，以及根据目录名/Task ID/年龄/Temp 位置推断可退役。

允许：读取项目事实源与安全的只读 inventory/Git/topology/size/runtime identity；形成 Project Snapshot、Registry/Manifest/Storage/Control Snapshot 草案；运行关系 evaluator；把分析与验收 Evidence 写回项目事实源。

无法安全检查必须标记 `INSPECTION_BLOCKED`；writer 不明确必须标记 `WRITER_INCONCLUSIVE`。

## 3. Frozen Project Snapshot

至少包含 resource/path families、Source identities、dirty/untracked/ignored/unpushed 已知事实、Workspace/Deployment/State/Data/Evidence/Cache 线索、parent/shared topology、active dependencies、writer/activity signals、protection/hold rules、storage measurement coverage 与 blocked inspections。

## 4. Required Analysis

至少输出：

1. component-aware resource classification；
2. ambiguity / blocked-inspection register；
3. draft Resource Registry + canonical topology inventory；
4. topology edge/owner closure gaps；
5. writer/quiescence gaps；
6. structured Source unique-value proof gaps；
7. State/Data/rollback gaps；
8. Deployment rollback gaps；
9. Evidence Manifest gaps；
10. Storage Ledger gaps；
11. draft Control Snapshot scope/bindings/digests；
12. canonical `LPRL_VALIDATION_RESULT` showing resolved scope/targets/rule outcomes/ref-graph cycles；
13. paper migration plan；
14. retirable-in-principle candidates（非 RETIRABLE verdict）；
15. Reconciliation/recurring-growth gaps；
16. LPRL specification weaknesses；
17. non-technical Owner summary。

## 5. Matched Candidate Option

用于模型 calibration 时冻结相同 contract/Project Snapshot；候选提交前不得读取对方结果。执行通道无法提供隔离则 BLOCKED，不由 Lead 模拟缺失候选。

## 6. Validator Attack Surface

Validator 至少攻击：scope/target 错配、canonical topology inventory 漏边、protected/shared-owner authorization 漏覆盖、reference graph cycle、Gate PASS 无 evaluator PASS、State/Data/Deployment arbitrary proof-ref PASS、Reconciliation held 被误当完成、stale snapshot、Source unique-value 遗漏、writer 不明、Evidence completeness 冲突、Storage double count/manual override、`_delete` 提前进入、Owner 被迫技术判断。

## 7. Lead Acceptance

```yaml
pilot_verdict:
  resource_model: pass|revise|fail
  topology_model: pass|revise|fail
  lifecycle_model: pass|revise|fail
  workspace_model: pass|revise|fail
  deployment_model: pass|revise|fail
  state_data_model: pass|revise|fail
  evidence_model: pass|revise|fail
  storage_model: pass|revise|fail
  retirement_model: pass|revise|fail
  relational_validation: pass|revise|fail
  recurring_growth_control: pass|revise|fail
  user_operability: pass|revise|fail
  routing_test: pass|revise|fail|not_run
  ready_for_controlled_migration_protocol_test: true|false
```

必须明确 proven RETIRABLE set、safe reclaimable derivation、Control Snapshot validity、Evaluator result refs、accepted/rejected Validator findings、必须修订项，以及本 Pilot 无物理迁移/删除。

## 8. Stop Condition

Paper Pilot 终点是 Lead Acceptance。即使 PASS，也不得在同一 Pilot 内开始 Controlled Migration。
