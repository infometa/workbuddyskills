# 商品域 — 搜索模拟契约（只读验证面）

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-search.md`。
> 语义：运营端「搜索模拟」页——以 C 端同款搜索链路验证关键词命中与排序，用于搜索干预（联想词/关键词调整）前后对比，**只读模拟，不改变线上数据**。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：spu.search-simulate 搜索模拟 · spu.suggest-word 联想词查询

---

## ✅ 搜索模拟 — ops.product.spu.search-simulate

- **语义**：以 C 端同款搜索请求结构执行搜索，返回命中结果与外部引擎信息（externalItemIds 等），验证关键词/排序效果。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | String | — | 搜索关键词 |
| pageNum | Integer | — | 页码（默认 1） |
| pageSize | Integer | — | 每页条数（默认 10） |
| sortField | String | — | 排序字段 |
| sortOrder | String | — | 排序方向 |
| debug | Boolean | — | 调试信息（默认 false） |
| disableCache | Boolean | — | 禁用缓存（默认 false；验证最新干预效果时用 true） |

### 出参（原始数据）

- C 端搜索同构的命中列表（商品卡片信息）+ `externalItemIds`（外部引擎 itemId 列表）+ 调试信息（debug=true 时）。

### 调用示例

```json
{"capability":"ops.product.spu.search-simulate","input":{"keyword":"研学","pageNum":1,"pageSize":10,"disableCache":true},"summary":"模拟C端搜索验证研学关键词命中"}
```

---

## ✅ 联想词查询 — ops.product.spu.suggest-word

- **语义**：关键词输入框联想词（与 C 端行为一致）：外部 Suggest 服务转发 + 静默降级——**失败/空/无效均返回 200 + 空 list**（返回空不等于服务异常，如实说明）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | String | ✅ | 输入关键词（≤50 字） |

### 出参（原始数据）

- 联想词列表（可能为空数组）。

### 调用示例

```json
{"capability":"ops.product.spu.suggest-word","input":{"keyword":"研学"},"summary":"查询研学关键词的C端联想词"}
```

---

## ⛔ 未开放能力（后台存在，当前开放能力集未包含）

| 业务能力 | 说明 |
|------|------|
| abs 摘要独立查询（simulate/abs-details） | 依赖定店定仓上下文（X-Store-Warehouse Header）——Capability 调用链不注入该 Header，上下文缺失时服务端静默跳过返回空，开放无意义 |
