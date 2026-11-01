# 商品域 — 门店商品查询契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-store.md`；写操作（上下架/档位/门店价/预留/审核/分配）见 `store-product-action.md`。
> 所有 ID 均为十进制字符串；出参为上游**原始业务数据**（不裁剪字段），未列出的展示型字段以后端实际返回为准，透传给用户即可。
> 门店商品 = SPU 分配到具体门店后的运营实体（`storeProductId`），可独立控制门店维度的上架状态、SKU 档位、门店价格与预留库存。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：store-product.search 门店商品分页 · store-product.status-count 状态计数 · store-product.skus 门店SKU列表 · store-product.inventory-detail 库存明细 · store-product.log-search 变更日志 · store-product.export 导出（URL型）

---

## ✅ 门店商品分页 — ops.product.store-product.search

- **语义**：按门店/名称/状态等筛选门店商品列表，返回分页结果；门店维度商品管理入口

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | — | 分页，默认 1/10 |
| storeIds | String[] | — | 门店ID列表（多选） |
| spuName / keyword | String | — | SPU 名称（旧字段，已被 keyword 聚合搜索取代）/ 聚合关键词（商品名/SPU ID/SKU ID/商家编码） |
| status | String | — | 门店商品上架状态：`ON_SHELF` / `OFF_SHELF` |
| productType | String | — | 商品形态：`PHYSICAL` / `SERVICE` / `STUDY_TOUR` |
| categoryCodes | String[] | — | 类目编码列表（多选） |
| bizType | String[] | — | 业务分类多选：`PHYSICAL` / `SERVICE_ONSITE`（到店服务）/ `SERVICE_PICKUP`（上门服务）/ `STUDY_TOUR`（研学） |
| source | String | — | 来源筛选：`ADMIN` / `GUIDE_PUBLISH` / `SUPPLIER` |
| categoryCode | String | — | 末级类目编码单选（精确） |
| brandId | String | — | 品牌 ID（精确） |

⚠️ **extensionFieldFilters（按扩展字段筛选）在开放调用链上不可用**：该参数为嵌套对象（`fieldCode → 值列表`），而本能力为 GET query 传输——调用链层对 query 参数的对象值直接拒绝（INPUT_INVALID）。按扩展字段筛选门店商品请走 `ops.product.store-product.export`（POST 传输，支持该筛选）。

### 出参（原始返回）

`data.records[]` 为门店商品 SPU 视图；**关键字段来源**：`records[].id`（→ 各写能力的 `storeProductId`/`id`）、`storeName`、`spuName`、`status`。

### 调用示例

```json
{"capability":"ops.product.store-product.search","input":{"pageNum":1,"pageSize":20,"storeIds":["6000012345678901234"],"status":"ON_SHELF"},"summary":"查询指定门店的在架商品"}
```

---

## ✅ 门店商品状态计数 — ops.product.store-product.status-count

- **语义**：复用列表筛选口径，一次返回全部/已上架/已下架数量（列表页 Tab 计数）。

### 入参

与门店商品分页搜索（`ops.product.store-product.search`）同构的筛选参数（storeIds/keyword/status 等，除分页外）。

### 出参

- `allCount`、`onShelfCount`、`offShelfCount`（数量）。

### 调用示例

```json
{"capability":"ops.product.store-product.status-count","input":{"storeIds":["6000012345678901234"]},"summary":"统计该门店商品各上下架状态数量"}
```

---

## ✅ 门店商品 SKU 列表 — ops.product.store-product.skus

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeProductId | String | ✅ | 门店商品ID（来自 store-product.search 的 `records[].id`） |

### 出参（原始返回）

`data[]` 为门店 SKU 视图，关键字段：

- **路径参数来源**：`[].skuId`（→ SKU 级操作的 `skuId`）、`[].storePrice`（门店价）、`[].status`（SKU 档位状态，ON_SHELF/OFF_SHELF）、`[].reservedStock`（该 SKU 当前预留——预留操作乐观锁 expectedOldQty 取这里）
- **格式敏感字段**：`price`（元）；`updatedTime`（yyyy-MM-dd HH:mm:ss）
- 四维库存：`totalStock`（总）/`lockedStock`（占用）/`reservedStock`（预留）/`availableStock`（可售）
- `specInfo`：JSON 字符串，内部结构为**对象映射** `{"颜色":"红色"}`（同 `spu.skus`）
- `skuExtensionFields`：**三层包装结构** `{fieldCode: {value, displayValue, fieldType}}`（编辑回填取 `.value`，同 `spu.detail`）
- `updatedBy`（最近更新人）

### 调用示例

```json
{"capability":"ops.product.store-product.skus","input":{"storeProductId":"3100012345678901234"},"summary":"查看门店商品的SKU明细"}
```

---

## ✅ 门店商品库存明细 — ops.product.store-product.inventory-detail

- **语义**：调预留库存/价格前先看此明细

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeProductId | String | ✅ | 门店商品ID |

### 出参（原始数据）

- 四维库存汇总：`totalStock`（总）/`lockedStock`（订单占用）/`reservedStock`（预留）/`availableStock`（可售）
- `warehouseDetails[]`：仓库维度明细——`warehouseId`（→ `inventory.init` 的 warehouseId）、`warehouseCode`、`warehouseName`、`status`（0-停用/1-启用）、各仓库 `totalStock`/`lockedStock`/`availableStock`

### 调用示例

```json
{"capability":"ops.product.store-product.inventory-detail","input":{"storeProductId":"3100012345678901234"},"summary":"查看门店商品库存明细"}
```

---

## ✅ 门店商品变更日志 — ops.product.store-product.log-search

- **语义**：门店商品操作日志，覆盖门店商品上/下架、SKU 上/下架、修改门店价格、设置时段库存（服务/研学类）、预留库存变更；按 `storeId + spuId` 精确查询某门店下某商品的操作记录

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | ✅ | 分页（必填） |
| storeId | String | ✅ | 门店ID（必填） |
| spuId | String | ✅ | 商品 SPU 业务标识（必填，直接按日志表 spu_id 过滤） |
| skuId | String | — | SKU 维度过滤 |
| changeType | String | — | 变动类型：`ON_SHELF`/`OFF_SHELF`（门店商品上/下架）、`SKU_ON_SHELF`/`SKU_OFF_SHELF`（SKU 上/下架）、`STORE_PRICE_UPDATE`（修改门店价格）、`SLOT_STOCK_UPDATE`（设置时段库存）、`RESERVED_QTY_UPDATE_SINGLE`/`RESERVED_QTY_UPDATE_BATCH`（预留库存单条/批量编辑） |

### 出参（原始返回）

`data.records[]` 为变更日志视图：`id`、`storeId`、`spuId`、`skuId`（SPU 级/时段级操作为空）、`changeType`（见上枚举）、`source`（`PLATFORM` 运营端 / `SUPPLIER` 供应商端）、`beforeVal`/`afterVal`（变动前后的文本值，如“已下架”→“已上架”、“¥129.00”→“¥139.00”、“19:00-21:00 容量:5 已开放”）、`operator`（操作人名称）、`createdAt`（yyyy-MM-dd HH:mm:ss）。

### 调用示例

```json
{"capability":"ops.product.store-product.log-search","input":{"pageNum":1,"pageSize":20,"storeId":"6000012345678901234","spuId":"6000012345678905678"},"summary":"查门店商品变更记录"}
```

---

## ✅ 门店商品导出（URL 型） — ops.product.store-product.export

- **语义**：按筛选条件导出 SPU 级门店商品（含四维库存汇总），返回 COS 预签名下载 URL（60 分钟时效）。筛选条件与门店商品分页搜索同构。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| storeId | String | — | 门店 ID（单选，兼容旧口径） |
| storeIds | List&lt;String&gt; | — | 门店 ID 列表（多选） |
| spuName | String | — | 商品名称（模糊，≤200 字符） |
| keyword | String | — | 聚合关键词：商品名 / SPU ID / SKU ID / 商家编码（≤200 字符） |
| status | String | — | 上架状态（ON_SHELF / OFF_SHELF） |
| bizType | List&lt;String&gt; | — | 业务类型多选（SERVICE_ONSITE / SERVICE_PICKUP / STUDY_TOUR 等） |
| categoryCodes | List&lt;String&gt; | — | 类目编码多选 |
| productType | String | — | 商品形态（PHYSICAL / SERVICE / STUDY_TOUR） |
| extensionFieldFilters | Map | — | 扩展字段筛选：`{fieldCode: [值列表]}`——按扩展字段**存储值精确匹配**（非模糊；SINGLE_SELECT/MULTI_SELECT 传选项 code，布尔传 true/false，服务端统一按字符串匹配）；多值 = 或关系；SPU 级与 SKU 级扩展字段命中任一即入选；`fieldCode` 须为已配置的扩展字段编码 |

### 出参

- `mode`（sync/async）、`downloadUrl`（下载地址）、`taskId`（异步任务 ID）。
- 拿到 `downloadUrl` 后转告用户自行下载。

### 调用示例

```json
{"capability":"ops.product.store-product.export","input":{"storeIds":["6000012345678901234"],"status":"ON_SHELF"},"summary":"导出该门店已上架的门店商品清单"}
```

---

## ⛔ 未开放能力（后台存在，当前开放能力集未包含）

| 业务能力 | 说明 |
|------|------|
| 门店选项列表 | 后台为临时实现（门店模块未落地，返回空列表），开放无意义 |
