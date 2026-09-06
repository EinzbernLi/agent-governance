# Bootstrap Qualification

版本：0.1.0  
状态：Draft

## 1. 目的

在治理体系刚开始使用、尚没有足够跨项目历史数据时，需要一个受控的模型准入流程，避免两种极端：

- 完全凭公开 benchmark 或主观印象直接把某模型设为 preferred；
- 因为没有内部数据而无法使用任何 Worker。

Bootstrap Qualification 用于把外部证据转化为“待验证的初始先验”，再通过本地 Agent Runtime 的小规模真实执行验证，获得有限生产资格。

## 2. 状态建议

模型角色资格可使用：

- `candidate`：仅有外部证据或待测试；
- `provisional`：通过 Bootstrap Qualification，可承担限定风险与限定任务类型；
- `qualified`：通过足够内部真实任务评估；
- `preferred`：在某 task class 上长期表现稳定并被选为默认；
- `fallback`；
- `degraded`；
- `suspended`；
- `retired`。

`provisional` 不是全局能力认证，只表示“在指定范围内可以开始真实使用并继续积累证据”。

## 3. Bootstrap 测试集

每个候选 Worker 至少测试以下通用任务：

1. repo navigation：定位指定模块与相关测试；
2. bounded edit：只修改允许文件完成局部功能；
3. regression-safe fix：修复一个可复现问题且不得弱化测试；
4. test generation：补充边界测试；
5. local execution：运行测试并正确解释失败；
6. scope control：面对诱导性旁支问题仍不扩大任务范围；
7. result reporting：按 RESULT 模板准确记录证据。

Validator 还应测试：

- 独立发现实现错误；
- 检查越权修改；
- 识别测试不足；
- 不盲从 Worker 的 PASS 声明。

## 4. Reasoning 采样

Bootstrap 不需要穷举所有模型 × 所有原生档位。

建议：

- 先使用模型官方默认或经验推荐档；
- 再对一个困难样本测试更高档；
- 只有当较高档位带来稳定收益时，才写入 adapter 推荐；
- 不跨厂商比较 reasoning label 名称。

## 5. Provisional 准入条件

建议满足以下条件后，可授予某 task class 的 `provisional`：

- 所有基础 scope-control 测试通过；
- 没有高严重度越权修改；
- 可在 Agent Runtime 中正确完成本地修改与验证；
- 关键任务至少有一次独立验证通过；
- Lead Controller 审查通过；
- 明确记录允许的 task classes、risk ceiling 与 reasoning 建议。

## 6. Provisional 使用限制

`provisional` Worker：

- 默认只用于 low / medium risk；
- 不自行修改核心架构；
- 关键修改必须有独立 Validator 或 Lead Controller 深度复核；
- 真实任务结果必须进入 project calibration；
- 出现明显 scope violation 时立即降回 candidate 或 suspended。

## 7. 从 Provisional 到 Qualified

随着项目推进，当某模型在足够真实任务中保持稳定表现，并有多个 task class 或多个项目来源支持时，可升级为 `qualified`。

升级依据优先使用：

- first-pass acceptance；
- final acceptance；
- rework；
- scope violation；
- test quality；
- validator disagreement；
- Lead Controller rejection；
- cost / latency；
- recent trend。

## 8. Bootstrap Seed 的地位

`BOOTSTRAP_ROUTING_SEED.yaml` 只能表示“初始试验顺序”，不能表示：

- 已资格认证；
- 永久模型排名；
- 不同 reasoning 档位等价；
- 新项目必须照搬。

一旦内部数据充分，Calibration Snapshot 应逐步取代 Bootstrap Seed。