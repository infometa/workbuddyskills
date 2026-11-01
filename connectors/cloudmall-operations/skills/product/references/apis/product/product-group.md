# 商品域 — 商品分组契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-publishing.md`（发品时选分组）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：group.options 分组选项

---

## ✅ 分组选项 — ops.product.group.options

- **语义**：商品分组下拉选项；发品时取 `id` 作为 `groupId`（可选字段）

### 入参

无（空对象 `{}`）。

### 出参（数组，原始数据）

- **关键字段来源**：`id`（→ 创建/编辑 `groupId`）
- 选项字段：`id`（→ groupId）、`name`。

### 调用示例

```json
{"capability":"ops.product.group.options","input":{},"summary":"获取商品分组选项"}
```

> ⛔ 分组的增删改当前未开放（分组为系统配置，后台无对应运营端点）。
