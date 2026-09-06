# Model Qualification

版本：0.2.0  
状态：Draft

## 1. 目的

本规范用于决定某个模型是否有资格承担 Lead Controller、Worker、Validator 等角色，以及在模型升级、能力漂移或疑似能力退化后如何重新评估。

核心原则：

> 不因为模型名称更新而自动升级；不因为公开排行榜领先而自动获得任务权限。

## 2. 模型状态

建议维护以下状态：

- `candidate`：待评估，仅可用于 shadow / benchmark；
- `provisional`：已通过 Bootstrap Qualification，可在限定 task class 与 risk ceiling 内承担真实任务；
- `qualified`：已通过最低正式资格；
- `preferred`：当前某类任务优先模型；
- `fallback`：备用模型；
- `degraded`：近期表现明显下降，限制使用；
- `suspended`：暂停任务分配；
- `retired`：停止使用。

`provisional` 用于解决治理体系刚启动时“内部数据不足但又需要开始真实验证”的问题。它不是全局能力认证。

## 3. 评估维度

每个模型至少评估：

- `repo_navigation`；
- `bounded_code_edit`；
- `multi_file_edit`；
- `test_generation`；
- `test_execution_reasoning`；
- `debugging`；
- `instruction_following`；
- `scope_control`；
- `long_context`；
- `tool_use`；
- `review_quality`；
- `domain_specific_reasoning`（如适用）；
- `cost`；
- `latency`。

## 4. 真实任务优先

公开 benchmark 仅作为候选筛选参考。正式路由应优先使用治理体系自己的匿名化真实任务集。

建议至少覆盖以下通用任务类型：

- 阅读陌生仓库并定位相关代码；
- 在明确文件范围内完成局部代码修改；
- 修复一个可复现 bug；
- 编写和运行单元测试；
- 分析错误日志并给出最小修复；
- 在受限范围内完成跨文件修改；
- 检查配置、接口和数据结构一致性；
- 根据既有规范更新文档；
- 独立审查另一模型的修改；
- 检查任务是否违反 scope / non-goals；
- 在长上下文下保持既有架构和 ADR 约束。

任务样本不得包含具体项目名称、个人信息、私有路径或不可公开的业务数据。必要时使用脱敏 fixture、合成仓库或匿名化代码片段。

## 5. Bootstrap Qualification

当内部数据不足时，先使用 `BOOTSTRAP_ROUTING_SEED.yaml` 规定试验顺序，再按 `BOOTSTRAP_QUALIFICATION.md` 做本地快速准入。

```text
External evidence seed
        ↓
Candidate
        ↓
Bootstrap Qualification
        ↓
Provisional（限定 task class / risk）
        ↓
真实项目任务积累
        ↓
Qualified
        ↓
Preferred（如长期稳定）
```

## 6. 建议记录指标

至少记录：

- `first_pass_acceptance_rate`；
- `lead_controller_rejection_rate`；
- `scope_violation_rate`；
- `test_pass_rate`；
- `context_omission_rate`；
- `rework_count`；
- `average_task_cost`；
- `accepted_task_cost`；
- `average_latency`。

其中 `accepted_task_cost` 定义为：

```text
某模型在一组任务上的实际总成本
────────────────────────────
最终经 Lead Controller 验收通过的任务数
```

它比单纯 token 单价更接近真实开发成本。

## 7. 新模型上线流程

```text
Candidate
   ↓
通用能力评测 / Bootstrap Qualification
   ↓
Provisional（如需）
   ↓
匿名化真实任务 benchmark
   ↓
Shadow Tasks / 与现模型对照
   ↓
Lead Controller 审查
   ↓
Qualified
   ↓
有限流量使用
   ↓
Preferred（如表现持续稳定）
```

## 8. 模型升级规则

新一代模型上线时：

- 不自动替换旧版本；
- 旧版本在可用时保持原资格；
- 新版本先作为 `candidate`；
- 如需快速开始真实评估，可先通过 Bootstrap Qualification 获得 `provisional`；
- 通过内部任务集后再调整路由；
- 如新版本只在部分任务更强，则只授予对应角色或任务类型资格。

## 9. 能力退化检测

出现以下情况时，应触发重新评估：

- 首次通过率持续下降；
- Lead Controller 驳回率明显上升；
- 越权修改增多；
- 工具调用失败增多；
- 同类任务返工次数上升；
- 输出格式遵守率下降；
- 已稳定通过的 benchmark 出现异常回退。

根据严重程度可将模型标记为 `degraded` 或 `suspended`。

## 10. 跨项目反馈

模型资格与路由应读取匿名化跨项目 Calibration Snapshot，但：

- 单一项目不能自动提升全局资格；
- 单次失败不能自动降级全局资格；
- 项目局部 override 可以存在；
- 中央资格变化必须满足样本门槛并经过 Lead Controller 审核。

## 11. Lead Controller 也必须评估

Lead Controller 不永久绑定某个模型。新的总控候选模型必须重点评估：

- 架构一致性；
- 核心代码质量；
- 长程项目状态保持；
- Task Package 质量；
- Worker 结果审查能力；
- 对既有 ADR 的遵循；
- 冲突裁决；
- 最终验收准确性；
- 是否容易进行无依据的大规模重构。

只有通过 Controller Qualification 后，才能替换当前 Lead Controller。

## 12. Execution Channel Qualification

同一模型在不同客户端或 Agent Runtime 中的表现必须允许独立评估。模型资格和执行通道健康状态不得混为一项。

例如，同一个 Lead Controller 模型可同时具备多个交互通道：

```text
same model
  ├── web_client
  └── desktop_client
```

两端应分别跟踪近期表现。建议至少比较：

- 相同 bootstrap 输入下的上下文恢复准确性；
- 相同任务包下的架构一致性；
- 核心代码修改质量；
- 指令遵循与 scope 控制；
- 最终验收判断一致性；
- 工具可用性与失败率；
- 同类任务相对历史基线是否出现可复现回退。

执行通道可以被标记为 `active`、`degraded` 或 `suspended`，但这不自动改变底层模型在其他通道中的资格。

当一个总控通道出现可复现质量退化而另一通道保持稳定时，可以切换 active channel。切换必须遵守 Execution Channel Governance，并在交接前确认最新 Context Checkpoint，防止双总控状态分叉。

Worker / Validator 的 Agent Runtime 也应记录执行通道。Reasoning level 属于任务级路由参数，由 Lead Controller 根据任务复杂度、风险和历史失败情况动态选择；除非某个模型或运行时存在明确限制，不应把一个固定 reasoning level 永久绑定到 Worker 角色。
