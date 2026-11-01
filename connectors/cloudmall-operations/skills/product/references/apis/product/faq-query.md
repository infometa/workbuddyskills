# 商品域 — FAQ（商详常见问题）查询契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-detail.md`；写操作（增改/启停/删除/排序）见 `faq-action.md`；商详装修见 `detail-layout-query.md` / `detail-layout-action.md`。
> 所有 ID 均为十进制字符串；出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：faq.page FAQ分页

---

## ✅ FAQ 分页 — ops.product.faq.page

- **语义**：商详常见问题分页列表（按启用状态/生效状态/关键词/商品形态筛选）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | ✅ | 页码 |
| pageSize | Integer | ✅ | 每页条数（≤100） |
| enabled | Boolean | — | 启用状态筛选（true=启用 / false=停用） |
| effectiveStatus | String | — | 生效状态：`IN_EFFECT`（生效中）/ `NOT_STARTED`（未开始）/ `EXPIRED`（已过期） |
| keyword | String | — | 问题模糊搜索（≤30 字） |
| productType | String | — | 商品形态筛选（如 PHYSICAL / STUDY_TOUR） |

### 出参（`PageResult`，原始数据）

- **路径参数来源**：`records[].id`（→ update/delete/toggle/reorder 的 FAQ ID）
- **枚举字段**：`enabled`、生效状态
- **格式敏感字段**：`effectiveStart/effectiveEnd`（yyyy-MM-dd HH:mm:ss；null=永久）
- 字段：`question`（≤30 字）、`answer`（≤300 字）、`sort`、`productTypes[]`（适用商品形态）。

### 调用示例

```json
{"capability":"ops.product.faq.page","input":{"pageNum":1,"pageSize":20,"effectiveStatus":"IN_EFFECT"},"summary":"查看生效中的商详FAQ"}
```
