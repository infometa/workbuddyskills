# 商品域 — SPU 检索与单笔事实读取契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-publishing.md`（草稿）等；写操作见 `spu-action.md`（创建/编辑/草稿/导入/媒体/审核）与 `spu-status-action.md`（上下架/删除/分配门店）。
> 所有 ID 均为十进制字符串；出参为上游**原始业务数据**（不裁剪字段）。按「关键字段来源 / 枚举 / 格式敏感 / 脱敏」四类标注，未列出的展示型字段以后端实际返回为准，透传给用户即可。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引（前缀 `ops.product.`）：spu.search 商品分页搜索 · spu.tab-count 状态Tab计数 · spu.detail 基础详情 · spu.skus SKU行 · spu.change-logs 变更记录 · sku.search SKU检索 · spu.audit-status-count 审核状态计数 · draft.search 草稿列表 · draft.detail 草稿详情 · benefit.coupon-templates 可用券模板

---

## ✅ SPU 分页搜索 — ops.product.spu.search

**排序口径**：无关键词、无显式排序时，服务端按 `createdTime` 降序返回；本开放契约没有可用的 `updatedTime` 排序入参。用户问「最近更新」时，不得把第一页当作最近更新；若匹配总数不超过 100，可用 `pageSize:100` 取齐后按返回的 `updatedTime` 降序选取。超过 100 条时，须继续分页取齐才能保证全量排名；不能取齐就明确说明无法保证全租户的最近更新顺序。不要在未核实的情况下声称管理后台有「更新时间倒序」筛选。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | — | 默认 1 |
| pageSize | Integer | — | 默认 20（建议 ≤100） |
| keyword | String | 否 | 聚合搜索（spuName/subtitle/spuId/skuIds/externalSpuId/externalSkuIds 六字段 OR） |
| productType | String | 否 | `PHYSICAL`/`SERVICE`/`STUDY_TOUR`（VIRTUAL 未进入此筛选契约） |
| categoryCodes | String[] | 否 | 类目编码数组，不能以类目名称替代 |
| brandId | String | 否 | 品牌ID（十进制字符串） |
| statusTab | String | 否 | `ALL`/`ON_SALE`/`OFF_SALE`/`HIDDEN`（未知值视为 ALL）；不存在 SOLD_OUT |
| auditStatus | String[] | 否 | `NONE`/`REVIEWING`/`APPROVED`/`REJECTED` |
| createSource | String | 否 | `ADMIN`/`GUIDE_PUBLISH`/`SUPPLIER` |
| storeId | String | 否 | 关联门店筛选；返回库存仍是租户聚合口径 |

其他后端支持的字段（categoryCode 单选/deliveryMethod/sortField 等）不在本契约维护范围——按本表传参即可，不要自行扩充入参。

⚠️ **extensionFieldFilters（按扩展字段筛选）在开放调用链上不可用**：该参数为嵌套对象（`fieldCode → 值列表`），而本能力为 GET query 传输——调用链层对 query 参数的对象值直接拒绝（INPUT_INVALID）。需要按扩展字段筛选商品时引导用户在管理后台操作。

### 出参（分页，原始数据）

- **关键字段来源**：`records[].spuId`（→ 详情/编辑/上下架/隐藏的 `input.id`）
- **枚举字段**：`productType`（PHYSICAL/SERVICE/STUDY_TOUR/VIRTUAL）、`source`（ADMIN/GUIDE_PUBLISH/SUPPLIER）、`isDraft`/`isHidden`/`isRecommended`（boolean）
- **格式敏感字段**：`createdTime`/`listingTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）、`price`/`minPrice`/`maxPrice`（元）、`totalStock`/`totalSales`（整数件数）。⚠️ `remainStock` 列表查询恒为 null（不在搜索数据源字段白名单）——剩余库存以 `spu.skus`/库存查询为准
- 字段缺失不等于零；库存字段为租户聚合口径，不代表门店可售库存。

### 调用示例

```json
{"capability":"ops.product.spu.search","input":{"pageNum":1,"pageSize":20,"statusTab":"ON_SALE","keyword":"研学"},"summary":"查找在售的研学商品"}
```

---

## ✅ SPU Tab 计数 — ops.product.spu.tab-count

- **语义**：各状态 Tab 数量（ALL 排除草稿；计数反映当前筛选条件）

### 入参（无分页——聚合统计）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | String | 否 | 1..100 |
| productType | String | 否 | `PHYSICAL`/`SERVICE`/`STUDY_TOUR` |
| categoryCodes | String[] | 否 | 1..10 项 |
| brandId | String | 否 | 品牌ID |

**未开放入参**：`deliveryMethod` 及其他后台筛选。

### 出参

| 字段 | 说明 |
|------|------|
| allCount | 全部非草稿数量 |
| onSaleCount | 可售（未隐藏 + SKU 聚合可售） |
| offSaleCount | 不可售（未隐藏 + SKU 聚合不可售） |
| hiddenCount | 已隐藏 |

### 调用示例

```json
{"capability":"ops.product.spu.tab-count","input":{"keyword":"研学"},"summary":"统计研学商品的各状态数量"}
```

---

## ✅ SPU 基础详情 — ops.product.spu.detail

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | SPU 业务ID——**字段名与出参一致，统一为 `spuId`**（取搜索/创建记录的 `spuId` 字段）；不能用 SKU ID/门店商品ID/页序号 |

### 出参（原始数据）

- **关键字段来源**：`spuId`（→ SPU 各操作能力的 input.spuId，字段名一致）、`skuList[].skuId`（→ 更新时传 `skuList[].skuId` 保留该 SKU）
- **枚举字段**：`productType`、`isDraft`/`isHidden`/`isGift`（boolean）、`auditStatus`
- **格式敏感字段**：`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）、`price`/`minPrice`（元）、`priceDescription`（商品详情图文 HTML，字段名虽叫"价格说明"，实际承载完整商品详情富文本）
- **结构化字段**（编辑回填锚点）：
  - `images`：string[]；`detailMedia[]`：对象数组 `{type: "image"/"video", url, sortOrder}`（与创建入参同构）。⚠️ 出参的 `images`/`detailMedia[].url`/`video`/`skuList[].specImage` 及 `spuExtensionFields.shareImage` 均为**实时预签名 URL**（带时效签名参数）——回传作编辑入参无害（入库前服务端自动剥离签名参数），但不要把带签名 URL 当永久素材地址存档
  - `attributes[]`：`{name, value, sortOrder}`（与创建入参同构）
  - `spuExtensionFields`：**三层包装结构** `{fieldCode: {value, displayValue, fieldType}}`（targetLevel=ALL 的字段另含 `source: "ALL"`）——与创建/编辑入参的裸值形态**不同**，编辑回填时取每个字段对象的 `.value`；`displayValue` 为展示文本（选项类字段是选项名），`fieldType` 为字段类型
  - `skuList[].skuExtensionFields`：同上三层包装结构
  - `benefitConfig`（仅 VIRTUAL 商品）：聚合 VO `{benefitType, couponTemplateId, couponName, couponSubCode, couponStatus, useExpireStart, useExpireEnd}`——`couponName` 等跨域字段来自促销中心 Feign，促销中心不可用时为 null；`useExpireStart/End` 为毫秒时间戳
  - `hasSuccessOrder`（仅 VIRTUAL 商品）：是否已产生成功订单（权益编辑锁定判定）；当前实现跨域判定源缺失、恒为 false 兜底，不要依赖它做锁定判断
- 详情含**活跃 SKU 列表**（`skuList[]`，与 `spu.skus` 同源）与 `auditStatus`；不含审核原因。没有 SKU 信息时不得回答"全部规格都可售"。

### 调用示例

```json
{"capability":"ops.product.spu.detail","input":{"spuId":"2058365707555589633"},"summary":"核对选定商品的基础详情"}
```

---

## ✅ SPU 的 SKU 行 — ops.product.spu.skus

- **语义**：SPU 行展开的活跃 SKU 子行（DB 强一致；归档 SKU 不返回）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | SPU 业务ID |

### 出参（数组，原始数据）

- **关键字段来源**：`skuId`（→ 库存查询筛选）、`skuList[].skuId`（→ 更新时传 `skuList[].skuId` 保留该 SKU）
- **枚举字段**：`status`（ENABLED/DISABLED）；SPU 可售 = 任一 SKU ENABLED
- **格式敏感字段**：`price`（元，精度(8,2)）、`totalStock`（跨仓库 physicalQty 聚合，整数）
- `specInfo` 为 JSON 字符串，内部结构为**对象映射**：`{"颜色":"红色","尺码":"L"}`（规格维度名 → 维度值）
- `skuExtensionFields` 为**三层包装结构** `{fieldCode: {value, displayValue, fieldType}}`（编辑回填取 `.value`，同 `spu.detail`）

### 调用示例

```json
{"capability":"ops.product.spu.skus","input":{"spuId":"2058365707555589633"},"summary":"查看商品的SKU规格与可售状态"}
```

---

## ✅ 商品变更记录 — ops.product.spu.change-logs

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | SPU 业务ID |
| pageNum | Integer | ✅ | ≥1 |
| pageSize | Integer | ✅ | 1..100 |

### 出参（分页，原始数据）

- **枚举字段**：`operationType`（如 UPDATE）
- **格式敏感字段**：`createdTime`（yyyy-MM-dd HH:mm:ss）
- `changedFields` 为数组，每项：`fieldName`（字段名）、`fieldLabel`（中文标签）、`oldValue`、`newValue`

### 调用示例

```json
{"capability":"ops.product.spu.change-logs","input":{"spuId":"2058365707555589633","pageNum":1,"pageSize":20},"summary":"查看商品最近的变更记录"}
```

---

## ✅ SKU 搜索 — ops.product.sku.search

- **语义**：按关键词搜索 SKU（四路召回：SKU 编号精确 + 商家 SKU 编码 + SKU 名称 + SPU 名称），跨 SPU 定位具体规格
- **实现说明**：走 ES 索引，不做类目/状态/租户过滤，返回全库匹配；适合定位具体规格，不适合按条件筛选商品清单（条件筛选用 `spu.search`）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | ✅ | ≥1 |
| pageSize | Integer | ✅ | 1..100 |
| keyword | String | 否 | SKU 编号或商品名称关键词 |

### 调用示例

```json
{"capability":"ops.product.sku.search","input":{"pageNum":1,"pageSize":20,"keyword":"红色"},"summary":"搜索红色规格的SKU"}
```

---

## ✅ 审核状态计数 — ops.product.spu.audit-status-count

- **语义**：审核工作台入口——先看各审核状态数量再定位待审清单

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | String | — | 商品名/关键词 |
| productType | String | — | 商品类型（如 `STUDY_TOUR`） |
| statusTab | String | — | 状态 Tab（同 spu.search） |
| categoryCodes | String[] | — | 类目编码列表 |
| createSource | String | — | 创建来源过滤 |

### 出参（原始返回）

`data` 为四桶审核状态计数：`{all, pending（=REVIEWING 待审）, approved, rejected}`。

### 调用示例

```json
{"capability":"ops.product.spu.audit-status-count","input":{"productType":"STUDY_TOUR"},"summary":"查看研学类商品各审核状态数量"}
```

---

## ✅ 草稿列表 — ops.product.draft.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | ✅ | ≥1 |
| pageSize | Integer | ✅ | 1..100 |
| spuName | String | 否 | 商品名称模糊 |
| keyword | String | 否 | 关键词 |
| categoryCode | String | 否 | 类目编码 |
| productType | String | 否 | `PHYSICAL`/`SERVICE`/`STUDY_TOUR`/`VIRTUAL` |

**未开放入参**：`deliveryMethod`。

### 出参（分页，原始数据）

- **关键字段来源**：`records[].draftId`（→ 草稿详情/覆盖保存）
- **格式敏感字段**：`updatedTime`（yyyy-MM-dd HH:mm:ss）、`price`（string，元）
- `price` 为从表单快照提取的价格字符串（元）。

### 调用示例

```json
{"capability":"ops.product.draft.search","input":{"pageNum":1,"pageSize":20},"summary":"查看我的商品草稿列表"}
```

---

## ✅ 草稿详情 — ops.product.draft.detail

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| draftId | String | ✅ | 草稿ID（字符串业务标识，非雪花） |

### 出参（原始数据）

- **格式敏感字段**：`createdTime`/`updatedTime`（yyyy-MM-dd HH:mm:ss）
- `productData`：完整表单 JSON 字符串（结构同创建入参），用于恢复表单继续编辑。

### 调用示例

```json
{"capability":"ops.product.draft.detail","input":{"draftId":"draft-8f3c2a1b"},"summary":"读取草稿恢复表单"}
```

---

## ✅ 可用优惠券模板 — ops.product.benefit.coupon-templates

- **语义**：虚拟商品关联优惠券的选择器数据源。跨域实时查询促销中心，**仅返回可用状态**的券模板；促销中心不可用时降级返回空分页（此时应提示用户稍后再试）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | ✅ | 页码 |
| pageSize | Integer | ✅ | 每页条数（≤100） |
| keyword | String | — | 券名称模糊匹配 |
| couponSubCode | String | — | 券子类型过滤 |

### 出参（`PageResult`，原始数据）

- **关键字段来源**：`records[].couponTemplateId`（→ SPU 创建/编辑关联券的模板 ID）、`records[].sourcePromotionId`（→ benefitConfig 必填的促销活动 ID，与模板 ID 成对取用）
- **格式敏感字段**：`acquireExpireStart/End`、`useExpireStart/End`（毫秒时间戳）；`useExpireDuration`（秒）
- **枚举字段**：`couponStatus`、`useExpireType`（1=固定时间段；2=领取后 N 天，此时 useExpireEnd 为 null）

### 调用示例

```json
{"capability":"ops.product.benefit.coupon-templates","input":{"pageNum":1,"pageSize":20,"keyword":"满减"},"summary":"查找可关联的满减券模板"}
```

---

## ⛔ 未开放能力（后台存在，当前开放能力集未包含）

| 业务能力 | 说明 |
|------|------|
| 商品列表导出 | 文件流型导出（产品决策仅开放 URL 型导出，走管理后台） |
| 导入模板下载 / 失败明细下载 | 文件流下载，走管理后台 |
| ES 重建 / 索引同步 | 运维面，不开放 |

> 需要这些能力时：整理操作对象与待确认变更，引导用户在管理后台操作；不承诺已执行。
