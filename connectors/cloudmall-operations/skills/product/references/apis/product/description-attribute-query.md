# 商品域 — 描述属性查询契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-dictionary.md`；写操作（增改删）见 `description-attribute-action.md`；按类目查询描述属性（发品参考）见 `category-brand-query.md` 的 `ops.product.description-attribute.by-category`。
> 所有 ID 均为十进制字符串；出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：description-attribute.page 描述属性分页

---

## ✅ 描述属性分页 — ops.product.description-attribute.page

- **语义**：描述属性管理分页列表（跨类目管理视角，可按 ID/名称/类目过滤）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | ✅ | 页码 |
| pageSize | Integer | ✅ | 每页条数（≤100） |
| attributeId | String | — | 属性 ID（精确） |
| attributeName | String | — | 属性名称（模糊，≤20 字符） |
| categoryCode | String | — | 类目编码（精确，来自 category.tree） |

### 出参（`PageResult`，原始数据）

- **路径参数来源**：`records[].id`（→ update/delete 的路径参数）
- 字段：`id`、`attributeName`、`categoryCode`、`interactionType`、属性值列表等。

### 调用示例

```json
{"capability":"ops.product.description-attribute.page","input":{"pageNum":1,"pageSize":20,"categoryCode":"T900001_C61"},"summary":"查看研学类目的描述属性列表"}
```
