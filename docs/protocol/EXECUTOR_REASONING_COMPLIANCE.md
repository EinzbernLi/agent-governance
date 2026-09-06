# Exact Model / Reasoning Compliance — Special Mode Only

版本：0.3.0  
状态：Explicit opt-in only

本协议**不属于普通开发、验证、科研或自动化 Task 的默认执行链**。

仅以下任务启用：

- model qualification；
- model benchmark；
- exact-runtime identity experiment；
- Task 明确把 executor identity / reasoning level 本身作为研究变量。

## Ordinary tasks

普通任务使用 `DISPATCH_ROUTING_PROTOCOL.md`。隐藏 internal child exact model/reasoning 不是 acceptance gate；外部 Owner launch 也不要求平台重新证明 Owner 的选择。

普通 external launch 的最小 activation record 是 Owner 按 Task assignment 选择目标平台/模型/reasoning 后执行该 Task；普通 native dispatch 记录实际 dispatch route 即可。两者都不需要额外 attestation chain。

## Special contract

特殊任务可明确要求：

```yaml
special_model_identity_mode:
  requested_model: <exact-model>
  requested_reasoning: <level>
  minimum_assurance: owner_attested|platform_attested|runtime_verified
```

证据必须区分 requested / attested / observed；`unexposed` 不等于 mismatch，family label 不能推断 exact model。

Assurance 含义：

- `owner_attested`：Owner 明确按 Task/Launch Card 选择了请求的平台/模型/reasoning；
- `platform_attested`：平台暴露了与请求对应的可归属元数据；
- `runtime_verified`：运行时/provider 级证据直接验证 exact identity/reasoning。

Native/orchestrated activation 不因为没有单独 attestation 文件而失败；如果 special Task 要求 platform/runtime 级 assurance，则必须使用实际可提供该证据的路径。

若任务要求的 assurance 高于当前路径可提供的证据，应在 activation 前换路径或 BLOCK，不得通过重复启动普通 executor 试错。

## Scope

Special mode 只验证它声明的 identity/reasoning 变量；Task scope、permissions、evidence boundary、tests、durable Result handoff 和 Lead final acceptance 仍使用普通治理规则。

本文件吸收 special identity mode 所需的 activation-evidence 语义；普通 dispatch 不再需要独立 Activation Attestation authority/file。
