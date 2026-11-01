# 商品域 — 商品通用配置查询契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-gift-setting.md`；写操作见 `setting-action.md`；评价专属设置（审核时效/默认好评/追评窗口/评分维度）见 `review-query.md` / `review-action.md`，商详装修见 `detail-layout-query.md` / `detail-layout-action.md`。
> 所有 ID 均为十进制字符串；出参为上游**原始业务数据**（不裁剪字段）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：setting.general-get 通用配置查询

---

## ✅ 通用配置查询 — ops.product.setting.general-get

- **语义**：查询租户商品通用配置（人工审核时效、默认好评时间、列表缺货过滤）。

### 入参

无（空对象 `{}`）。

### 出参（原始数据）

- `reviewTimeout`（人工审核时效，秒）、`defaultPraiseTime`（默认好评时间，秒）、`filterOutOfStockProduct`（商品列表是否过滤缺货商品）。
- 首次未配置时 `data` 可能为 null——如实告知用户当前无配置，保存后生效。

### 调用示例

```json
{"capability":"ops.product.setting.general-get","input":{},"summary":"查看商品通用配置"}
```

---

## ⛔ 未开放能力（后台存在，当前开放能力集未包含）

| 业务能力 | 说明 |
|------|------|
| 分类导航门店 Redis 缓存重建 | 运维面 |
