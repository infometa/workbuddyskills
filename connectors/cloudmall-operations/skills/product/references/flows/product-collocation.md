# 商品域 — 搭配管理流程

> 对应契约：`apis/product/collocation-query.md`（分页/详情/看板/海报配置查询/投放物料）、`apis/product/collocation-action.md`（创建/编辑/上下线/删除/图片上传/海报保存/投放重试）。概念知识：`references/domains/product-concepts.md`；写操作共同纪律见 `product-core.md`。

---

## 搭配管理

**场景**：单店商品组合（搭配套餐）的创建、上线与发布审核。

### 操作步骤

1. **看数据**：`ops.product.collocation.dashboard`（timeRange=LAST_7_DAYS 等）或 `collocation.search` 定位搭配 → 取 `records[].id`
2. **看结构**：`collocation.detail`（编辑前必读——编辑为全量覆盖）
3. **执行**：
   - 创建/编辑：`collocation.create` / `update`（storeId + name（6~10 字）+ hasMainImage + showRecommendInDetail + products[{spuId, sortOrder, 锚点}]（2~3 项）；表单先与用户确认）。⚠️ 搭配主图 `mainImageUrl` 服务端**不校验归属**（任意 URL 落库）——只用 `collocation.upload-image` 上传结果或用户明确给的可信 URL；租户校验仅海报配置链路有
   - 上/下线：`collocation.online` / `offline`
   - 删除：`collocation.delete`（🔴 不可逆，确认对象与名称）
4. **核验**：`collocation.search` / `detail` 回读状态

### 海报与投放物料（搭配发布链路）

1. **上传图片**：搭配商品图用 `collocation.upload-image`（JPEG/PNG/WebP ≤5MB）；**海报主图必须用 `collocation.poster-image`**（≤2MB，返回 30 分钟签名 URL）
2. **配置海报文案**：`collocation.poster-config-get` 读现态 → `collocation.poster-config-save`（mainTitle ≤12 字必填；⚠️ mainImageUrl 须来自 poster-image 上传结果——租户目录强校验，素材中心/外链 URL 被拒）
3. **取投放物料**：`collocation.launch-material`（envVersion 必填）——返回 GENERATING 时稍后重查；物料失败时 `collocation.launch-material-retry`（仅 FAILED 可重试，否则 409）

### 边界

- 体验版预览码重试（legacy trial 面）与投放动作审计埋点未开放，不属运营执行能力。
