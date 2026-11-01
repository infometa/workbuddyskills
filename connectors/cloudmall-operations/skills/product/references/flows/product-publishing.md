# 商品域 — 商品发布、编辑与审核流程

> 对应契约：`apis/product/spu-action.md`（创建/编辑/草稿/导入/媒体/审核）、`apis/product/spu-query.md`（检索/详情/SKU 行/草稿读取/审核计数）、`apis/product/category-brand-query.md` 与 `apis/product/product-group.md`（发品字典）、`apis/product/description-attribute-query.md`（描述属性参考）。概念知识：`references/domains/product-concepts.md`；写操作共同纪律见 `product-core.md`。

---

## 商品发布（创建 SPU）

**场景**：运营创建新商品。

### 操作步骤

1. **准备基础数据**（字典查询，`当前运行时的 Capability 查询执行器`）：
   - 类目树：`ops.product.category.tree` → 获取 `categoryCode`
   - 品牌选项：`ops.product.brand.options` → 获取 `brandId`（PHYSICAL/VIRTUAL 必填；SERVICE/STUDY_TOUR 可空）
   - （可选）分组选项：`ops.product.group.options` → 获取 `groupId`

2. **收集素材**：
   - 主图 1~5 张（第一张为主图）、可选视频/详情素材
   - 用户可直接提供图片/视频文件（经 `ops.product.spu.upload-media` 上传取 URL），或提供已在云MALL可访问的图片 URL；用户给不出的素材应说明缺少的材料，不把陌生 URL 当可信内部素材

3. **确认表单**（对话复述）：
   - 必填：`spuName`（4~256 字符）、`productType`、`categoryCode`、`images`、`specMode`、`skuList`
   - `specMode=SINGLE` 时 SPU 顶层 `price` 必填；MULTI 时各 SKU `price` 必填
   - SKU 1~500 个

4. **创建商品**（`当前运行时的 Capability 写操作执行器`）：`ops.product.spu.create`
   - 返回新建 `spuId` 并回读详情核验商品名一致
   - 完整参数表 → `apis/product/spu-action.md`

5. **（可选）表单未填完先存草稿**：`ops.product.draft.save`
   - `productData` 为完整表单 JSON 快照；覆盖保存时传 `draftId`

### 参数数据流

`category/tree → categoryCode`、`brand/options → brandId`、用户提供的图片 URL → `images[]`，均进创建请求。

### 异常处理
- `INPUT_INVALID`：对照 spu-action.md 参数表修正（品牌条件必填、价格精度(8,2)≥0.01、图片 1~5 张）
- `PERMISSION_DENIED`：当前账号无创建权限，停止并说明
- 超时/网络错误：结果不确定——用 `ops.product.spu.search` 按商品名查是否已创建，确认未创建后才可重新提交

### 后续步骤：分配到门店（如需上架到门店）
1. **分配门店**（`当前运行时的 Capability 写操作执行器`）：`ops.product.spu.assign-stores`（单 SPU）或 `ops.product.spu.batch-assign-store`（多 SPU），传目标 `storeIds`（≤100，来自用户提供或商户域门店清单）
2. 分配后门店级上下架/门店价/预留由门店商品能力管理（见 `product-store.md` 与 `store-product-action.md`）

---

## 商品编辑

**场景**：运营修改已有商品信息。

### 操作步骤

1. **查询现态**：`ops.product.spu.detail`（如需 SKU：`ops.product.spu.skus`）
2. **对话确认变更**：更新是**全量覆盖**——复述将保留的字段、将修改的字段、SKU 增删变化（未传的已有 SKU 会被**归档**下架而非物理删除，数据保留供订单/售后反查）；保留用户没有要求修改的字段；`productType` 不可变
3. **提交更新**（`当前运行时的 Capability 写操作执行器`）：`ops.product.spu.update`
   - 已有 SKU 传 `skuId`（更新），新增 SKU 不传（系统生成）
   - 不接收 `source` 和 `isHidden`
4. **查看变更记录**：`ops.product.spu.change-logs`

### 参数来源

`{id}` 取搜索 `ops.product.spu.search` 响应的 `records[].spuId`；完整参数表 → `apis/product/spu-action.md`。

---

## 草稿管理

**场景**：商品表单未填完先保存，之后继续编辑。

### 操作步骤

1. **保存草稿**（`当前运行时的 Capability 写操作执行器`）：`ops.product.draft.save`
   - `productData` 为完整表单 JSON 快照；首次不传 `draftId`，覆盖保存时传入
2. **查草稿列表**：`ops.product.draft.search`（按当前用户过滤；`spuName`/`keyword`/`categoryCode`/`productType` 筛选）
3. **读草稿详情**：`ops.product.draft.detail` → `productData` 恢复表单继续编辑
4. **删除草稿**：`ops.product.draft.delete`（🔴 不可逆，先向用户复述草稿标题确认）

---

## 商品批量导入

1. **确认**：用户明确要导入商品 Excel（≤5000 行、≤10MB；模板从管理后台获取）
2. **提交**：`ops.product.spu.import`（**同步执行**，处理完才返回——大文件响应较慢属正常）
3. **报告**：返回 totalCount/successCount/failureCount；有失败时失败明细下载为文件流（未开放），建议用户在管理后台下载核对

---

## 商品审核

**场景**：待审核商品（REVIEWING）的通过与驳回（导购发品/供应商来源的审核工作台）。

### 操作步骤

1. **总览**：`ops.product.spu.audit-status-count`（各审核状态数量）→ **找待审对象**：`ops.product.spu.search`（按审核状态过滤）→ 取 `records[].spuId`
2. **看资料**：`ops.product.spu.detail` + `spu.skus`（必要时看草稿详情）——审核依据充分再动手
3. **执行**：通过 `ops.product.spu.audit-approve`（单条 spuId 或批量 spuIds）；驳回 `ops.product.spu.audit-reject`（**仅单条无批量**；auditRemark 必填，写具体可行动的原因）
4. **核验**：`spu.search`/`spu.detail` 回读审核状态

### 业务规则

- 审核通过 ≠ 已上架：需要上架另走 SPU 上架 + 门店上架流程（见 `product-status.md` / `product-store.md`）。
- **可审对象**：仅 `auditStatus=REVIEWING` 且来源 GUIDE_PUBLISH/SUPPLIER（导购发品/供应商）的商品——ADMIN 自建商品不走此审核；按 createSource 过滤待审清单。
- **批量整批回滚**：批量通过任一条不满足前置则全批失败（无部分成功）；返回 Void 无逐条结果，以回读核验。
