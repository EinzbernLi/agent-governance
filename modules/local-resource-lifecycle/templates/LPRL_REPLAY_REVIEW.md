# LPRL Replay Review

版本：0.2.2-pilot  
状态：Template

## 1. Purpose

Replay 使用冻结的历史 Paper Pilot evidence 验证新版 LPRL。Replay 不重新检查项目本地磁盘，不更新 Project Snapshot，不执行任何 migration/cleanup/permission change。

## 2. Inputs

```yaml
replay_id: "LPRL-REPLAY-000"
governance_ref: "<exact LPRL candidate commit>"
source_pilot_ref: "<project pilot ref>"
frozen_project_snapshot_ref: "<exact snapshot ref>"
prior_lead_acceptance_ref: "<exact acceptance ref>"
validator_findings_ref: "<exact validator ref>"
prior_replay_acceptance_ref: null
```

## 3. Required Schema Coverage

Validator 至少检查：

- `LPRL_CONTROL_SNAPSHOT.yaml`
- `LPRL_VALIDATION_RULES.yaml`
- `LPRL_VALIDATION_RESULT.yaml`
- `LPRL_RESOURCE_REGISTRY.yaml`
- `LPRL_STATE_DATA_MANIFEST.yaml`
- `LPRL_DEPLOYMENT_MANIFEST.yaml`
- `LPRL_EVIDENCE_MANIFEST.yaml`
- `LPRL_STORAGE_LEDGER.yaml`
- `LPRL_GATE_BUNDLE.yaml`
- `LPRL_RETIREMENT_MANIFEST.yaml`
- `LPRL_RECONCILIATION.yaml`
- `LPRL_OWNER_REPORT.md`
- `LPRL_CONTROLLED_MIGRATION.md`

## 4. Core Adversarial Tests

确认 Validation Rules 会 BLOCK：

1. Gate PASS + snapshot digest mismatch；
2. Registry RETIRABLE + no Gate passing GATE_BUNDLE_PASS；
3. Source PASS + any discovery dimension unchecked；
4. Writer PASS + proof belongs to a different resource/component/target scope；
5. Writer PASS + no observation/revalidation/fencing；
6. Evidence accepted + completeness false or unresolved items；
7. safe reclaimable > 0 + contributing resource not RETIRABLE；
8. shared bytes counted while one scoped owner is held/protected；
9. Retirement approved + stale snapshot；
10. Migration ready + pre-action drift；
11. task complete / batch verified / rolled_back + reconciliation missing；
12. held reconciliation used to satisfy completion；
13. Registry derived lifecycle/Gate ref changes fact_digest；
14. Storage derived reclaimable changes measurement_digest；
15. Gate stores protected-parent action authorization；
16. Retirement affects protected/shared owner but authorization set is missing or extra relative to evaluator owner closure。

## 4.1 v0.2.5-pilot Scoped Topology Conformance Cases

以下 cases 专门验证 scoped topology completeness；它们不改变其他
Facts/Gate 维度的独立 fail-closed 规则。

### PASS candidate: complete declared scope with unrelated unknowns

Registry 含有声明 topology discovery scope 之外的资源，其 writer、State、
runtime 或 storage facts 仍为 UNKNOWN。声明 scope 内的 Gate resource/component
集合完整，所有 touching/reachable edges 与 protected/shared-owner closure
均已表示，`unresolved_regions: []` 且 `coverage_complete: true`。在其他 Gate
条件未满足时，`TOPOLOGY_SCOPE_CLOSURE` 可以 PASS，但其他对应规则仍必须
独立 BLOCKED。

### BLOCK: scoped resource omitted

Gate/Snapshot scoped `resource_id` 不在
`discovery_scope_resource_ids` 中 -> `TOPOLOGY_SCOPE_CLOSURE` BLOCKED。

### BLOCK: scoped component omitted

Gate/Snapshot scoped `component_id` 不在
`discovery_scope_component_ids` 中 -> BLOCKED。

### BLOCK: missing touching edge or reachable owner

Gate scope 可达的 applicable touching edge，或该 edge 可达的
protected/shared-owner endpoint，未出现在 inventory/resolved closure ->
BLOCKED；missing/extra edge 与 owner refs 必须机器可见。

### BLOCK: false completeness

`coverage_complete: true` 但 `unresolved_regions` 非空 -> BLOCKED。

### BLOCK: incomplete inventory

`coverage_complete: false` 即使当前 ad-hoc evidence 看不到 drift，Gate
topology 仍 BLOCKED；不能由 worker 判断 unresolved region “无关”而放行。

### BLOCK: post-Snapshot refresh

Snapshot A 绑定 `coverage_complete: false` 的 Registry digest；Registry 后续
变为 complete。Snapshot A 下 Gate 仍 invalid/BLOCKED。必须刷新 Registry Facts
与受影响 digests，再冻结新的 Snapshot B；后续 topology 观察不能作为 unbound
side proof 注入 Snapshot A。

### Separation case: unrelated lifecycle unknowns

声明 topology discovery scope 之外的 writer/State/runtime/storage UNKNOWN，若
没有阻止 edge/owner discovery，不得单独把 topology `coverage_complete` 变为
false；这些 UNKNOWN 仍由各自 Gate 规则处理。

## 5. v6 Finding Closure Tests

### V6-F01 Scope closure

Construct and require BLOCK for:

- Gate scope B using Writer/Source/Topology proof from A；
- Snapshot resource/component target set not equal to evaluator resolved scope；
- Retirement exact target B consuming Gate/Storage derivation for A；
- Migration exact targets not equal to Retirement exact targets；
- bound input with out-of-scope target not declared shared-owner dependency。

Require evaluator output to enumerate the exact resolved target set and missing/extra refs.

### V6-F02 Reconciliation closure

Construct:

- task status complete + null reconciliation ref；
- migration verified/rolled_back + reconciliation status held；
- reconciliation complete + evaluator not PASS。

All must BLOCK finalization. `held` must remain explicitly non-complete.

### V6-F03 Topology / authorization evaluability

Construct:

- Registry topology inventory `coverage_complete: false` but Git topology PASS；
- an edge touching scoped target omitted from evaluator resolved edge set；
- missing protected/shared owner；
- extra unrelated owner authorization used to conceal incomplete closure。

Require missing/extra edge and owner sets to be machine-visible and BLOCK.

### V6-F04 Cycle / evaluator contract

Construct ref graphs containing:

- Gate -> Registry fact digest -> Snapshot -> Gate；
- Retirement -> Gate input facts -> Retirement；
- Reconciliation -> earlier authorization -> Reconciliation。

All authority/dataflow cycles must BLOCK. Also verify every machine PASS uses the versioned `LPRL_VALIDATION_RESULT` schema and unresolved human decisions prevent PASS.

### V6-F05 State/Data and Deployment Gate detail

Construct:

- state_data PASS with arbitrary non-null proof_ref but UNKNOWN unique-copy；
- required recovery with backup_verified false；
- audit-held protected State/Data exact target without later action authorization；
- deployment PASS while required_current target is selected；
- required_previous rollback generation neither preserved nor replaced；
- rollback compatibility UNKNOWN/BLOCKED or blockers nonempty。

All must BLOCK.

## 6. Prior Strength Regression Tests

Confirm retained behavior for lifecycle fail-closed, Source unique-value proof, Evidence completeness, Storage measurement/derived separation, State/Data vs Deployment identity separation, Owner operability, protected-parent action separation and recurring-growth controls.

## 7. Complexity / Authority Review

Validator must explicitly answer:

- Is there exactly one machine evaluator output schema?
- Does Validation Result add technical evidence only, without becoming action authority?
- Are scope/topology/cycle rules centralized rather than duplicated across artifacts?
- Can any prose-only assertion make a machine PASS without corresponding rule/result fields?
- Is any new field a duplicate decision authority rather than a fact, digest or evidence pointer?

## 8. Required Output

```yaml
replay_verdict:
  overall: pass|revise|fail
  registry_and_topology: pass|revise|fail
  lifecycle_fail_closed: pass|revise|fail
  source_unique_value_gate: pass|revise|fail
  writer_quiescence_gate: pass|revise|fail
  git_topology_gate: pass|revise|fail
  state_data_rollback: pass|revise|fail
  evidence_manifest: pass|revise|fail
  storage_accounting: pass|revise|fail
  retirement_buffer: pass|revise|fail
  relational_validation: pass|revise|fail
  owner_operability: pass|revise|fail
  recurring_growth_control: pass|revise|fail
  controlled_migration_protocol: pass|revise|fail
  ready_for_controlled_migration_protocol_test: true|false
```

Also list material findings, resolved v6 findings, residual human-decision boundaries, complexity/authority risks and exact required revisions.

## 9. Acceptance Rule

Only Lead Controller gives final Replay acceptance.

`ready_for_controlled_migration_protocol_test: true` only permits designing a later read-only/controlled migration test. It does not authorize any local mutation.
