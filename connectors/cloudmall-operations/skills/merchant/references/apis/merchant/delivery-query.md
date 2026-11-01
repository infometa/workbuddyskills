# 商户域 — 配送方式与运费/履约模板查询契约

> 概念知识：`references/domains/merchant-concepts.md`，状态与枚举：`references/domains/merchant-enums.md`；运营流程：`references/flows/merchant-warehouse.md`；写操作见 `delivery-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。按「关键字段来源 / 枚举 / 格式敏感」三类标注。
> ⚠️ BY_VOLUME（按体积计费）后端暂未开放，创建/编辑会被服务端拒绝——需要按体积计费时如实告知用户不可用。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：delivery-method.list 配送方式列表（全部） · delivery-method.list-enabled 配送方式列表（仅启用） · freight-template.search 运费模板分页 · freight-template.detail 运费模板详情 · fulfillment-template.search 履约模板分页 · fulfillment-template.detail 履约模板详情

---

## ✅ 配送方式列表（全部） — ops.merchant.delivery-method.list

### 入参（无）

### 出参（数组）

- **关键字段来源**：`id`（→ 仓库绑定配送方式的 deliveryId）、`code`（express/city_express/rider_delivery/self_service 等小写编码——**交易域和商品域引用此 code**）
- **枚举字段**：`status`（0=停用 1=启用）

### 调用示例

```json
{"capability":"ops.merchant.delivery-method.list","input":{},"summary":"列出全部配送方式"}
```

---

## ✅ 配送方式列表（仅启用） — ops.merchant.delivery-method.list-enabled

### 入参（无）

### 出参（数组）

同上，仅含 status=1 的记录。

### 调用示例

```json
{"capability":"ops.merchant.delivery-method.list-enabled","input":{},"summary":"列出可用的配送方式"}
```

---

## ✅ 运费模板分页搜索 — ops.merchant.freight-template.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| templateId | String | 否 | 模板ID精确匹配 |
| templateName | String | 否 | 模板名称模糊匹配，≤50 |
| chargeMode | String | 否 | `BY_QUANTITY`/`BY_WEIGHT`/`BY_VOLUME`/`FIXED`/`FREE` |
| enabled | Boolean | 否 | 启用状态 |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`（→ 区块模板绑定的 freightTemplateId）
- **枚举字段**：`chargeMode`（五值）、`enabled`（boolean）
- **格式敏感字段**：`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）、`chargeConfig`（JSON 字符串，结构见 `delivery-action.md` 创建参数）

### 调用示例

```json
{"capability":"ops.merchant.freight-template.search","input":{"pageNum":1,"pageSize":20,"templateName":"标准","enabled":true},"summary":"查找启用中的标准运费模板"}
```

---

## ✅ 运费模板详情 — ops.merchant.freight-template.detail

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 模板ID |

### 出参（原始数据）

含完整 `chargeConfig` JSON 字符串；枚举/格式同上。

### 调用示例

```json
{"capability":"ops.merchant.freight-template.detail","input":{"id":"7500012345678901234"},"summary":"查看运费模板计费配置"}
```

---

## ✅ 履约模板分页搜索 — ops.merchant.fulfillment-template.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| templateName | String | 否 | 模板名称模糊搜索 |
| templateType | String | 否 | 模板类型（当前取值「预约配送」） |
| status | Integer | 否 | 0=禁用 1=启用 |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`（→ 区块/自提点绑定的 fulfillmentTemplateId）
- **枚举字段**：`status`（0/1）
- **格式敏感字段**：`timeConfig`（JSON 字符串，结构见 `delivery-action.md` 创建参数）、`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）

### 调用示例

```json
{"capability":"ops.merchant.fulfillment-template.search","input":{"pageNum":1,"pageSize":20,"templateName":"次日达"},"summary":"查找次日达履约模板"}
```

---

## ✅ 履约模板详情 — ops.merchant.fulfillment-template.detail

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 模板ID |

### 出参（原始数据）

含完整 `timeConfig`；字段同上。

### 调用示例

```json
{"capability":"ops.merchant.fulfillment-template.detail","input":{"id":"7600012345678901234"},"summary":"查看履约模板时间配置"}
```
