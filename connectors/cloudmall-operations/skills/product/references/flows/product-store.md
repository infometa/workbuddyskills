# 商品域 — 门店商品运营流程

> 对应契约：`apis/product/store-product-query.md`（搜索/SKU/库存明细/日志/导出/状态计数）、`apis/product/store-product-action.md`（上下架/档位/门店价/预留/审核/分配门店）。概念知识：`references/domains/product-concepts.md`，状态机：`references/domains/product-enums.md`；写操作共同纪律见 `product-core.md`。

---

## 门店商品运营

**场景**：SPU 分配到门店后，控制门店维度的可售性、价格与预留库存。

### 操作步骤

1. **定位门店商品**：`ops.product.store-product.search`（按门店/状态/名称）→ 取 `records[].id`（storeProductId）
2. **看现态**：`store-product.skus`（SKU 档位/门店价）、`store-product.inventory-detail`（预留/库存）
3. **执行**（按需选一）：
   - 门店上下架：`store-product.on-shelf`/`off-shelf`（单条）或 `batch-on-shelf`/`batch-off-shelf`（批量 ids）
   - SKU 档位：`store-product.sku-toggle-shelf`（单条翻转——**先确认当前档位**）或 `batch-sku-toggle-shelf`（action=ON_SHELF/OFF_SHELF）
   - 门店价：`sku-store-price`（单 SKU，storePrice 必传——恢复全局价暂不可用，需后台操作；⚠️ 单条路径无下限校验，价格必须用户明确给合法正数）或 `batch-sku-store-price`（items 清单，校验 ≥0.01）——**价格先向用户确认**
   - 预留库存：`reserved-qty`（带 expectedOldQty 乐观锁，当前值取 `store-product.skus` 该 SKU 的 `reservedStock`）或 `batch-reserved-qty`（≤100，整批拦截）
   - 门店审核（导购发品）：`store-product.audit`（REJECT 必填 rejectReason）
4. **核验**：回读 `store-product.search`/`skus`/`inventory-detail`

### 异常处理

- 乐观锁冲突（expectedOldQty/版本不一致）：重新查询现态后与用户确认再重试，不盲目重发。
