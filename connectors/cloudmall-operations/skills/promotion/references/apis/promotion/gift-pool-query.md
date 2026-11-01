# 促销域 — 赠品库查询契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-support.md`
> 赠品库是满元赠/满件赠/买赠活动的赠品 SKU 来源；**SPU 维度聚合展示**，移除前查询引用并核对关联影响，0不是完整安全证明。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 能力索引（前缀 `ops.promotion.`）：查询 gift-pool.search · gift-pool.sku-details · gift-pool.reference-count
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）执行。
> 赠品增删（批量添加 / 移除 🔴）见 `gift-pool-action.md`；移除前必查本文件 reference-count。

---

## ✅ 赠品池分页搜索 — `ops.promotion.gift-pool.search`


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| keyword | String | 否 | **SPU ID / SKU ID 精确搜索**（十进制字符串；不是名称模糊搜索） |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].spuId`（→ SKU 明细/按 SPU 移除）、`records[].giftPoolId`（→ 单记录移除；⚠️ **列表行 giftPoolId 仅对应 SPU 第一条 SKU**——逐 SKU 移除请用 `skuDetails[].giftPoolId`）、`skuDetails[].skuId`
- **枚举字段**：`productStatus`——⚠️ **当前实现仅返回 `in_use` / `available` 两态**（按 linkedActivityCount>0 判定；下架/全零库存的组合状态计算未接商品数据，off_shelf/out_of_stock 现版本不可达）
- **格式敏感字段**：`skuCount`（SPU 下赠品 SKU 数）、`linkedActivityCount`（关联商品行数，不是去重活动数，可能含MG主品行；仅统计未开始/预热/进行中的MYG/MJG/MG，已结束/暂停及未落主表草稿不在该口径，0不能证明无引用）、`createdTime`（yyyy-MM-dd HH:mm:ss）
- ⚠️ `realStock`/`productPrice`/`productImage`/`specName` 当前版本**不返回**（商品富化未实现，字段整体缺位）——价格与库存需经商品域能力查询。

### 调用示例

```json
{"capability":"ops.promotion.gift-pool.search","input":{"pageNum":1,"pageSize":20,"keyword":"2058365707555589633"},"summary":"按商品ID查赠品池记录"}
```

---

## ✅ 赠品 SKU 明细 — `ops.promotion.gift-pool.sku-details`

- 展开行懒加载

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | SPU ID |

### 出参（原始数据）

- 同列表行结构（含完整 `skuDetails` 数组）；**关键字段来源**：`skuDetails[].skuId`、`skuDetails[].giftPoolItemId`（→ 赠品活动 extJson 的 `giftPoolItemId`）。
- ⚠️ `skuDetails[]` 内的 `specName` / `productPrice` / `realStock` / `specImage` **同样恒缺位**（全中心无赋值点，与列表行的商品富化字段同源不可达）——SKU 名称/价格/库存需经商品域能力查询。

### 调用示例

```json
{"capability":"ops.promotion.gift-pool.sku-details","input":{"spuId":"2058365707555589633"},"summary":"展开该赠品的SKU明细"}
```

---

## ✅ 活动引用数查询 — `ops.promotion.gift-pool.reference-count`

- 移除赠品前的安全预检

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuIds | String[] | 至少传其一 | SPU ID 列表（与 skuIds 至少传其一，**均不传返回空 Map 不报错**） |
| skuIds | String[] | 至少传其一 | SKU ID列表；spuIds非空时本字段被忽略，需要两个粒度时分开查 |

### 出参（原始数据）

- Map：key 为 SPU/SKU ID（十进制字符串），value为上述状态/类型的关联商品行计数（不按活动去重、不滤主赠角色）。0不能排除暂停活动或未落主表草稿引用；结合真实活动与用户意图核对移除影响，未知不宣称安全。

### 调用示例

```json
{"capability":"ops.promotion.gift-pool.reference-count","input":{"spuIds":["2058365707555589633"]},"summary":"移除前检查赠品被活动引用数"}
```

---
