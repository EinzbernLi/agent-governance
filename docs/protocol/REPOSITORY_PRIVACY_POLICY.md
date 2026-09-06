# Repository Privacy & Anonymization Policy

版本：0.2.0  
状态：Accepted supporting policy

> Governance currency/adoption authority remains `docs/project-adoption/GOVERNANCE_CURRENCY_PROTOCOL.md`. This document is a supporting privacy policy, not a competing semantic owner.

## 1. 目的

本治理仓库必须保持通用、匿名、可复用。它只保存治理协议、模板、release metadata、模型资格/路由规则、公开外部 evidence 和有意去项目化的通用结论；不保存任何接入项目的身份或项目专属状态。

核心边界：

```text
downstream owns project facts
upstream owns reusable governance facts
no adopter registry
no required telemetry / phone-home
```

## 2. 禁止写入

以下内容不得作为 external adopter/project state 提交或持续保存在本仓库：

- 具体接入项目名称或代号；
- 个人姓名、用户名、邮箱、手机号、账号标识或联系方式；
- 下游仓库的实际 `owner/repository` 身份；
- downstream Issue / PR / Task / Lead / branch / commit SHA 映射；
- 本地绝对路径、用户目录或设备标识；
- downstream `LOCAL_POLICY` / `PROJECT_STATE` / LPRL Registry、Snapshot、Gate、Deployment/State/Data 等项目事实；
- downstream 原始模型 outcome、原始 Task/Result/Validator evidence 或逐样本记录；
- 客户、机构、实验室、团队的非公开信息；
- API Key、Token、密码、Cookie、证书或其他凭据；
- 私有业务数据、实验数据、样本数据；
- 只对某个具体项目成立的领域规则；
- 可反推出具体项目身份的任务描述或 benchmark 数据。

GitHub 平台本身显示 contributor/account metadata 不等于治理产品建立 adopter mapping；治理仓库不得维护 `account -> downstream project` 的持久关联。

## 3. 示例占位符

文档、模板和测试中统一优先使用：

- `example-project`
- `owner/repository`
- `<project-root>`
- `<task-id>`
- `<model-id>`
- `<provider>`
- `sample_module.py`

如需更真实的 benchmark，应使用合成代码、公开样例或完成脱敏后的 fixture。

## 4. 接入项目的边界

具体项目应在自己的 repo/GitHub authority surface 中保存：

- 项目状态；
- 本地策略；
- 受保护目录；
- Task / Result / Review / Acceptance；
- Lead Claim / checkpoint；
- 项目专属 benchmark / project-local calibration；
- LPRL 项目事实与本地资源状态；
- governance-update signal；
- 与上游 public Issue/feedback 的本地映射（如需要）。

这些信息不得反向同步到治理仓库。治理仓库的正确运行也不得要求 adopter registration、central project database、downstream credential 或 usage telemetry。

## 5. Optional upstream model feedback

外部项目模型反馈默认只留在项目本地。只有 Owner/治理维护者明确 opt-in 时，项目侧才可以根据 `templates/PROJECT_ROUTING_FEEDBACK.yaml` 形成匿名**aggregate** contribution。

允许上游接收的只应是通用聚合维度，例如 role、task class、risk、model/reasoning semantic key 和聚合 outcome 指标。禁止 raw sample rows、project/repository/Task/Issue/PR/SHA/path/business/personal fields，也禁止为了证明“来自不同项目”而创建稳定 adopter pseudonym/hash。

```text
explicit opt-in != automatic delivery
aggregate feedback != project registration
anonymous package != distinct-project identity proof
```

匿名 aggregate 可以作为补充 evidence，但单个或无法证明独立来源的匿名包不得自动改变中央 qualification/default，也不得伪装满足 `min_distinct_project_sources`。

## 6. 提交前检查

对治理仓库的新增或修改至少检查：

1. 是否出现真实 downstream 项目名/仓库身份或可持续关联标识；
2. 是否出现个人信息；
3. 是否出现私有仓库路径；
4. 是否出现绝对路径或账号目录；
5. 是否出现 downstream Issue/Task/Lead/branch/SHA、LPRL/project-local state 或 raw model outcome；
6. 示例是否可以改成通用占位符；
7. benchmark / feedback 是否已经在 downstream 边界完成匿名化和聚合；
8. 是否误将某项目的局部策略升级成全局治理规则；
9. 是否偷偷引入 adopter registry、telemetry、phone-home 或 automatic upstream sender。

发现上述问题时，应先在 downstream 边界完成泛化/匿名化；中央不得先接收原始项目事实再替用户做“事后匿名化”。
