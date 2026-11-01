# 商品域 — 研学营期名额调整流程

> 对应契约：`apis/product/tour-session-query.md`（按门店查/跨门店聚合）、`apis/product/tour-session-action.md`（批量更新）。概念知识：`references/domains/product-concepts.md`；写操作共同纪律见 `product-core.md`。

---

## 研学营期名额调整

**场景**：研学商品按场次调整总量/预留（平台角色）。

### 操作步骤

1. **定位研学 SKU**：`store-product.search`（productType=STUDY_TOUR）→ `spu.skus` 取 `skuId`（list 必填 skuId+storeId）
2. **查现态**：`ops.product.tour-session-quota.list`（skuId+storeId 必填，取场次 `id` 与版本号）或 `aggregate`（spuId 必填，跨门店看分布）
3. **确认**：向用户复述场次日期与当前值 → 目标值
4. **执行**：`tour-session-quota.batch-update`——**仅 SINGLE_STORE 逐场次**（updates[{id, expectedVersion, totalQuota 必填, reservedQty?}]）
5. **核验**：`list` 回读名额；**版本冲突项重查后重试**（⚠️ 重试必须换新 idempotencyKey——重复 key 返回空结果造成假成功），不盲目重发

### 权限

仅平台管理员/运营角色；权限不足返回 PERMISSION_DENIED，向用户说明即可。
