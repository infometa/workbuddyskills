# 商品域 — 搜索效果验证流程（搜索模拟）

> 对应契约：`apis/product/search-simulation.md`（搜索模拟/联想词查询，只读验证面）。概念知识：`references/domains/product-concepts.md`。

---

## 搜索效果验证（搜索模拟）

**场景**：调整搜索干预（联想词/关键词）前后，验证 C 端搜索命中与排序。

1. **模拟搜索**：`ops.product.spu.search-simulate`（与 C 端同构；验证最新干预效果传 `disableCache: true`）
2. **联想词**：`ops.product.spu.suggest-word`（≤50 字；**返回空=无联想词或服务降级，不代表异常**）
- 只读验证面，不改变线上数据；abs 摘要依赖定店定仓 Header 未开放。
