# 商户域 — 分类导航配置与发布流程

> 对应契约：`apis/merchant/category-nav-query.md` / `category-nav-action.md`（模板）、`apis/merchant/category-nav-content-query.md` / `category-nav-content-action.md`（前台分类与商品关联）、`apis/merchant/category-nav-stats.md`（统计）；概念知识：`references/domains/merchant-concepts.md`，状态机见 `references/domains/merchant-enums.md`；写操作共同纪律与字段来源见 `merchant-core.md`。

**场景**：从零配置一个前台分类导航并发布；或复制现有导航做活动改版。

---

## 新建并配置

1. `ops.merchant.category-nav.create`（layoutMode 创建后不可改；name ≤20 字）→
2. `ops.merchant.category-nav.front-category.batch-save` 维护分类树（additions 用 tempId 占位，响应 `idMapping` 换真实 ID；层级 ≤3 级）→
3. 商品填充（二选一或组合）：
   - **手动添加**：`ops.product.spu.search`（商品域）选商品 → `ops.merchant.category-nav.category-products.add`（source=manual；注意部分成功——invalidIds/duplicateCount 逐项报告）
   - **类目关联**：`ops.product.category.tree`（商品域）取后台类目编码 → `link-backend-category.preview` 预估导入量 → 用户确认数量 → `link-backend-category`（dynamic=实时同步 / snapshot=一次性导入）
4. `ops.merchant.category-nav.store-visibility.update` 配置门店可见性（SPECIFIED 时冲突→展示 conflictTemplates 确认→forceUpdate=true 重提）。

## 发布

5. `ops.merchant.category-nav.publish`（或编辑页一步到位用 `save-and-publish`）→
6. **二次确认语义**：`success=false` 时检查返回——`emptyCategories[]`（空分类警告）确认后 `forcePublish=true`；`conflictTemplates[]`（替换已有生效模板）确认后 `confirmReplace=true` → 重提 →
7. 回读 list/detail 确认 `status=published`。

## 数据表现复盘

- `stats.overview`（转化概览）→ `stats.core`（PV/UV/订单）→ `stats.trend`（按日趋势）→ `stats.category`（分类点击率排行，sortBy/sortDirection 白名单）。

## 治理

- 无效门店绑定：`invalid-store-bindings.check` → 展示明细确认 → `invalid-store-bindings.remove`（removedCount 核验）。
- 下线活动导航：`offline`（已下线可重新发布）；设兜底：`set-default`。
