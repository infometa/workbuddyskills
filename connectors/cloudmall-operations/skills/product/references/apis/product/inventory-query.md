# 商品域 — 仓库库存查询契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-inventory.md`；写操作（调整/初始化/批量导入）见 `inventory-action.md`。
> 所有 ID 均为十进制字符串；出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：inventory.search 仓库库存分页 · inventory.log-search 库存流水分页 · inventory.warehouses SKU关联仓库 · inventory.export 库存导出（URL型） · inventory.import-task 导入任务进度 · inventory.import-failure-url 导入失败明细地址

---

## ✅ 仓库库存分页 — ops.product.inventory.search

- **语义**：SKU × 仓库维度的库存记录分页。`physicalQty` 总库存、`lockedQty` 订单占用、`availableQty` 可售（=总-占用，系统计算）；门店预留 `reservedQty` 不在本查询范围且不能与 `lockedQty` 混用

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | — | 默认 1（服务端无强制校验） |
| pageSize | Integer | — | 默认 20（建议 ≤100） |
| warehouseId | String | 否 | 仓库ID（十进制字符串） |
| skuId | String | 否 | SKU 业务ID精确筛选 |
| spuId | String | 否 | SPU 业务ID筛选 |
| warehouseType | String | 否 | `STORE_WAREHOUSE`-门店仓 / `FRONT_WAREHOUSE`-前置仓 / `MAIN_WAREHOUSE`-主仓 |
| keyword | String | 否 | 商品名称/SKU ID 模糊（≤100 字符） |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`（库存记录ID → 库存调整入参）、`records[].skuId`/`spuId`
- **枚举字段**：`warehouseType`（STORE_WAREHOUSE/FRONT_WAREHOUSE/MAIN_WAREHOUSE）、`warehouseStatus`（0-停用/1-启用）
- **格式敏感字段**：数量字段均为整数件数
- 缺失数量字段不等于 0；`version` 为乐观锁字段（库存调整 `inventory.adjust` 必传，来自最近查询结果）。

### 调用示例

```json
{"capability":"ops.product.inventory.search","input":{"pageNum":1,"pageSize":20,"spuId":"2058365707555589633"},"summary":"查看商品各仓库的库存分布"}
```

---

## ✅ 库存流水分页 — ops.product.inventory.log-search

- **语义**：按 SKU + 仓库查看库存变动历史（排查超卖/异常变动的依据）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | ✅ | ≥1 |
| pageSize | Integer | ✅ | 1..100 |
| skuId | String | ✅ | SKU 业务ID |
| warehouseId | String | ✅ | 仓库ID |
| changeType | String | 否 | 变动类型：`MANUAL_ADJUST`/`BATCH_IMPORT`/`ORDER_LOCK`/`ORDER_RELEASE`/`SALE_OUTBOUND`/`RETURN_INBOUND` |

### 出参（分页，原始数据）

- **枚举字段**：`changeType`（见 Layer 1 库存变动类型）
- **格式敏感字段**：数量字段为整数件数；时间为 yyyy-MM-dd HH:mm:ss

### 调用示例

```json
{"capability":"ops.product.inventory.log-search","input":{"pageNum":1,"pageSize":20,"skuId":"9000012345678901234","warehouseId":"7000012345678901234"},"summary":"查看SKU的库存变动历史"}
```

---

## ✅ SKU 关联仓库 — ops.product.inventory.warehouses

- **语义**：返回该 SKU 关联的**全部仓库（含未初始化库存的）**——初始化库存前先查有哪些仓库可选

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skuId | String | ✅ | SKU 业务ID |
| storeId | String | — | 门店ID（按门店过滤） |

### 出参（原始返回）

`data[]` 为仓库视图；**关键字段来源**：`[].warehouseId`（→ `inventory.init` 的 `warehouseId`）、仓库名称。

### 调用示例

```json
{"capability":"ops.product.inventory.warehouses","input":{"skuId":"9000012345678901234"},"summary":"查询SKU可用的仓库列表"}
```

---

## ✅ 库存导出（URL 型） — ops.product.inventory.export

- **语义**：按筛选条件导出库存数据，返回 COS 预签名下载 URL（60 分钟时效）。`exportScope`：`ALL`（全量）/ `FILTERED`（按入参筛选）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| exportScope | String | ✅ | `ALL`（全量）/ `FILTERED`（按筛选导出） |
| warehouseId | String | — | 仓库 ID 筛选 |
| warehouseType | String | — | 仓库类型：`STORE_WAREHOUSE` / `FRONT_WAREHOUSE` / `MAIN_WAREHOUSE` |
| spuId | String | — | SPU ID 筛选 |
| keyword | String | — | 关键词（≤100 字符） |

### 出参

- `mode`（sync/async）、`downloadUrl`（同步模式返回的下载地址）、`taskId`（异步模式的任务 ID）。
- 拿到 `downloadUrl` 后转告用户自行下载，不代为下载文件。

### 调用示例

```json
{"capability":"ops.product.inventory.export","input":{"exportScope":"FILTERED","warehouseType":"MAIN_WAREHOUSE"},"summary":"导出主仓库存明细并返回下载链接"}
```

---

## ✅ 导入任务进度 — ops.product.inventory.import-task

- **语义**：查询库存导入任务进度（前端 2 秒轮询；跨租户/不存在的任务统一 404）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| taskId | String | ✅ | 任务 ID（路径参数，来自 import 返回） |

### 出参

- **枚举字段**：`status`（`PENDING` / `PROCESSING` / `SUCCESS` / `PARTIAL_FAIL` / `FAIL`）
- **格式敏感字段**：`createdAt/startedAt/finishedAt`（yyyy-MM-dd HH:mm:ss）
- `totalRows`（异步解析后回写，未解析为 null）、`processedRows`、`successCount`、`failureCount`、`failureReason`（仅 FAIL 有值）、`failureSamples[]`。

### 调用示例

```json
{"capability":"ops.product.inventory.import-task","input":{"taskId":"imp-9f2c1a3b"},"summary":"查询库存导入任务进度"}
```

---

## ✅ 导入失败明细下载地址 — ops.product.inventory.import-failure-url

- **语义**：任务有失败行（PARTIAL_FAIL）时，获取失败明细的 COS 预签名下载 URL（60 分钟时效），转告用户自行下载核对。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| taskId | String | ✅ | 任务 ID（路径参数） |

### 出参

- `mode`（sync）、`downloadUrl`（失败明细下载地址）。

### 调用示例

```json
{"capability":"ops.product.inventory.import-failure-url","input":{"taskId":"imp-9f2c1a3b"},"summary":"获取库存导入失败明细下载链接"}
```

---

## ⛔ 未开放能力（后台存在，当前开放能力集未包含）

| 业务能力 | 说明 |
|------|------|
| 导入模板下载 / 失败明细文件流下载 | 文件流下载，走管理后台（失败明细已开放 URL 型替代） |
