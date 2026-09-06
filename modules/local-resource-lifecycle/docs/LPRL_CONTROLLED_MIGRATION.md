# LPRL Controlled Migration Protocol

版本：0.2.4-pilot
状态：Replay Candidate

## 1. Purpose

Controlled Migration 是 Paper Pilot / Replay 之后，对明确本地资源执行真实重组、retirement 或空间回收的独立高风险阶段。

Paper analysis、candidate envelope、目录名/年龄、retirable-in-principle 均不是 action authorization。

## 2. Entry Conditions

开始 Controlled Migration Protocol test 前必须全部满足：

- candidate exact revision 已冻结并通过 Replay Lead Acceptance；
- Project Resource Registry + canonical topology inventory 完整；
- applicable State/Data 与 Deployment manifests 完整；
- Evidence Manifest accepted；
- Storage measurement validated；
- frozen Control Snapshot 通过 scope/digest/topology closure；
- canonical Validation Result PASS；
- Gate Bundle 通过 `GATE_BUNDLE_PASS`；
- Retirement Manifest 在同一 snapshot/scope 下 approved；
- Owner report 已生成；
- Lead/Owner/protected-or-shared-owner action authorizations 已覆盖 evaluator resolved owner set。

任一 UNKNOWN/BLOCKED/FAIL/stale digest/scope mismatch/cycle/unresolved human decision：不得开始。

## 3. Prohibited Shortcuts

禁止：

- 目录名/Task ID 作为 deletion authority；
- untracked/ignored 自动视为 Cache；
- 先放 `_delete` 再判断；
- 先 mutate Git/worktree metadata 再补 topology；
- 改 permission/ownership 绕过 inspection block；
- apparent bytes 当 reclaimed bytes；
- 手填 safe reclaimable；
- 混用不同 snapshot/scope 的 Gate/Evidence/Storage/Retirement；
- 使用 held Reconciliation 声称 task/batch complete；
- 使用 non-null arbitrary proof_ref 代替 State/Data/Deployment/Topology machine validation。

## 4. Batch Model

```yaml
batch_id: "batch-000"
status: draft # draft|ready|executing|held|verified|rolled_back|blocked
validation_input_digest: null # lprl-cjson-v1 / migration_batch_validation_inputs
validation_result_ref: null

control_snapshot_ref: null
control_snapshot_digest: null
retirement_manifest_ref: null

resource_ids: []
component_ids: []
exact_targets: []
authorization_refs: []
expected_mutations: []
expected_storage_effect_ref: null
abort_conditions: []
restore_procedure_ref: null
post_verification_checks: []

pre_action_revalidation:
  status: UNKNOWN # PASS|BLOCKED|FAIL
  observed_snapshot_digest: null
  source_revalidation_ref: null
  writer_revalidation_ref: null
  topology_revalidation_ref: null
  state_data_revalidation_ref: null
  dependency_revalidation_ref: null

post_action:
  verification_ref: null
  after_storage_ledger_ref: null
  reconciliation_record_ref: null
```

Batch `validation_input_digest` uses the named `lprl-cjson-v1` projection
`migration_batch_validation_inputs`: it includes the pre-action decision state,
including `status` because `MIGRATION_BATCH_READY` validates readiness, and
excludes `validation_input_digest`, `validation_result_ref`, and the complete
post-action outcome object. No digest is constructed from post-action fields
before the mutation decision.

`MIGRATION_BATCH_READY` 要求 batch exact targets 与 Retirement exact target set 相等，且 evaluator PASS。

## 5. Pre-action Revalidation

每个 mutation 紧邻执行前重新确认：writer/activity、Source unique-value、canonical topology inventory、State/Data bindings、Deployment rollback capacity、active dependencies、Evidence/Storage/Retirement refs、authorizations 和 restore path 均未 drift。

`observed_snapshot_digest` 必须等于 batch `control_snapshot_digest`。

任何变化：

```text
ABORT_AND_REEVALUATE
```

不能原地改字段继续执行；必须重新形成事实记录，必要时新 Snapshot/Gate/Retirement authorization。

## 6. Protected / Shared Topology

Evaluator 必须从 canonical topology inventory 计算 exact applicable edge set 和 protected/shared-owner closure。

Retirement/Migration authorization 必须覆盖这个 owner set；child retirement 不自动授权 parent metadata/shared object mutation。

任何 missing/extra edge 或 authorization：BLOCKED。

## 7. Retirement Buffer and Purge

进入 `_delete` 必须满足 Retirement `status: buffered` 的状态不变量：approved technical/action chain + holds clear + `_delete` ref + entered_at + inventory hash。

Purge 必须单独满足 purge authorization；`purged` 还必须有 completed_at + purge record。

`_delete` 不是长期 archive，也不是“待技术判断”区域。

## 8. Storage Reporting

每批只报告重新测量并由规则派生的 actual exclusive bytes、shared bytes、unknown bytes 和 remaining buffer bytes。禁止把删除前 apparent directory size 宣称为实际释放空间。

## 9. Post-action Verification

每 batch 后验证：exact target 变化正确、non-target unchanged、protected/shared topology 无越权变化、active Deployment/State/Data 健康、Source provenance 可追踪、Registry/Manifest refs 更新、storage remeasurement 完成、Owner Report 更新。

验证失败必须进入 held/rollback/block 路径，不能继续下一 batch。

## 10. Reconciliation Finalization Gate

每个 task/validation/batch 必须有 `LPRL_RECONCILIATION.yaml`。

- `status: held` = 未完成；
- `status: complete` + `RECONCILIATION_COMPLETE PASS` 才能满足 finalization；
- batch `verified` 或 `rolled_back` 若缺 complete reconciliation，`RECONCILIATION_REQUIRED` 必须 BLOCK。

## 11. Completion

Lead Controller 最终验收：retired/protected/held/unknown set、abort/restore、actual released bytes、buffer/purge state、Registry/Topology/Manifest/Snapshot/Validation Result consistency、Reconciliation complete 和下一轮 candidates。

Controlled Migration Task 只授权其列出的 exact batch；不得外推为全项目清理授权。
