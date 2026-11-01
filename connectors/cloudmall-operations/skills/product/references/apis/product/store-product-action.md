# 商品域 — 门店商品写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-store.md`；现态读取（门店商品/SKU 档位/库存明细）先读 `store-product-query.md`（先读现值模式）。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：store-product.on-shelf 门店上架 · store-product.off-shelf 门店下架 · store-product.batch-on-shelf 批量上架 🔴 · store-product.batch-off-shelf 批量下架 🔴 · store-product.sku-toggle-shelf SKU档位翻转 · store-product.batch-sku-toggle-shelf SKU档位批量 🔴 · store-product.sku-store-price 门店价 🔴 · store-product.batch-sku-store-price 门店价批量 🔴 · store-product.reserved-qty 预留库存 🔴 · store-product.batch-reserved-qty 预留库存批量 🔴 · store-product.audit 门店商品审核 🔴 · store-product.batch-assign-store 批量分配门店

---

## ✅ 门店上架 — ops.product.store-product.on-shelf

- **语义**：影响该门店可售性，执行前向用户复述门店与商品

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 门店商品ID（storeProductId） |

### 出参（原始返回）

`data` 为 `null`（Void）；以调用后 `store-product.search` 核验状态为准。

### 调用示例

```json
{"capability":"ops.product.store-product.on-shelf","input":{"id":"3100012345678901234"},"summary":"门店上架该商品"}
```

---

## ✅ 门店下架 — ops.product.store-product.off-shelf

- **语义**：影响该门店可售性，执行前向用户复述门店与商品

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 门店商品ID（storeProductId） |

### 出参（原始返回）

`data` 为 `null`（Void）；以调用后 `store-product.search` 核验状态为准。

### 调用示例

```json
{"capability":"ops.product.store-product.off-shelf","input":{"id":"3100012345678901234"},"summary":"门店下架该商品"}
```

---

## ✅ 门店批量上架 — ops.product.store-product.batch-on-shelf

- 🔴 商业影响档位；批量影响面大，执行前向用户复述对象清单

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | 门店商品ID列表，≤200 项 |

### 出参（原始返回）

`data` 为批量结果对象：`{totalCount, successCount, failCount}`（仅计数，无逐条明细——失败项进服务端日志；有失败时按计数报告并建议回读列表核对）。

### 调用示例

```json
{"capability":"ops.product.store-product.batch-on-shelf","input":{"ids":["3100012345678901234","3100012345678901235"]},"summary":"批量门店上架两个商品"}
```

---

## ✅ 门店批量下架 — ops.product.store-product.batch-off-shelf

- 🔴 商业影响档位；批量影响面大，执行前向用户复述对象清单

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | 门店商品ID列表，≤200 项 |

### 出参（原始返回）

`data` 为批量结果对象：`{totalCount, successCount, failCount}`（仅计数，无逐条明细——失败项进服务端日志；有失败时按计数报告并建议回读列表核对）。

### 调用示例

```json
{"capability":"ops.product.store-product.batch-off-shelf","input":{"ids":["3100012345678901234"]},"summary":"批量门店下架"}
```

---

## ✅ SKU 档位切换（单条翻转） — ops.product.store-product.sku-toggle-shelf

- **语义**：控制门店商品内单个 SKU 档位的可售性（如仅下架某规格）。toggle 为**翻转语义**（在架↔下架），执行前先查 `store-product.skus` 确认当前档位

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeProductId | String | ✅ | 门店商品ID |
| skuId | String | ✅ | SKU 业务ID |

### 调用示例

```json
{"capability":"ops.product.store-product.sku-toggle-shelf","input":{"storeProductId":"3100012345678901234","skuId":"9000012345678901234"},"summary":"翻转该SKU的门店档位"}
```

---

## ✅ SKU 档位切换（批量显式） — ops.product.store-product.batch-sku-toggle-shelf

- **语义**：批量切换 SKU 档位，`action` 为显式方向（非翻转）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| action | String | ✅ | `ON_SHELF` / `OFF_SHELF`（显式方向，非翻转） |
| items | Array | ✅ | `[{storeProductId, skuId}]` 列表，≤500 项 |

### 调用示例

```json
{"capability":"ops.product.store-product.batch-sku-toggle-shelf","input":{"action":"ON_SHELF","items":[{"storeProductId":"3100012345678901234","skuId":"9000012345678901234"}]},"summary":"批量开启SKU档位"}
```

---

## ✅ 门店价格（单 SKU） — ops.product.store-product.sku-store-price

- 🔴 商业影响档位；执行前必须用户确认价格
- **语义**：设置该门店该 SKU 的专属价。**`storePrice` 必传**（当前版本省略传值不会恢复全局价——后端置空更新不生效，恢复全局价请在管理后台操作）。⚠️ 单条路径服务端**无价格下限校验**（批量路径校验 ≥0.01）——传 0/负数会落库，价格数值必须由用户明确给出且为合法正数。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeProductId | String | ✅ | 门店商品ID |
| skuId | String | ✅ | SKU 业务ID |
| storePrice | String | ✅ | 新门店价（元字符串，如 "199.00"） |

### 出参（原始返回）

`data` 为 `null`（Void）；以 `store-product.skus` 的 `storePrice` 核验。

### 调用示例

```json
{"capability":"ops.product.store-product.sku-store-price","input":{"storeProductId":"3100012345678901234","skuId":"9000012345678901234","storePrice":"199.00"},"summary":"设置门店专属价199元"}
```

---

## ✅ 门店价格（批量） — ops.product.store-product.batch-sku-store-price

- 🔴 商业影响档位；批量改价执行前必须用户确认价格清单

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeProductId | String | ✅ | 门店商品ID |
| items | Array | ✅ | `[{skuId, storePrice}]` 列表（storePrice 必填；批量路径校验 ≥0.01） |

### 调用示例

```json
{"capability":"ops.product.store-product.batch-sku-store-price","input":{"storeProductId":"3100012345678901234","items":[{"skuId":"9000012345678901234","storePrice":"199.00"}]},"summary":"批量设置门店SKU价格"}
```

---

## ✅ 预留库存（单 SKU） — ops.product.store-product.reserved-qty

- 🔴 商业影响档位；预留量影响可售计算，执行前确认数值
- **语义**：设置该门店该 SKU 的预留库存；`expectedOldQty` 传当前值做乐观锁（不一致会被服务端拒绝）。**上限规则（服务端强制）**：预留量不能超过该门店可分配上限（总库存-订单占用的合计），超出被拒。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeProductId | String | ✅ | 门店商品ID |
| skuId | String | ✅ | SKU 业务ID |
| reservedQty | Integer | ✅ | 新预留量（≥0） |
| expectedOldQty | Integer | ✅ | 当前预留量（乐观锁必填，来自 `store-product.skus` 该 SKU 的 `reservedStock`；不一致会被拒绝） |

### 调用示例

```json
{"capability":"ops.product.store-product.reserved-qty","input":{"storeProductId":"3100012345678901234","skuId":"9000012345678901234","reservedQty":20,"expectedOldQty":10},"summary":"设置门店SKU预留库存20"}
```

---

## ✅ 预留库存（批量统一值） — ops.product.store-product.batch-reserved-qty

- 🔴 商业影响档位；预留量影响可售计算，执行前确认数值
- **语义**：`skuItems` 统一设置同一预留量；**整批拦截**——任一 SKU 校验失败则整批不生效（超限 SKU 见错误消息）。批量无乐观锁字段。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skuItems | Array | ✅ | `[{storeProductId, skuId, storeId}]` 列表，≤100 项 |
| reservedQty | Integer | ✅ | 统一设置的新预留量（**整批拦截**：任一 SKU 超限则整批被 422 拒绝，超限 SKU 见错误消息） |

### 调用示例

```json
{"capability":"ops.product.store-product.batch-reserved-qty","input":{"skuItems":[{"storeProductId":"3100012345678901234","skuId":"9000012345678901234","storeId":"6000012345678901234"}],"reservedQty":20},"summary":"批量设置预留库存"}
```

---

## ✅ 门店商品审核 — ops.product.store-product.audit

- 🔴 商业影响档位；驳回必须给原因
- **前置条件**（服务端强制）：仅**导购发品/供应商来源**（GUIDE_PUBLISH/SUPPLIER）且对应 SPU `auditStatus=REVIEWING` 的门店商品可审——ADMIN 自建商品不可审，违反返回业务校验失败

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 门店商品ID |
| action | String | ✅ | `APPROVE`（通过）/ `REJECT`（驳回） |
| rejectReason | String | REJECT 时必填 | 驳回原因 |

### 调用示例

```json
{"capability":"ops.product.store-product.audit","input":{"id":"3100012345678901234","action":"APPROVE"},"summary":"审核通过该门店商品"}
```

```json
{"capability":"ops.product.store-product.audit","input":{"id":"3100012345678901234","action":"REJECT","rejectReason":"门店售价低于成本线"},"summary":"驳回该门店商品"}
```

---

## ✅ 批量分配门店（门店商品侧） — ops.product.store-product.batch-assign-store

- **语义**：把一批门店商品（`ids` 为门店商品关联 ID，服务端定位对应 SPU）批量分配到目标门店。与 SPU 侧 `spu.batch-assign-store`（传 SPU ID）区分：本能力传**门店商品 ID**。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | List&lt;String&gt; | ✅ | 门店商品关联 ID 列表（≤200 条，来自 store-product.search 的 records[].id） |
| storeIds | List&lt;String&gt; | ✅ | 目标门店 ID 列表（≤100 个） |

### 出参

- 批量结果（成功/失败明细，部分失败逐条报告）。

### 调用示例

```json
{"capability":"ops.product.store-product.batch-assign-store","input":{"ids":["3100012345678901234"],"storeIds":["6000012345678901234"]},"summary":"把该门店商品追加分配到目标门店"}
```
