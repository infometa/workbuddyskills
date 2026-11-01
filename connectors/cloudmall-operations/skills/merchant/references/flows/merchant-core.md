# 商户域 — 写操作共同执行闭环与数据流转

> 所有商户域写操作共用的执行纪律与跨能力字段来源映射；各业务族流程见 `flows/` 下对应文件，能力契约见 `references/apis/merchant/`。
> 写操作风险档位与字段确认红线以入口 SKILL.md 为准（🔴/🟡 分级不在本文件重复）；执行器为单次提交、永不自动重试。

---

## 执行闭环

写操作纪律：**先读现态、与用户确认关键参数、执行、回读核验**；写能力单次提交，超时后先查现态再决定下一步，禁止盲目重试。

- **对象定位**：按用户给出的 ID/名称及范围可靠匹配；多个候选对象时列出必要的业务差异请用户选定，不取第一条。查询结果即使唯一，名称不匹配、输入只是说明文字或目标未明确时也不能默认选中；「只读/仅查询」与写动作冲突时先澄清。对象明确后的执行授权遵守当前运行时审批模式；分页翻完前不宣称不存在。
- **字段来源**：系统可读的 ID 和状态由读取结果取得；金额、地址、编码、绑定清单等必须由用户明确给出或来自查询结果，禁止 AI 编造。
- **写前变化**：写入前对象状态改变：重新说明影响。输入缺失、未知嵌套结构或未开放依赖：停止对应写入，明确缺什么。
- **超时纪律**：写操作超时或网络错误时结果不确定（可能已提交）——先查询对象状态再向用户说明，不自动重复提交。
- **回读不明确**：报告「已提交，结果待核验」；不以列表延迟或空结果断言失败，不通过执行反向动作试探。
- **批量结果**：批量操作结果含逐条失败明细的（供应商导入等）逐条报告，不把 HTTP 成功当全部业务成功；仅计数的（门店/组织导入等）按计数报告并回读列表核对。
- **只读查询**：搜索/详情/列表/树/统计/日志无需确认直接查；供应商详情的脱敏字段（手机号等）不要求用户提供明文还原。
- **未开放能力**：不调用未开放能力，引导用户在管理后台操作。

## 数据流转依赖（跨能力字段来源）

| 目标字段 | 来源能力 |
|---------|---------|
| store.create 的 orgNodeId | `ops.merchant.org.tree`（REGION 节点 id） |
| 省市区编码/名称 | `ops.merchant.region.tree` |
| store.bind-warehouse 的 warehouseId | `ops.merchant.store.available-warehouses` 或 `ops.merchant.warehouse.search` |
| store.bind-pickup-site 的 pickupSiteId | `ops.merchant.store.available-pickup-sites` 或 `ops.merchant.pickup-site.search` |
| warehouse.bind-delivery-methods 的 deliveryIds | `ops.merchant.delivery-method.list` |
| warehouse.bind-delivery-blocks 的 blockIds | `ops.merchant.delivery-area-block.search` |
| warehouse.bind-block-template 的模板 id | `ops.merchant.freight-template.search` / `ops.merchant.fulfillment-template.search` |
| fixed-area.create 的 orgNodeId | `ops.merchant.org.tree` |
| entry-rule.update-params 的 defaultStoreId | `ops.merchant.store.picker` |
| rerank_manual 的 actionValue（商品 ID） | 商品域 SPU/SKU 查询能力 |
| supplier.update 的 expectedVersion | `ops.merchant.supplier.detail` 的 `version` 或 draft 的 `sections[].version` |
| supplier.license-ocr 的 materialId | `ops.merchant.supplier.detail` 的 `enterpriseInfo.licenseMaterialId`（素材先经 material.upload 上传） |
| supplier.profile-review 的 sectionKey | detail 的 `profileReviews[].sectionKey`（仅 reviewing 状态） |
| category-nav.store-visibility.update 的 storeIds | `ops.merchant.store.search` / `ops.merchant.store.options` |
| category-products.add 的 spuIds | 商品域 `ops.product.spu.search` |
| link-backend-category 的 backendCategoryCodes | 商品域 `ops.product.category.tree` |
| front-category.batch-save 的 parentId | 分类树出参（"0"=根；新增用响应 idMapping 的真实 ID） |
| store-isolation.batch-add 的 storeIds | `ops.merchant.store.search`（先经 store-ids 排除已隔离项） |
