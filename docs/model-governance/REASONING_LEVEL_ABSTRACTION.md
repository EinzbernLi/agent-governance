# Reasoning Level Abstraction

版本：0.2.0  
状态：Draft

## 1. 目的

不同模型厂商对 reasoning / thinking level 的命名、档位数量和实际含义并不一致。即使两个模型都提供 `high`，也不能据此推断它们具有相同的推理预算、能力、延迟或任务表现。

因此，本治理体系禁止把不同厂商的原生 reasoning label 直接视为能力等价关系。

核心原则：

> Task Package 表达任务希望投入多少推理资源，并单独表达当前 exact executor 的原生档位约束；RESULT 记录实际使用档位和合规状态。

Reasoning compliance 与 executor identity compliance 分离。换了模型不是“档位偏差”，而是 executor mismatch。

## 2. 三层 Reasoning 模型

### 2.1 `reasoning.profile`

跨厂商、跨模型的任务意图层，只表达资源投入倾向，不代表模型能力排名。

通用 profile：

- `economy`：优先效率；
- `balanced`：普通任务平衡投入；
- `deep`：复杂代码、多文件、疑难调试或高风险验证；
- `max_available`：要求当前 exact model + execution channel 的最高合适原生档位。

### 2.2 Reasoning Adapter

Reasoning Adapter 负责把 profile 映射到某个模型/通道的原生档位，并在需要比较“高/低”时提供有序 native levels。

示例：

```yaml
ordered_native_levels:
  - low
  - medium
  - high
  - xhigh
  - max
```

该顺序只在对应 adapter 内有效，禁止跨厂商比较。

### 2.3 `reasoning.native_constraint`

Task Package 对 exact executor 的原生 reasoning 约束：

```yaml
reasoning:
  profile: deep
  native_constraint:
    policy: preferred
    preferred_level: high
    minimum_level: high
    maximum_level: null
    allow_escalation: true
    allow_deescalation: false
    allow_unexposed: false
    mapping_source: <adapter-ref>
```

这使“推荐 High，但允许 xHigh”与“必须严格 High”成为不同合同，而不是靠聊天解释。

## 3. 四种 Native Constraint Policy

### `exact`

实际 native level 必须与 `preferred_level` 完全一致。适合 benchmark、成本/延迟固定或需要精确复现实验的任务。

### `minimum`

`minimum_level` 为硬下限。更高档位允许，除非设置了 `maximum_level`。

### `preferred`

`preferred_level` 是目标值；是否允许升级/降档由 `allow_escalation`、`allow_deescalation` 和 hard bounds 决定。

常见高风险验证配置：

```yaml
policy: preferred
preferred_level: high
minimum_level: high
allow_escalation: true
allow_deescalation: false
```

此时 High 正常，xHigh 属于允许升级，Medium 低于硬下限而阻塞。

### `max_available`

要求当前 exact model + current execution channel 可用的最高合法档位。如果无法验证是否真的使用最高档位，则按 Task 的 `allow_unexposed` 决定 fail closed 还是记录受控的不可验证偏差。

## 4. 为什么不能直接对齐 high = high

禁止：

```text
GPT high == Gemini high
GPT medium == Gemini medium
```

原因包括厂商定义、档位数量、预算、客户端暴露和模型版本均可能不同。

因此：

- profile 可跨厂商表达意图；
- native constraint 只约束当前 exact executor；
- native level 排序只使用对应 adapter 的 `ordered_native_levels`；
- 不得凭字符串名称猜测档位高低。

## 5. 执行通道参与映射，但不改变语义

映射键至少包含：

```text
model + model_version + execution_channel
```

同一模型不同入口可能暴露不同 reasoning 上限。

例如网页端最高只暴露 `high`，另一 Agent Runtime 暴露 `xhigh`；同一个 `deep` profile 可以得到不同原生映射，但必须分别记录实际 constraint 与 observed level。

## 6. Lead Controller 的选择顺序

Lead Controller 应：

1. 先选 exact final executor；
2. 根据任务风险和历史表现选择 `reasoning.profile`；
3. 读取对应 model/channel Reasoning Adapter；
4. 生成 `native_constraint`；
5. 如覆盖 adapter 推荐值，记录 `override_reason`；
6. 将 constraint 纳入 executor reachability 判断；
7. activation 后由执行会话完成 Pre-execution Compliance Gate。

## 7. Compliance 判定

Reasoning 合规状态至少区分：

- `exact_match`
- `compliant`
- `allowed_escalation`
- `allowed_deviation`
- `noncompliant`
- `unverifiable`
- `unverifiable_allowed`

例如：

```text
Task: exact model A, preferred High, minimum High, escalation allowed

model A / High   -> exact_match
model A / xHigh  -> allowed_escalation
model A / Medium -> noncompliant
model B / High   -> executor identity mismatch, not reasoning deviation
```

完整 Gate 规则见 `docs/protocol/EXECUTOR_REASONING_COMPLIANCE.md`。

## 8. Owner Launch Card 与 Prompt

人工 activation 时，可以把模型、profile、policy、preferred/minimum/max level 告诉 Owner 用于 UI 选择。

这些 Control Plane 信息默认不重复写进 direct executor 的自然语言 Prompt，以免具备编排能力的 Agent 把“使用模型 X / 档位 Y”误解成再次创建子代理。

## 9. 原生档位不可见

如果执行端不暴露 native level，应记录：

```yaml
observed_level: provider_default_or_unexposed
```

是否可继续由 Task 的 policy 决定：

- exact / minimum 等需要验证而 `allow_unexposed: false` → BLOCKED；
- 显式 `allow_unexposed: true` → 可记录 `unverifiable_allowed`，但必须附 capability/runtime attestation。

不得虚构一个未被 UI/runtime 暴露的原生档位。

## 10. 模型更新与 Adapter 更新

模型版本、客户端或档位定义变化时：

- 不修改通用 profile 定义；
- 重新验证 adapter；
- 更新 `ordered_native_levels` 和映射；
- 保留旧证据；
- 不因为档位名称相同而继承旧版本顺序或能力结论。

这样 profile、native constraint、executor identity 和实际执行 evidence 可以长期稳定分层。