# pricingSnapshot 使用规范（references/model-pricing.md）

适用版本：AI-HIVE Connector 1.2.0
更新日期：2026-09-09

## 核心原则

1. **只信服务端**：`pricingSnapshot` 必须来自 `list_models(detail="full")`、`get_model` 或 dry-run 的真实返回值。
2. **不构造**：客户端不得自行构造、估算或缓存价格；不得用历史价格覆盖服务端返回值。
3. **不改写**：`publicModelId` / `routingMode` / `pricingSnapshot` 三元组必须原样用于后续 `chat_text` / `generate_image` / `generate_video`。
4. **最终费用**：按 AI-HIVE 实际用量与账单记录计算；任何"预估"都不能视为最终扣费。

## 调用链路

```
list_models(...)
   └─ 返回 models[]：每个 model 含 publicModelId + routingMode + pricingSnapshot

get_model(publicModelId, routingMode)
   └─ 返回该模型当前参数契约与 pricingSnapshot

generate_image / generate_video(dryRun: true)   [可选预检]
   └─ 只读校验参数与媒体, 返回解析后参数与预估预占金额; 不创建任务、不扣费

user -> decide model
   └─ 分别把选中项的 publicModelId、routingMode、pricingSnapshot 原样传给 chat_text / generate_*
   └─ 付费调用必传稳定 UUID 作为 clientRequestId; 同键同参重试不重复扣费

get_generation_task(...)
   └─ 返回 finalPrice 仅当服务端回写，SKILL 不主动估算
```

## 不做的事

- ❌ 不写"按字符数算大概 0.01 元"这类估算。
- ❌ 不在不调用 `list_models` 的情况下"猜"模型存在与否。
- ❌ 不修改 `routingMode`（如把 `default` 改成 `fast`）；如果服务端返回多个路由，按用户意图选取。
- ❌ 不在扣费前承诺"免费"或"低于某价"。

## 用户余额不足时

展示工具实际返回的余额不足消息；若生成任务已创建并失败，则按 `failure` 安全字段展示。随后按 `error-catalog.md` 通用建议处理：
- 不补写价格
- 不重复创建任务
- 引导用户在 AI-HIVE 完成充值后再试

## 截图与对外文案

公开市场文案只能描述"余额按服务端实时结算"，不得写固定价格或促销话术。
