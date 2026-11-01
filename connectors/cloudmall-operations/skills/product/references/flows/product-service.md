# 商品域 — 到店服务与预约模板管理流程

> 对应契约：`apis/product/store-service-query.md`（服务分页/详情、模板分页/选项/详情）、`apis/product/store-service-action.md`（服务增改/上下架/删除、模板增改删）。概念知识：`references/domains/product-concepts.md`；写操作共同纪律见 `product-core.md`。

---

## 到店服务与预约模板管理

**场景**：配置到店履约的预约类服务（讲解/体验等）：先建预约模板，再建服务并绑定模板，控制发布与上下架。

### 操作步骤

1. **建预约模板**（如无可用模板）：`ops.product.appointment-template.options` 查现有 → 不满足则 `appointment-template.create`（名称唯一；营业时段 HH:mm；粒度 30/60/120；提前预约规则）
2. **建服务**：`ops.product.store-service.create`——`storeScope`（all/specified，specified 用 storeAssignments 做门店差异化模板）；**发布（isDraft=false）时 templateId 必填**，未定型先存草稿（isDraft=true）
3. **编辑**：`store-service.update`（serviceItems 全量覆盖：更新项传原 id）；⚠️ **返回 overBookedSlots 超卖警告时必须如实转告**（被预约引用时段因下调人数上限而超卖）
4. **上下架**：`store-service.on-shelf` / `off-shelf`；**删除**：🔴 `store-service.delete` 确认服务名后执行
5. **模板维护**：`appointment-template.update` / `delete`——delete 被服务引用时拒绝（先解除关联）；改动被在架服务引用的模板时段前先评估影响
