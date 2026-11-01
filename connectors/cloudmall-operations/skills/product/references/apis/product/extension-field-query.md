# 商品域 — 商品扩展字段查询契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-dictionary.md`；写操作（增改/启停/排序/删除）见 `extension-field-action.md`。
> 所有 ID 均为十进制字符串；出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：extension-field.search 扩展字段分页

---

## ✅ 扩展字段分页 — ops.product.extension-field.search

- **语义**：商品扩展字段定义的分页列表（发品表单的可配置字段台账，含启用状态与能力开关）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | ✅ | 页码 |
| pageSize | Integer | ✅ | 每页条数（≤100） |
| keyword | String | — | 名称/编码关键词 |
| targetLevel | String | — | 字段层级：`ALL` / `SPU` / `SKU` |
| fieldType | String | — | 字段类型（枚举见 create） |
| enabled | Boolean | — | 启用状态 |
| capability | String | — | 能力筛选：`PRODUCT_LIST_VISIBLE` / `PRODUCT_FILTERABLE` / `PRODUCT_EXPORTABLE` / `EDITABLE` |

### 出参（`PageResult`，原始数据）

- **路径参数来源**：`records[].id`（→ update/set-enabled/delete/sort 的字段 ID）
- **枚举字段**：`targetLevel`（ALL/SPU/SKU）、`fieldType`、`requiredMode`（NONE/ALWAYS/CONDITION）
- 字段：`id`、`fieldCode`、`fieldName`、`targetLevel`、`fieldType`、`optionConfig`（string，JSON 数组 `[{code,label}]`）、`enabled`、`editable`、`sortOrder` 等。

### 调用示例

```json
{"capability":"ops.product.extension-field.search","input":{"pageNum":1,"pageSize":20,"targetLevel":"SPU"},"summary":"查看 SPU 层级的扩展字段定义"}
```

---

## ⛔ 未开放能力（后台存在，当前开放能力集未包含）

| 业务能力 | 说明 |
|------|------|
| 运行时按场景拉取启用字段（runtime） | 表单渲染辅助面，查询需求已由分页 + enabled 筛选覆盖 |
