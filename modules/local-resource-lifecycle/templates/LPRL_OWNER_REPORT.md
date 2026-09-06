# LPRL Owner Report

> 面向非专业项目 Owner。技术 Gate、拓扑闭包、State/Data/Deployment 校验、引用图无环检查、哈希一致性和空间派生由 Evaluator/Lead Controller 处理；Owner 只审批已经完成技术证明的后果。

## Summary

```yaml
report_id: "owner-report-000"
report_time: null
control_snapshot_ref: null
control_snapshot_digest: null
registry_ref: null
validation_result_refs: []
storage_ledger_ref: null
safe_reclaimable_derivation_ref: null
```

## 必须保留

| 资源说明 | 原因 | 当前占用 | 下一步 |
|---|---|---:|---|
| | | | |

## 当前活动

| 资源说明 | 正在承担的职责 | 当前占用 | 是否需要用户操作 |
|---|---|---:|---|
| | | | 否 |

## 待技术判定

| 资源说明 | 缺少的证明/闭包 | 当前处理 |
|---|---|---|
| | | 保留，不操作 |

## 原则候选但未授权

| 资源说明 | 已有证明 | 尚缺 Gate/授权 | 候选空间（非承诺） |
|---|---|---|---:|
| | | | |

## 可安全释放

只有绑定到同一 frozen Control Snapshot、canonical Validation Result PASS、完整 Gate Bundle PASS、没有 retention/hold 阻塞，并由 Storage Ledger 派生出安全可释放空间的内容才出现在这里。

| Retirement ID | 内容说明 | 派生安全空间 | 恢复窗口 | 建议操作 |
|---|---|---:|---|---|
| | | | | |

## 已进入 `_delete` / 等待最终清空

| Retirement ID | 已验证空间 | 可恢复至 | purge 是否已授权 |
|---|---:|---|---|
| | | | |

## Owner Decision

Owner 不需要判断 Git/worktree/State/Data/Deployment/manifest digest 或 evaluator 技术安全性。只需对已经完成技术 Gate 的动作选择：

- 批准进入 retirement buffer；
- 暂缓；
- 批准最终 purge（适用时）。

技术事实不完整、scope/topology closure 失败、snapshot 失效、引用图成环或关系校验失败时，Agent 必须保持“待技术判定”，不得把风险转交给 Owner 猜测。
