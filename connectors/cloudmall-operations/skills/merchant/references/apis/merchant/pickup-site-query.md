# 商户域 — 自提点查询契约

> 概念知识：`references/domains/merchant-concepts.md`；运营流程：`references/flows/merchant-store.md`；自提点写操作见 `pickup-site-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：pickup-site.search 自提点分页搜索 · pickup-site.detail 自提点详情

---

## ✅ 自提点分页搜索 — ops.merchant.pickup-site.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| id | String | 否 | 自提点ID精确匹配 |
| name | String | 否 | 自提点名称模糊搜索 |
| status | Integer | 否 | 0=禁用 1=启用 |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].id`（→ 详情/编辑/状态变更/删除/门店绑定的 pickupSiteId）
- **枚举字段**：`status`（0/1）、`siteType`（STORE_PICKUP=门店默认自提点 / REGULAR_PICKUP=常规自提点）、`isBound`（仅门店可绑场景）
- **格式敏感字段**：`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）、`businessHoursStart`/`businessHoursEnd`（HH:MM）
- `stores[]` 为关联门店（id/name/storeCode）。

### 调用示例

```json
{"capability":"ops.merchant.pickup-site.search","input":{"pageNum":1,"pageSize":20,"name":"科技园","status":1},"summary":"查找启用中的科技园自提点"}
```

---

## ✅ 自提点详情 — ops.merchant.pickup-site.detail

- 编辑回填共用

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 自提点ID |

### 出参（原始数据）

- **关键字段来源**：`fulfillmentTemplateId`（关联履约模板）、`stores[].id`（关联门店ID）
- **枚举字段**：`status`（0/1）、`siteType`
- **格式敏感字段**：`longitude`/`latitude`（WGS84 坐标）、`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）
- `businessHoursJson` 为每日营业时间 JSON 字符串，结构见 `pickup-site-action.md` 创建参数说明。

### 调用示例

```json
{"capability":"ops.merchant.pickup-site.detail","input":{"id":"7200012345678901234"},"summary":"查看自提点详情与营业时间配置"}
```

---

## ⛔ 未开放

| 操作 | 原因 |
|------|------|
| 导出自提点 | 二进制文件流响应；产品决策仅开放 URL 型导出，此型走管理后台 |
