# 商品域 — 静态标签查询契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-tag.md`；写操作（绑定/定义维护/删除）见 `static-tag-action.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 静态标签 = 运营手工定义的商品标记（如"热销""新品推荐"），与隐藏/推荐开关独立；标签绑定在 SKU 级。SKU 搜索选择器见 `spu-query.md` 的 `ops.product.sku.search`。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：static-tag.search 标签分页 · static-tag.skus 标签关联SKU列表

---

## ✅ 标签分页 — ops.product.static-tag.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | — | 分页 |
| tagName | String | — | 标签名（模糊） |
| effectStatus | String | — | 生效状态：`EFFECTIVE`（生效中）/ `NOT_EFFECTIVE`（未生效）/ `EXPIRED`（已过期） |
| validFrom / validTo | String | — | 有效期范围（`YYYY-MM-DD HH:mm:ss`，空格分隔） |

### 出参（原始返回）

`data.records[]` 为标签视图；**关键字段来源**：`records[].id`（→ 标签 SKU 列表/绑定的 `id`）、`tagName`、优先级。

### 调用示例

```json
{"capability":"ops.product.static-tag.search","input":{"pageNum":1,"pageSize":20,"tagName":"热销"},"summary":"查询热销相关标签"}
```

---

## ✅ 标签关联 SKU 列表 — ops.product.static-tag.skus

- **语义**：绑定前先看当前关联，避免误解绑

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 标签ID（来自 static-tag.search 的 `records[].id`） |
| pageNum / pageSize | Integer | — | 分页 |

### 出参（原始返回）

`data.records[]` 为标签-SKU 关联视图（含 skuId、商品名等）。

### 调用示例

```json
{"capability":"ops.product.static-tag.skus","input":{"id":"8000012345678901234","pageNum":1,"pageSize":20},"summary":"查看标签当前关联的SKU"}
```
