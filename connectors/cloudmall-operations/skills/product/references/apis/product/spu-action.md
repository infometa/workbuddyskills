# 商品域 — 商品发布与审核写操作契约

> 概念知识：`references/domains/product-concepts.md`，状态与枚举：`references/domains/product-enums.md`；运营流程：`references/flows/product-publishing.md`；检索与单笔事实读取（搜索/详情/SKU 行/草稿读取）先读 `spu-query.md`。
> 所有 ID 均为十进制字符串；写操作须遵守入口 Skill 的风险档位、明确确认和回读纪律。
> **工具**：`当前运行时的 Capability 写操作执行器`（`mall.action`）——单次提交、不自动重试，超时或结果不确定先回读。
> 能力索引（前缀 `ops.product.`）：spu.create 创建商品 · spu.update 编辑商品 🔴 · draft.save 草稿保存 · draft.delete 删除草稿 🔴 · spu.import Excel导入 · spu.upload-media 媒体上传 · spu.audit-approve 审核通过 🔴 · spu.audit-reject 审核驳回 🔴

---

## ✅ 创建商品 — ops.product.spu.create

- 只在用户明确要求创建并确认表单后调用；执行语义为单次提交、原样返回。**超时/网络错误时结果不确定（可能已创建）——先用搜索按商品名查是否已存在，确认未创建后才可重新提交**

### 入参（运营端来源）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuName | String | ✅ | 4..256 字符 |
| productType | String | ✅ | `PHYSICAL`/`SERVICE`/`STUDY_TOUR`/`VIRTUAL` |
| categoryCode | String | ✅ | 类目编码（来自 category.tree） |
| brandId | String | 条件 | PHYSICAL/VIRTUAL 必填；SERVICE/STUDY_TOUR 可空（来自 brand.options） |
| images | String[] | ✅ | 主图 URL 列表，1..5 张（第一张为主图） |
| specMode | String | ✅ | `SINGLE`/`MULTI` |
| price | Number | 条件 | SINGLE 模式必填；≥0.01，精度(8,2)，元 |
| skuList | Array | ✅ | 1..500 项（结构见下） |
| subtitle | String | 否 | ≤512 |
| groupId | String | 否 | 分组ID（来自 group.options） |
| externalSpuId | String | 否 | 商家 ERP SPU 编码，≤128；**同租户内唯一**（重复创建/改为他人已用编码会被拒绝） |
| video | String | 否 | 视频 URL，≤1024 |
| deliveryMethods | String[] | 条件 | **PHYSICAL 必填**（运营端表单必选项；服务端不拒绝为空，但为空的实物商品 C 端不可见/配送方式展示不出来——线上实抓）。配送方式 code（**小写**，大小写敏感）：`express`/`city_express`/`rider_delivery`/`self_service`，按商品实际支持勾选，创建后回读核验。**按 productType 分支的服务端行为**（静默归一不报错）：PHYSICAL 仅允许这 4 个物流码，传内置码（service_verification/virtual_fulfillment）报错；SERVICE/STUDY_TOUR **无论传什么都会被归一为 `[service_verification]`**（服务核销类，不走物流）；VIRTUAL **无论传什么都会被归一为 `[virtual_fulfillment]`**（虚拟履约）。服务/研学/虚拟商品无需传该字段（传了也会被覆盖），回读详情时看到的即归一后的内置码 |
| isGift | Boolean | 否 | 是否赠品，默认 false |
| attributes | Array | 否 | 描述属性，≤30 项：`{name(必填), value(必填), sortOrder(可选)}`——name/value 均不能为空（服务端 @NotBlank）；value 一律字符串——多选预设值**逗号拼接**；预设值按类目来自 `ops.product.description-attribute.by-category`（传预设值本身） |
| detailMedia | Array | 否 | 详情素材：`{type: 'image'/'video'（大小写皆可）, url, sortOrder}`；视频最多 3 个 |
| priceDescription | String | 否 | 商品详情图文 HTML，≤10000 字符 |
| spuExtensionFields | Object | 否 | SPU 扩展字段：`{[fieldCode]: value}`。value 类型由配置 fieldType 决定：NUMBER/MONEY→数字、DATE→`"YYYY-MM-DD"`、DATETIME→`"YYYY-MM-DD HH:mm:ss"`、BOOLEAN→布尔、SINGLE_SELECT→选项 code 字符串、MULTI_SELECT→选项 code 数组；空值键剔除（不落库）。**服务端校验行为**：SINGLE_SELECT/MULTI_SELECT 传不在选项内的值报错；BOOLEAN 仅接受 true/false/1/0（其余报错）；NUMBER/MONEY 非数字报错；DATE/DATETIME **不校验格式**（按约定传）；requiredMode=ALWAYS 的字段缺失/为空报错。**系统预置字段**（bizType/serviceDuration/servicePickupMethod/platformSaleForbidden/storeSlotCapacity，editable=false）：创建/编辑时可传——其中 `bizType` 为业务分桶（SERVICE_ONSITE/SERVICE_PICKUP/STUDY_TOUR，驱动库存分派与门店商品筛选），服务/研学商品发品时应传。**未在扩展字段配置中声明的键会原样透传落库**（服务/研学商品的业务配置 serviceSetting/tourMeta/buyNotice 等即承载于此）：除明确知道的业务键外**不要自行构造未声明键**；编辑此类商品时业务键未提交会保留（见 `spu.update` 合并语义），不要主动传 null 清空 |
| sortOrder | Integer | 否 | 排序值，默认 100 |
| isHidden | Boolean | 否 | 是否隐藏，默认 false |
| benefitConfig | Object | 条件 | **VIRTUAL 商品必填**：关联券配置 `{benefitType: "COUPON", couponTemplateId: "<券模板ID字符串>", sourcePromotionId: "<促销活动ID字符串>"}`（benefitType 固定 COUPON；`couponTemplateId` 与 `sourcePromotionId` 成对取自 `ops.product.benefit.coupon-templates` 返回 records 的同名字段，**缺任一即被拒绝**）；服务端实时校验券模板可用性（促销中心不可用时降级放行） |

**VIRTUAL 商品强约束**（服务端强制）：仅 `specMode=SINGLE` 且 `skuList` 恰好 1 个 SKU，`benefitConfig` 必填。

`skuList[]` 结构：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skuName | String | ✅ | 单规格模式可填商品名或「默认规格」 |
| price | Number | ✅ | ≥0.01，精度(8,2)，元 |
| specInfo | String | 条件 | 规格 JSON 字符串（**对象映射**，非数组）：`{"颜色":"红色","尺码":"L"}`；SINGLE 模式可不传或传 `"{}"`；MULTI 模式按约定每个 SKU 必填非空（服务端不做强制校验，空对象会原样落库） |
| specImage | String | 否 | 规格图 URL，≤1024 |
| externalSkuId | String | 否 | 商家 ERP SKU 编码，≤128 |
| status | String | 否 | `ENABLED`（默认）/`DISABLED` |
| weight | Number | 否 | ≥0，精度(7,3)，kg |
| volume | Number | 否 | ≥0，精度(4,6)，m³ |
| minPurchaseQty | Integer | 否 | 1..99，件 |
| purchaseLimit | Integer | 否 | 0..99；0=不限购 |
| skuExtensionFields | Object | 否 | SKU 扩展字段：结构与 spuExtensionFields 相同（targetLevel=SKU/ALL），每个 SKU 独立一份 |

**不开放字段**：`source`、`supplierId` 为导购/供应商来源身份字段——**运营端调用一律不传**（传入会被服务端当真处理：source=SUPPLIER 会强制进入待审+下架状态，属来源申报行为而非普通参数）。

### 出参（原始返回）

`data` 为创建响应：`{spuId, isDraft}`（新建 SPU 业务ID 与草稿标记）。

### 调用示例

```json
{"capability":"ops.product.spu.create","input":{"spuName":"云南研学三日营体验套餐","productType":"STUDY_TOUR","categoryCode":"T900001_C61","images":["https://cos.example.com/main-1.jpg"],"specMode":"SINGLE","price":1299.00,"skuList":[{"skuName":"默认规格","price":1299.00}]},"summary":"创建研学三日营商品"}
```

---

## ✅ 编辑商品（全量覆盖） — ops.product.spu.update

- 🔴 商业影响档位；执行前必须对话确认变更清单
- **执行语义**：单次提交、原样返回（Void）。流程纪律：执行前先读详情与 SKU 行核对现态；提交后回读详情确认变更生效；超时时先查现态再决定如何处理，不盲目重试
- **⚠️ 全量覆盖**：须传**完整 SKU 列表**——未传的已有 SKU 会被**归档**（下架保留数据，供订单/售后反查，非物理删除）；先读详情与 SKU 行，保留用户未要求修改的字段
- **⚠️ 完整现态是唯一合法数据源**：保留字段必须逐字段取自 `spu.detail`+`spu.skus` 的回读现态；**detail/skus 任一读取失败时，禁止用 `spu.search` 等列表出参推断补齐构造本次提交**（images 全列表、attributes、detailMedia、SKU 明细等不在列表出参中，凭部分数据提交 = 未显式提交的字段丢失）——此时如实告知「现态读取失败，无法安全执行全量覆盖编辑」，引导后台操作或稍后重试
- **🔴 确认纪律**：对话确认必须在**首次提交前**独立完成——用户首发指令已含完整字段值**不构成豁免**（确认的增量价值在保留字段与数据来源，不在修改字段本身）；自动审批模式（runApprovalPolicy=auto）只豁免平台审批，**不豁免对话确认**；确认内容至少包含：修改字段、保留字段、保留字段的数据来源（现态回读，或明确说明无推断项）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | SPU 业务ID |
| 其余字段 | — | — | 与创建相同（见 `spu-action.md` 创建商品表），差异：**无 `isHidden`**；`skuList[].skuId` 可选——已有 SKU 传（更新），新增不传（系统生成） |

**⚠️ 扩展字段在编辑时的合并语义（SPU 级与 SKU 级不同）**：
- **spuExtensionFields（SPU 级）是「保留式合并」**而非全量覆盖（与 skuList 等其他字段的全量覆盖语义相反）：仅覆盖本次提交的键（提交 null/空值 = 主动清空该键），**未提交的键沿用旧值**（嵌套业务对象递归合并，漏传的子键同样保留）。编辑时只传需要修改的扩展字段键即可；**主动清空**必须显式传 null。
- **skuList[].skuExtensionFields（SKU 级）是「不传保留、传了全量覆盖」**：该 SKU 项不传 skuExtensionFields 则保留原值；一旦传了（哪怕只传部分键），该 SKU 的扩展字段整体按本次提交重建（未包含的旧键丢失）。编辑既有 SKU 的扩展字段时应从详情回显取全量再修改。

**不开放字段**：`source`、`supplierId`（同创建）；`skipReAudit`（平台角色专属免重审标记，非平台角色传入会被权限拒绝）；⚠️ **`productType` 不可变**——编辑不能改变商品形态。

### 出参（原始返回）

`data` 为 Void（null）。用 `ops.product.spu.detail` / `ops.product.spu.skus` 回读核验变更生效。

### 调用示例

```json
{"capability":"ops.product.spu.update","input":{"spuId":"2058365707555589633","spuName":"云南研学三日营体验套餐","productType":"STUDY_TOUR","categoryCode":"T900001_C61","images":["https://cos.example.com/main-1.jpg"],"specMode":"SINGLE","price":1399.00,"skuList":[{"skuId":"9000012345678901234","skuName":"默认规格","price":1399.00}]},"summary":"调整商品价格并保留既有SKU"}
```

---

## ✅ 草稿保存 — ops.product.draft.save

- **语义**：保存商品表单 JSON 快照（按当前用户隔离）；覆盖保存传 `draftId`

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| productData | String | ✅ | 完整表单 JSON 快照（结构同创建入参：spuName/productType/categoryCode/images/specMode/skuList 等，序列化为字符串）。**服务端不校验该结构**——仅提取 `spuName`（草稿标题兜底）、价格（列表展示）并对图片 URL 预签名，其余原样存储与回显；「结构同创建入参」是调用约定而非服务端校验，正式发布仍须走 spu.create 的完整校验 |
| title | String | 否 | 草稿标题（如商品名），≤256 |
| draftId | String | 否 | ≤64；首次保存为空，覆盖时传入 |

### 出参（原始返回）

`data` 为保存响应：`{draftId}`（首次保存生成；覆盖保存回传原值）。

### 调用示例

```json
{"capability":"ops.product.draft.save","input":{"title":"云南研学三日营体验套餐","productData":"{\"spuName\":\"云南研学三日营体验套餐\",\"productType\":\"STUDY_TOUR\",\"specMode\":\"SINGLE\"}"},"summary":"保存商品草稿待继续编辑"}
```

---

## ✅ 删除草稿 — ops.product.draft.delete

- 🔴 不可逆；执行前向用户复述草稿标题确认
- **语义**：删除指定草稿。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| draftId | String | ✅ | 草稿 ID（路径参数，来自 draft.search） |

### 调用示例

```json
{"capability":"ops.product.draft.delete","input":{"draftId":"draft-8f3c2a1b"},"summary":"删除草稿云南研学套餐（未完成）"}
```

---

## ✅ Excel 批量导入商品 — ops.product.spu.import

- **传输形态**：multipart 文件上传（Excel）
- **语义**：批量导入/更新商品，**同步执行**（处理完才返回）。限制：≤5000 行、文件 ≤10MB。模板从管理后台「商品列表-导入」入口获取。

### 入参

- 文件部分：`file`（Excel，≤10MB，≤5000 行）。

### 出参

- `totalCount`（总行数）、`successCount`、`failureCount`、`hasFailureDetail`（是否有失败明细）、`failureTaskId`（有失败时的明细任务 ID）。
- ⚠️ 失败明细下载为文件流端点，当前未开放——有失败时向用户报告失败数量并建议在管理后台下载明细核对。

### 调用示例

```json
{"capability":"ops.product.spu.import","input":{"file":"uploads/批量导入模板.xlsx", "fileType":"excel"},"summary":"批量导入商品 Excel（5000 行以内）"}
```

---

## ✅ 媒体上传 — ops.product.spu.upload-media

- **传输形态**：multipart 文件上传
- **语义**：上传商品图片/视频，返回 COS URL——创建/编辑商品 `images` 等字段的图片来源。图片 jpg/jpeg/png/gif/bmp ≤5MB；视频 mp4/flv ≤200MB。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | 文件 | ✅ | 图片（jpg/jpeg/png/gif/bmp ≤5MB）或视频（mp4/flv ≤200MB） |
| type | String | — | 存储目录名，默认 `main`（主图）；一般沿用默认 |

### 出参

- `url`（媒体访问地址，→ 商品创建/编辑的 images）、`key`（COS 文件 Key）。

### 调用示例

```json
{"capability":"ops.product.spu.upload-media","input":{"file":"uploads/图片素材.png", "fileType":"image","type":"main"},"summary":"上传商品主图获取 URL"}
```

---

## ✅ SPU 审核通过 — ops.product.spu.audit-approve

- 🔴 商业影响档位；审核决定商品能否进入上架流程；单条/批量共用（`spuId` 或 `spuIds` 二选一）
- **语义**：通过后商品进入可上架状态（与上下架开关独立——审核通过 ≠ 已上架）
- **前置条件**（服务端强制）：商品 `auditStatus=REVIEWING`（待审）**且来源为导购发品/供应商**（`GUIDE_PUBLISH`/`SUPPLIER`）——ADMIN 自建商品不走此审核，对非待审或不可审来源调用会失败
- **批量语义**：事务整批执行——**任一条不满足前置则全批回滚**（无部分成功；返回 Void 无逐条结果，以 `spu.search` 回读核验）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅* | SPU 业务ID（单条） |
| spuIds | String[] | ✅* | SPU 业务ID列表（批量，与 spuId 二选一） |
| auditRemark | String | — | 审核备注 |
| idempotencyKey | String | — | ⚠️ 幂等键当前**服务端未实现**（仅记录日志，重复提交不拦截）——靠流程纪律防重：超时先查审核状态再决定 |

### 出参（原始返回）

`data` 为 `null`（Void）；以 `spu.search`/`spu.detail` 的审核状态字段核验。

### 调用示例

```json
{"capability":"ops.product.spu.audit-approve","input":{"spuId":"2058365707555589633","auditRemark":"资料齐全，审核通过"},"summary":"审核通过该研学商品"}
```

```json
{"capability":"ops.product.spu.audit-approve","input":{"spuIds":["2058365707555589633","2058365707555589634"]},"summary":"批量审核通过两个商品"}
```

---

## ✅ SPU 审核驳回 — ops.product.spu.audit-reject

- 🔴 商业影响档位；**`auditRemark` 必填**（服务端强校验非空）；驳回原因会传达给商品编辑方，文案要具体可行动
- **前置条件**（服务端强制）：同 audit-approve——`auditStatus=REVIEWING` 且来源 `GUIDE_PUBLISH`/`SUPPLIER`（仅单条，无批量）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| spuId | String | ✅ | SPU 业务ID |
| auditRemark | String | ✅ | 驳回原因（必填） |
| idempotencyKey | String | — | ⚠️ 幂等键当前服务端未实现（仅记录日志）——靠流程纪律防重 |

### 出参（原始返回）

`data` 为 `null`（Void）。

### 调用示例

```json
{"capability":"ops.product.spu.audit-reject","input":{"spuId":"2058365707555589633","auditRemark":"主图模糊，请更换后重新提审"},"summary":"驳回该商品并说明原因"}
```
