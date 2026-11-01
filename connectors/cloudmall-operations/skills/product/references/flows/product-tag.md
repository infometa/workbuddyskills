# 商品域 — 静态标签运营流程

> 对应契约：`apis/product/static-tag-query.md`（标签分页/关联 SKU 列表）、`apis/product/static-tag-action.md`（绑定/定义维护/删除）、`apis/product/spu-query.md`（SKU 搜索定位规格）。概念知识：`references/domains/product-concepts.md`；写操作共同纪律见 `product-core.md`。

---

## 静态标签运营

**场景**：给 SKU 打运营标签（如"热销"）、调整标签关联，或维护标签定义本身。

### 操作步骤（SKU 打标/调关联）

1. **找标签**：`ops.product.static-tag.search` → 取 `records[].id`
2. **看现关联**：`static-tag.skus`（避免误解绑）
3. **找 SKU**：`ops.product.sku.search`（跨 SPU 定位规格）
4. **执行**：`static-tag.bind-skus`（**全量提交**：skuIds 为最终关联全集，服务端差量增删；空数组=清空，谨慎）——执行前向用户复述新增/移除清单
5. **核验**：`static-tag.skus` 回读关联结果

### 标签定义维护

1. **新建**：`static-tag.create`（名称 ≤10 字符、优先级 1~9999、有效期 PERMANENT/CUSTOM——CUSTOM 须 validFrom+validTo 成对）
2. **编辑**：`static-tag.update`（全量字段；先读分页现态）或仅调优先级 `static-tag.priority`
3. **删除**：🔴 `static-tag.delete` / `batch-delete`（≤200）不可逆——确认标签名清单；有关联 SKU 时先看 `static-tag.skus` 评估影响面
