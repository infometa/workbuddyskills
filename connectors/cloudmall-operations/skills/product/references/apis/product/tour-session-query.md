# 商品域 — 研学营期名额查询契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-tour.md`；写操作（批量更新名额）见 `tour-session-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 研学商品（`productType=STUDY_TOUR`）按「营期场次」管理名额：总量 `totalQuota`、预留 `reservedQty`、锁定（`lockedQty`，下单未支付）与已售；可售 = 总量 − 预留 − 锁定 − 已售（口径与后端一致）。**权限要求平台管理员/运营角色**（权限不足会得到 PERMISSION_DENIED）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：tour-session-quota.list 按门店查营期名额 · tour-session-quota.aggregate 跨门店名额聚合

---

## ✅ 按门店查营期名额 — ops.product.tour-session-quota.list

- **语义**：改名额前先查当前场次与版本号

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skuId | String | ✅ | SKU 业务ID（研学 SKU，先经 store-product 查询定位） |
| storeId | String | ✅ | 门店ID |
| fromDate / toDate | String | — | 日期范围（`YYYY-MM-DD`） |
| includeArchived | Boolean | — | 是否含已归档场次（默认 false） |

### 出参（原始返回）

`data[]` 为场次名额视图；**关键字段来源**：`[].id`（→ batch-update 的 `updates[].id`）、`[].version`（→ `updates[].expectedVersion` 的版本字段）、`totalQuota`、`reservedQty`、`lockedQty`、`signedQty`（已售）、`availableQty`（可售）、`sessionId`、`departureDate`（yyyy-MM-dd）、`startTime`/`endTime`（HH:mm:ss）、`status`、`bizType`。

### 调用示例

```json
{"capability":"ops.product.tour-session-quota.list","input":{"skuId":"9000012345678901234","storeId":"6000012345678901234","fromDate":"2026-09-10","toDate":"2026-09-30"},"summary":"查询门店9月下旬营期名额"}
```

---

## ✅ 按 SPU 跨门店聚合 — ops.product.tour-session-quota.aggregate

- **语义**：看一个研学商品在各门店的名额分布

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | SPU 业务ID（必填） |
| skuId | String | — | SKU 业务ID（可选，收窄到单规格） |

### 调用示例

```json
{"capability":"ops.product.tour-session-quota.aggregate","input":{"spuId":"2058365707555589633"},"summary":"查看研学商品各门店名额汇总"}
```
