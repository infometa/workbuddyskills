# 商品域 — 仓库库存管理流程

> 对应契约：`apis/product/inventory-query.md`（库存/流水/仓库/导出/导入任务）、`apis/product/inventory-action.md`（调整/初始化/批量导入）、`apis/product/spu-query.md`（SPU 聚合口径）、`apis/product/spu-status-action.md`（分门店库存保存）。概念知识：`references/domains/product-concepts.md`；写操作共同纪律见 `product-core.md`。

---

## 库存查询

**场景**：运营查看商品库存。

### 操作步骤

1. **SPU 聚合口径**：`ops.product.spu.search` 返回 `totalStock`（⚠️ `remainStock` 列表查询恒为 null——剩余库存以 `spu.skus` 或库存查询为准；租户聚合，缺失≠0）
2. **SKU 跨仓库聚合**：`ops.product.spu.skus` → 各 SKU 的 `totalStock`（跨仓库 SUM）
3. **仓库维度明细**：`ops.product.inventory.search`
   - 按 `warehouseId`/`skuId`/`spuId`/`warehouseType` 筛选
   - 返回 physicalQty（总）/ lockedQty（占用）/ availableQty（可售=总-占用）
4. **口径提醒**：门店预留（reservedQty）≠ 订单占用（lockedQty）；搜索聚合数不能替代门店可售库存

## 调整库存

1. **查现态**：`ops.product.inventory.search` 取 `records[].id`（库存记录ID）、当前数量与 `version`（乐观锁）
2. **用户确认**：调整方式与数量（SET/ADD/SUBTRACT）；数量必须用户明确给值
3. **执行**：`ops.product.inventory.adjust`（携带 version）
4. **回读核验**：重新 `ops.product.inventory.search` 确认
- 首次无库存记录的组合先 `ops.product.inventory.init` 初始化（可选仓库先查 `ops.product.inventory.warehouses` 取 warehouseId）
- 调低总库存可能联动下调门店预留（响应含 warning，如实转达）
- **超时禁止盲目重试 ADD/SUBTRACT**（可能重复加减）；version 冲突（并发）时重新查询后再确认
- 分门店库存分配：`ops.product.spu.store-stock`
- 变动历史排查：`ops.product.inventory.log-search`（skuId+warehouseId 必填，按 changeType 筛选）

## 库存导入（批量调整的文件形态）

1. **确认**：用户明确要批量导入并已备好 Excel（≤5000 行、≤10MB；模板从管理后台「库存-导入」获取）；提交前先读文件核对行数与必填列（SKU ID / 仓库编码 / 操作类型 / 数量）——若文件是含示例行的原始模板，须先移除示例行或与用户确认，否则示例行会进入导入任务失败
2. **提交**：`ops.product.inventory.import`（异步受理，立即返回 taskId）
3. **轮询**：`ops.product.inventory.import-task`（每 2~5 秒一次）直到终态：`SUCCESS` / `PARTIAL_FAIL` / `FAIL`
4. **报告**：全部成功报告数量；`PARTIAL_FAIL` 报告成功/失败行数并 `ops.product.inventory.import-failure-url` 取失败明细下载链接转告用户核对；`FAIL` 报告 failureReason

## 库存导出

1. **确认范围**：全量（exportScope=ALL）或按筛选（FILTERED + warehouseId/warehouseType/spuId/keyword）
2. **执行**：`ops.product.inventory.export` → 拿 `downloadUrl`（60 分钟时效）转告用户自行下载
- 门店商品清单导出同理：`ops.product.store-product.export`（筛选与门店商品搜索同构）
