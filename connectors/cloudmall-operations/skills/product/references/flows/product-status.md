# 商品域 — 商品上下架与状态管理流程

> 对应契约：`apis/product/spu-status-action.md`（上下架/隐藏/推荐/批量/删除/分配门店）、`apis/product/spu-query.md`（检索/详情/SKU 行/Tab 计数）。概念知识：`references/domains/product-concepts.md`，状态机：`references/domains/product-enums.md`；写操作共同纪律见 `product-core.md`。

---

## 上下架与状态管理

**场景**：运营管理商品的可售状态。

### 操作步骤

1. **查询商品列表**：`ops.product.spu.search`
   - 按 `statusTab` 筛选：ALL/ON_SALE/OFF_SALE/HIDDEN
   - 可用 `ops.product.spu.tab-count` 先看各状态数量级
2. **状态操作**（`当前运行时的 Capability 写操作执行器`，均需明确用户意图 + 已确认的 spuId）：
   - 上架：`ops.product.spu.on-shelf`（非草稿、未隐藏）
   - 下架：`ops.product.spu.off-shelf`（非草稿、未隐藏）
   - 隐藏：`ops.product.spu.hide`（非草稿）
   - 取消隐藏：`ops.product.spu.unhide`
   - 推荐（toggle）：`ops.product.spu.recommend`——执行前查 `isRecommended`，执行后回读确认；超时禁盲目重试（toggle 可能反转）
   - 单次提交、原样返回；执行前读现态（已是目标状态无需执行），执行后回读确认；超时先查状态
3. **批量操作**（≤200 条，先向用户复述对象清单）：
   - 批量上架/下架/隐藏/取消隐藏：`ops.product.spu.batch-on-shelf` / `batch-off-shelf`（⚠️ 字段名 `spuIds`）/ `batch-hide` / `batch-unhide`
   - 批量改价：`ops.product.spu.batch-update`（**仅 field=price**，元字符串；⚠️ 会抹平该 SPU 全部活跃 SKU 价格，多规格慎用）
   - 批量结果原样返回（含成功/失败明细），**逐条报告**，不把 HTTP 成功当全部业务成功

### 删除商品

- 前置：仅**草稿或已隐藏**状态可删除；在架商品需先下架并隐藏
- 🔴 不可逆：执行前必须向用户确认完整对象清单

### 业务规则
- SPU 上架 ≠ 在 C 端可售，还需门店上架 + 有库存
- "上架"不等价于"取消隐藏"——两个独立维度，不能混淆
