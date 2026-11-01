# 促销域 — 活动库存查询契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-support.md`
> 适用于单品层限量活动（周期购等）的运行态库存。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 能力索引（前缀 `ops.promotion.`）：查询 stock.items
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）执行。
> 增加库存（仅正增量，幂等 batchOperationId）见 `stock-action.md`。

---

## ✅ 活动库存项分页 — `ops.promotion.stock.items`

- **说明**：服务端校验活动归属当前租户且促销类型支持增加库存——**不是所有促销类型的通用库存接口**，类型不支持时如实转述错误。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| promotionId | String | ✅ | 活动 ID |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| goodsId | String | 否 | 商品 ID（**同时匹配活动明细中的 SPU ID 或 SKU ID**；注意不是只匹配 skuId） |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].skuId`（→ 增库存 items[].skuId）
- **格式敏感字段**：`totalCount`（总库存）/`availableCount`（可用库存，均为件数整数）；`specInfo`（规格描述）、`externalSkuId`（外部编码）——⚠️ 商品富化字段（spuName/skuName/specInfo/externalSkuId）在商品域查询**降级时缺位**（skuId/totalCount通常保留；availableCount即使返回0，也可能是Redis缺值/异常降级，不能仅凭字段存在断言真实可用量）
- 出参**不含** stockPolicy/usedCount（只有 totalCount/availableCount 两个库存数）。

### 调用示例

```json
{"capability":"ops.promotion.stock.items","input":{"promotionId":"4100000000000000001","pageNum":1,"pageSize":20},"summary":"分页查看周期购活动各SKU库存"}
```

---
