# pricingSnapshot 使用规范（references/model-pricing.md）

适用版本：AI-HIVE Connector 1.0.0
更新日期：2026-07-31

## 核心原则

1. **只信服务端**：`pricingSnapshot` 必须来自 `list_models` 的真实返回值。
2. **不构造**：客户端不得自行构造、估算或缓存价格；不得用历史价格覆盖服务端返回值。
3. **不改写**：`publicModelId` / `routingMode` / `pricingSnapshot` 三元组必须原样用于后续 `chat_text` / `generate_image` / `generate_video`。
4. **最终费用**：按 AI-HIVE 实际用量与账单记录计算；任何"预估"都不能视为最终扣费。

## 调用链路

```
list_models(...)
   └─ 返回 models[]：每个 model 含 publicModelId + routingMode + pricingSnapshot

user -> decide model
   └─ 把选中的 model 对象（含 pricingSnapshot）作为入参传给 chat_text / generate_* 

get_generation_task(...)
   └─ 返回 finalPrice 仅当服务端回写，SKILL 不主动估算
```

## 不做的事

- ❌ 不写"按字符数算大概 0.01 元"这类估算。
- ❌ 不在不调用 `list_models` 的情况下"猜"模型存在与否。
- ❌ 不修改 `routingMode`（如把 `default` 改成 `fast`）；如果服务端返回多个路由，按用户意图选取。
- ❌ 不在扣费前承诺"免费"或"低于某价"。

## 用户余额不足时

返回 `INSUFFICIENT_BALANCE`（Category: `billing`），按 `error-catalog.md` 通用展示建议：
- 不补写价格
- 不重复创建任务
- 引导用户在 AI-HIVE 完成充值后再试

## 截图与对外文案

公开市场文案只能描述"余额按服务端实时结算"，不得写固定价格或促销话术。
