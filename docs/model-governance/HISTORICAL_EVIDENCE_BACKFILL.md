# Historical Evidence Backfill / 历史证据回填

版本：0.1.0  
状态：Draft

## 1. 目的

在治理体系正式建立之前，已有项目可能已经采用“Lead Controller + Worker / Validator”的协作方式，并留下可审计的 Task、PR、commit、测试和最终验收记录。

这些历史记录不应被浪费，但也不能因为缺少新协议字段而直接视为完整前瞻性校准数据。

本规范定义如何将旧项目的历史执行记录匿名化回填为模型资格证据。

## 2. 可计入的历史任务

一个历史任务至少满足以下条件，才可进入回填：

- 可以确定执行模型或验证模型；
- 可以确定模型在该任务中的角色；
- 存在明确任务范围或可恢复的 scope；
- 存在 exact commit / tree / PR 等可审计代码证据；
- 存在测试、CI 或本地验证证据；
- 存在 Lead Controller 的明确 PASS / REWORK / REJECT 结论；
- 可以确定最终是否被接受；
- 可以确定返工次数或至少确定是否 first-pass；
- 不依赖不可验证的聊天口头结论。

若无法可靠确定模型身份、角色或验收结果，则不得猜测。

## 3. 历史证据的权重

历史回填证据低于按现行治理协议产生的前瞻性数据。

建议证据等级：

- `retrospective_strong`：模型/角色、精确代码、测试、Lead 验收、返工轨迹均明确；
- `retrospective_partial`：大部分证据明确，但 reasoning level、成本或部分中间状态缺失；
- `unusable`：模型身份、任务角色或验收结果无法可靠恢复。

中央 Calibration 不得把 retrospective 数据与 prospective 数据无区别合并。

## 4. 历史证据可以带来的升格

历史回填可以支持：

```text
candidate
   ↓
provisional（限定 role / task class / risk ceiling）
```

历史回填本身通常不足以直接支持：

```text
qualified -> preferred
```

`preferred` 应优先要求现行治理体系下的前瞻性任务数据、跨项目样本和近期健康状态。

## 5. 按任务类型升格，不做全局升格

模型资格必须尽可能细分到：

- role；
- task_class；
- risk ceiling；
- execution channel；
- reasoning profile / native level（如可恢复）。

例如，一个模型可以是：

```yaml
bounded_code_edit:
  status: provisional
  risk_ceiling: medium
```

同时在：

```yaml
high_risk_state_machine_change:
  status: candidate
```

不得因为模型在某些任务上成功，就推断它适合所有 Worker 任务。

## 6. 返工是有价值的负证据

历史任务最终 PASS 不等于 first-pass PASS。

必须尽量区分：

- `accepted_first_pass=true`；
- `accepted_after_rework`；
- `rejected`；
- `abandoned/superseded`。

Lead Controller 多次指出重大缺陷后才通过的任务，应降低该模型在相应 task class / risk 下的初始置信度，而不能只记录最终 PASS。

## 7. 匿名化要求

回填到治理仓库的中央记录不得包含：

- 原项目名称；
- 仓库地址；
- 真实路径；
- 业务对象名称；
- 私有数据；
- 可反推出项目身份的任务文本。

中央只保留聚合后的 task class、模型、role、reasoning、风险和结果指标。

## 8. 与新模型的公平比较

已有模型可以凭历史证据获得 `provisional` 初始资格；新加入且没有历史记录的模型保持 `candidate`。

之后应安排 matched shadow / calibration tasks，使新旧模型在尽量相同的 task class 和风险条件下比较。

因此：

- 历史模型拥有“经验先验”，不是永久特权；
- 新模型没有历史劣势的永久惩罚；
- 新模型通过足够对照任务后可以追平或超过 incumbent；
- incumbent 如果近期退化，也可以被降级。

## 9. 推荐迁移流程

```text
已有项目历史记录
       ↓
恢复模型 / role / task class / outcome
       ↓
匿名化
       ↓
标记 retrospective evidence grade
       ↓
生成 provisional qualification proposal
       ↓
Lead Controller 审核
       ↓
更新 MODEL_REGISTRY / Calibration Snapshot
       ↓
未来 prospective tasks 继续校准
```
