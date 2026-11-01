# 商户域 — 仓库查询契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-warehouse.md`；仓库写操作见 `warehouse-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。按「关键字段来源 / 枚举 / 格式敏感」三类标注，未列出的展示型字段以后端实际返回为准，透传给用户即可。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：warehouse.search 仓库分页搜索 · warehouse.stats 仓库配置统计 · warehouse.detail 仓库详情 · warehouse.delivery-methods 仓库已绑配送方式 · warehouse.delivery-blocks 仓库区块配置查询

---

## ✅ 仓库分页搜索 — ops.merchant.warehouse.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| id | String | 否 | 仓库ID精确匹配 |
| keyword | String | 否 | 仓库名称/编码模糊搜索，≤50 字符 |
| status | Integer | 否 | 0=停用 1=启用 |
| configStatus | String | 否 | `UNCONFIGURED`/`DRAFT`/`READY` |
| warehouseType | String | 否 | `STORE_WAREHOUSE`/`FRONT_WAREHOUSE`/`MAIN_WAREHOUSE` |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`（→ 仓库详情/编辑/绑定操作的 `input.id`）
- **枚举字段**：`status`（0/1）、`warehouseType`、`configStatus`、`isBound`（仅门店可绑仓库场景）
- **格式敏感字段**：`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）
- `stores[]` 为已关联门店（storeId/storeName）、`deliveryMethods[]` 为已绑配送方式名称。

### 调用示例

```json
{"capability":"ops.merchant.warehouse.search","input":{"pageNum":1,"pageSize":20,"keyword":"前置仓","status":1},"summary":"查找启用中的前置仓"}
```

---

## ✅ 仓库统计卡片 — ops.merchant.warehouse.stats

### 入参（无）

### 出参

| 字段 | 说明 |
|------|------|
| total | 总仓库数 |
| readyCount | 已就绪（READY） |
| draftCount | 待完善（DRAFT） |
| unconfiguredCount | 未配置（UNCONFIGURED） |

### 调用示例

```json
{"capability":"ops.merchant.warehouse.stats","input":{},"summary":"查看仓库配置状态统计"}
```

---

## ✅ 仓库详情 — ops.merchant.warehouse.detail

- 编辑回填与详情查看共用

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 仓库ID |

### 出参（原始数据）

- **关键字段来源**：`id`、`blockConfigs[].freightTemplateId`/`fulfillmentTemplateId`（null=未配置，需补绑）
- **枚举字段**：`status`（0/1）、`warehouseType`、`configStatus`、`blockConfigs[].blockType`（1=电子围栏 2=全国 3=省 4=市 5=区）、`blockConfigs[].configStatus`（COMPLETE/DRAFT）
- **格式敏感字段**：`capacity`（库容，2 位小数）、`createdTime`（yyyy-MM-dd HH:mm:ss）

### 调用示例

```json
{"capability":"ops.merchant.warehouse.detail","input":{"id":"7000012345678901234"},"summary":"查看仓库详情与区块配置"}
```

---

## ✅ 仓库已绑配送方式 — ops.merchant.warehouse.delivery-methods

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 仓库ID |

### 出参（数组）

- **关键字段来源**：`deliveryId`（→ 区块绑定/模板绑定操作的 `input.deliveryId`）
- **枚举字段**：`code`（express/city_express/rider_delivery/self_service，小写）、`deliveryStatus`（0/1）、`configComplete`（boolean，该方式下区块是否全部配完模板）

### 调用示例

```json
{"capability":"ops.merchant.warehouse.delivery-methods","input":{"id":"7000012345678901234"},"summary":"查看仓库已绑配送方式及配置完成度"}
```

---

## ✅ 仓库区块配置查询 — ops.merchant.warehouse.delivery-blocks

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 仓库ID |
| deliveryId | String | ✅ | 配送方式ID |

### 出参（数组）

- **关键字段来源**：`id`（→ 解绑区块的 `input.blockRecordId`，是绑定记录ID不是区块ID）、`blockId`（→ 模板绑定的 `input.blockId`）、`freightTemplateId`/`fulfillmentTemplateId`（null=未配置）
- **枚举字段**：`blockType`（1=电子围栏 2=全国 3=省 4=市 5=区）、`configStatus`（**COMPLETE/INCOMPLETE**——注意与本能力不同，仓库详情 `blockConfigs[].configStatus` 的取值是 COMPLETE/DRAFT，两处枚举集不一致，按各自说明解读）、`blockStatus`（0/1，区块自身启停）

### 调用示例

```json
{"capability":"ops.merchant.warehouse.delivery-blocks","input":{"id":"7000012345678901234","deliveryId":"7400012345678901234"},"summary":"查看快递配送方式的区块配置"}
```

---

## ⛔ 未开放

| 操作 | 原因 |
|------|------|
| 仓库删除 | 后端未提供仓库删除端点（仅启停） |
