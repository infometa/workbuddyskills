# 商品域 — 类目、品牌与基础数据维护流程

> 对应契约：`apis/product/category-brand-query.md`（类目树/选项/搜索、品牌选项/分页/详情/关联商品、按类目查描述属性）、`apis/product/category-brand-action.md`（类目批量维护、品牌增改删/Logo上传/绑定解绑）、`apis/product/description-attribute-query.md` 与 `apis/product/description-attribute-action.md`（描述属性维护）、`apis/product/extension-field-query.md` 与 `apis/product/extension-field-action.md`（扩展字段配置）、`apis/product/product-group.md`（分组选项）。概念知识：`references/domains/product-concepts.md`；写操作共同纪律见 `product-core.md`。

---

## 字典查询（发品前置）

1. **类目树**：`ops.product.category.tree`（全量树，取 `categoryCode`；类目名称不能代替编码）；深层类目定位可用 `ops.product.category.search`（keyword → categoryCode + path）
2. **品牌选项**：`ops.product.brand.options`（取 `id` 作为 `brandId`；品牌名不能代替 ID）
3. **分组选项**：`ops.product.group.options`

## 类目结构维护

1. **读现态**：`category.tree` 确认目标类目位置与子类目
2. **执行**：`ops.product.category.batch-save`（additions/updates/deletions/sortChanges 四组可混合；一次提交）
3. **核验**：回读 `category.tree`
- 🔴 删除前置：目标类目必须**无子类目且未挂商品**（先 tree + spu.search 按 categoryCode 确认）；同级名称唯一。

## 品牌维护

1. **查品牌**：`ops.product.brand.page`（管理视角）→ 取 `records[].id`
2. **建/改**：`brand.create` / `brand.update`（名称 ≤50 字符重名拒绝）；logo 先 `brand.upload-logo`（jpg/jpeg/png ≤2MB）上传取 URL
3. **绑定/解绑商品**：`brand.bind-spus` / `brand.unbind-spus`（`{spuIds:[...]}`；spuIds 来自 spu.search）
4. **删除**：🔴 `brand.delete` 前置——品牌下无关联 SPU（先 `brand.spus` 确认并解绑）；确认品牌名后执行

## 描述属性维护

1. **查列表**：`ops.product.description-attribute.page`（按类目/名称过滤）
2. **建/改**：`description-attribute.create` / `update`（update 的 attributeValues **全量覆盖** ≤20——先读现态保留未涉及的旧值）；同类目属性名唯一
3. **删除**：🔴 `description-attribute.delete` 确认属性名后执行
- 发品参考（按类目查属性+预设值）用 `description-attribute.by-category`（见 category-brand-query.md）。

## 扩展字段配置

1. **查台账**：`ops.product.extension-field.search`（按层级/类型/状态筛选）
2. **建/改**：`extension-field.create` / `update`（fieldCode+targetLevel 唯一；选择类字段 optionConfig=`[{code,label}]`、条件必填 linkageConfig=`[{field,operator,value}]`——⚠️ linkageConfig 服务端不解析，CONDITION 必填仅前端表单消费，服务端只强制 ALWAYS）
3. **启停**：`extension-field.set-enabled`（停用优先于删除）
4. **排序**：`extension-field.sort`（items 批量）
5. **删除**：🔴 `extension-field.delete` 确认字段名后执行

⛔ 平台类目一键同步、分类导航 ES/Redis 重建为运维面，不开放。
