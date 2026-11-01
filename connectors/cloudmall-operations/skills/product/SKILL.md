---
name: product
display_name: 云MALL商品
display_name_en: CloudMall Products
description: 本域定位：商品基础数据层（SPU/SKU/价格/库存），非交易/促销/门店。商品域运营：商品发布/编辑/草稿/导入、审核、上下架/隐藏/推荐/批量改价、SKU规格、仓库库存（调整/流水/导入导出）、门店商品（门店价/预留库存/档位）、评价（回复/审核/关键词/统计）、研学营期名额、静态标签、搭配（海报/投放物料）、类目/品牌/描述属性/扩展字段、商详装修与FAQ、到店服务与预约模板、送礼配置、商品设置、搜索模拟。防混淆：优惠券/满减/秒杀→促销域；分销/导购→营销域；订单/售后/物流→交易域；**租户级推荐配置/四力推荐开关/推荐切换与数据上报→商户域**——本域的"推荐"仅指商品级推荐标记（单商品推荐位）。
description_zh: 按任务类型路由最小加载路径，通过已登记 capability 执行查询与写操作；未开放操作只整理需求，不承诺执行。
description_en: Task-typed minimal loading paths for product domain operations; execute registered capabilities for queries and writes, and only organize requirements for unpublished operations.
allowed-tools: cloudmall_query,cloudmall_action
version: 0.9.1
author: 云MALL
---

# 云MALL商品域运营技能包

> 本技能按**任务类型路由最小加载路径**；下方能力路由表是本域唯一的 capability → 契约文件索引。写操作的前置条件/状态约束在对应契约锚点内，本表不重复。

## 业务目的定位（本域是什么）

> 本域的业务本质是**管理"卖什么"——商品信息/价格/库存/上下架/类目/品牌是商品的基础数据层**。
> 不是交易执行（交易域）、不是促销定价（促销域）、不是门店归属（商户域）。
> 简单判断：说"商品/SPU/SKU/价格/库存/上下架/类目/品牌"→本域。

## 任务类型路由

| 任务类型 | 最小加载路径 |
|---------|-------------|
| **简单查询**（查商品/SKU/库存/评价/门店商品/类目品牌/标签/搭配/配置现值） | 能力路由表 → 定位契约文件 → 读目标 `## ✅ capability` 锚点 → 直接调用查询执行器（跳过 L1/L2） |
| **写操作**（发布/编辑/审核/上下架/改价/库存调整/回复等） | 通用约定 + 风险档位（本文件）→ `references/flows/` 对应业务族文件（发品与审核=`product-publishing.md`；上下架状态=`product-status.md`；库存=`product-inventory.md`；门店商品=`product-store.md`；评价=`product-review.md`；营期名额=`product-tour.md`；静态标签=`product-tag.md`；搭配=`product-collocation.md`；类目品牌与基础数据=`product-dictionary.md`；商详装修与FAQ=`product-detail.md`；到店服务与预约模板=`product-service.md`；送礼与商品设置=`product-gift-setting.md`；写操作共同闭环=`product-core.md`）→ 契约文件锚点 → 按风险档位确认后调用 |
| **概念咨询/异常排查**（状态含义/操作前置/枚举值） | `references/domains/product-enums.md`（状态机与枚举字典）→ 契约文件锚点 |
| **概念咨询/异常排查**（实体关系/规则语义） | `references/domains/product-concepts.md` → 契约文件锚点 |

## 能力路由表（唯一索引）

> 所有 capability 完整 id = `ops.` + 下表短名（如 `ops.` + `product.spu.search`）；契约文件均在 `references/apis/product/` 下。🔴 = 风险档位高危（见下方操作风险档位）。

### 查询能力（Capability 查询执行器）

| 契约文件 | capabilities |
|---|---|
| `spu-query.md` | product.spu.search 商品分页搜索 · product.spu.tab-count 状态Tab计数 · product.spu.detail 基础详情 · product.spu.skus SKU行 · product.spu.change-logs 变更记录 · product.sku.search SKU检索 · product.spu.audit-status-count 审核状态计数 · product.draft.search 草稿列表 · product.draft.detail 草稿详情 · product.benefit.coupon-templates 可用券模板 |
| `store-product-query.md` | product.store-product.search 门店商品分页 · product.store-product.status-count 状态计数 · product.store-product.skus 门店SKU列表 · product.store-product.inventory-detail 库存明细 · product.store-product.log-search 变更日志 · product.store-product.export 导出（URL型） |
| `review-query.md` | product.review.search 评价分页 · product.review.tab-count 状态Tab计数 · product.review.detail 评价详情 · product.review.reply-templates 回复模板列表 · product.review.stats-overview 统计总览 · product.review.stats-trend 统计趋势 · product.review.stats-star-distribution 星级分布 · product.review.stats-word-cloud 评价词云 · product.review.stats-product-ranking 评价排行 · product.review.keyword-candidates 关键词候选池 · product.review.keywords-enabled 已启用关键词 · product.review.setting-get 设置查询 · product.review.export 评价导出（URL型） |
| `category-brand-query.md` | product.category.tree 类目树 · product.category.options 类目平铺选项 · product.category.search 类目搜索 · product.brand.options 品牌选项 · product.brand.page 品牌分页 · product.brand.detail 品牌详情 · product.brand.spus 品牌关联商品 · product.description-attribute.by-category 按类目查描述属性 |
| `store-service-query.md` | product.store-service.search 服务分页 · product.store-service.detail 服务详情 · product.appointment-template.search 模板分页 · product.appointment-template.options 模板选项 · product.appointment-template.detail 模板详情 |
| `collocation-query.md` | product.collocation.search 搭配分页 · product.collocation.dashboard 搭配看板 · product.collocation.detail 搭配详情 · product.collocation.poster-config-get 海报文案查询 · product.collocation.launch-material 投放物料查询 |
| `inventory-query.md` | product.inventory.search 仓库库存分页 · product.inventory.log-search 库存流水 · product.inventory.warehouses SKU关联仓库 · product.inventory.export 库存导出（URL型） · product.inventory.import-task 导入任务进度 · product.inventory.import-failure-url 失败明细地址 |
| `extension-field-query.md` | product.extension-field.search 扩展字段分页 |
| `static-tag-query.md` | product.static-tag.search 标签分页 · product.static-tag.skus 标签关联SKU |
| `description-attribute-query.md` | product.description-attribute.page 描述属性分页 |
| `detail-layout-query.md` | product.detail-layout.config-get 装修配置查询 · product.detail-layout.logs 装修操作日志 |
| `faq-query.md` | product.faq.page FAQ分页 |
| `gift-setting-query.md` | product.gift-setting.get 送礼配置查询 · product.gift-setting.validate-skus 白名单校验 |
| `setting-query.md` | product.setting.general-get 通用配置查询 |
| `search-simulation.md` | product.spu.search-simulate 搜索模拟（只读） · product.spu.suggest-word 联想词查询 |
| `product-group.md` | product.group.options 分组选项 |
| `tour-session-query.md` | product.tour-session-quota.list 按门店查营期名额 · product.tour-session-quota.aggregate 跨门店名额聚合 |

### 写能力（Capability 写操作执行器）

| 契约文件 | capabilities |
|---|---|
| `spu-action.md` | product.spu.create 创建商品 · product.spu.update 编辑商品（全量覆盖）🔴 · product.draft.save 草稿保存 · product.draft.delete 删除草稿 🔴 · product.spu.import Excel导入 · product.spu.upload-media 媒体上传 · product.spu.audit-approve 审核通过 🔴 · product.spu.audit-reject 审核驳回 🔴 |
| `spu-status-action.md` | product.spu.on-shelf 上架 · product.spu.off-shelf 下架 · product.spu.hide 隐藏 · product.spu.unhide 取消隐藏 · product.spu.recommend 推荐开关 · product.spu.batch-on-shelf 批量上架 🔴 · product.spu.batch-off-shelf 批量下架 🔴 · product.spu.batch-hide 批量隐藏 🔴 · product.spu.batch-unhide 批量取消隐藏 🔴 · product.spu.batch-update 批量改价 🔴 · product.spu.delete 删除商品 ⛔已摘除（后端废弃，改用 hide/unhide） · product.spu.batch-delete 批量删除 🔴 · product.spu.assign-stores 分配门店 · product.spu.batch-assign-store 批量分配门店 · product.spu.store-stock 分门店库存 |
| `store-product-action.md` | product.store-product.on-shelf 门店上架 · product.store-product.off-shelf 门店下架 · product.store-product.batch-on-shelf 批量上架 🔴 · product.store-product.batch-off-shelf 批量下架 🔴 · product.store-product.sku-toggle-shelf SKU档位翻转 · product.store-product.batch-sku-toggle-shelf SKU档位批量 🔴 · product.store-product.sku-store-price 门店价 🔴 · product.store-product.batch-sku-store-price 门店价批量 🔴 · product.store-product.reserved-qty 预留库存 🔴 · product.store-product.batch-reserved-qty 预留批量 🔴 · product.store-product.audit 门店商品审核 🔴 · product.store-product.batch-assign-store 批量分配门店 |
| `review-action.md` | product.review.reply 回复评价 · product.review.audit 评价审核 🔴 · product.review.batch-audit 批量审核 🔴 · product.review.append-audit 追评审核 🔴 · product.review.keyword-batch-enable 批量启用关键词 · product.review.keyword-enable 启用关键词 · product.review.keyword-disable 停用关键词 · product.review.keyword-reject 驳回关键词 · product.review.reply-template-create 新增模板 · product.review.reply-template-update 编辑模板 · product.review.reply-template-delete 删除模板 🔴 · product.review.reply-template-set-default 设默认模板 · product.review.setting-save 评价设置保存 🔴 |
| `category-brand-action.md` | product.category.batch-save 类目批量维护 🔴 · product.brand.create 品牌创建 · product.brand.update 品牌编辑 · product.brand.delete 品牌删除 🔴 · product.brand.upload-logo Logo上传 · product.brand.bind-spus 绑定商品 · product.brand.unbind-spus 解绑商品 |
| `store-service-action.md` | product.store-service.create 创建服务 · product.store-service.update 编辑服务 · product.store-service.on-shelf 服务上架 · product.store-service.off-shelf 服务下架 · product.store-service.delete 删除服务 🔴 · product.appointment-template.create 创建模板 · product.appointment-template.update 编辑模板 · product.appointment-template.delete 删除模板 🔴 |
| `collocation-action.md` | product.collocation.create 创建搭配 · product.collocation.update 编辑搭配 🔴 · product.collocation.online 搭配上线 · product.collocation.offline 搭配下线 · product.collocation.delete 删除搭配 🔴 · product.collocation.upload-image 图片上传 · product.collocation.poster-image 海报主图上传 · product.collocation.poster-config-save 海报文案保存 · product.collocation.launch-material-retry 物料重试 |
| `inventory-action.md` | product.inventory.adjust 库存调整 🔴 · product.inventory.init 库存初始化 · product.inventory.import 批量导入（异步） |
| `extension-field-action.md` | product.extension-field.create 新增字段 · product.extension-field.update 编辑字段 · product.extension-field.set-enabled 启停字段 · product.extension-field.sort 字段排序 · product.extension-field.delete 删除字段 🔴 |
| `static-tag-action.md` | product.static-tag.create 新增标签 · product.static-tag.update 编辑标签 · product.static-tag.priority 优先级调整 · product.static-tag.bind-skus 绑定SKU（全量）🔴 · product.static-tag.delete 删除标签 🔴 · product.static-tag.batch-delete 批量删除 🔴 |
| `description-attribute-action.md` | product.description-attribute.create 新增属性 · product.description-attribute.update 编辑属性 · product.description-attribute.delete 删除属性 🔴 |
| `detail-layout-action.md` | product.detail-layout.lock-acquire 获取编辑锁 · product.detail-layout.lock-release 释放编辑锁 · product.detail-layout.config-save 配置保存 |
| `faq-action.md` | product.faq.create 新增FAQ · product.faq.update 编辑FAQ · product.faq.toggle 启停切换 · product.faq.reorder FAQ排序 · product.faq.delete 删除FAQ 🔴 |
| `gift-setting-action.md` | product.gift-setting.save 送礼配置保存 🔴 |
| `setting-action.md` | product.setting.general-save 通用配置保存 |
| `tour-session-action.md` | product.tour-session-quota.batch-update 批量更新名额 🔴 |

## 未开放（不调用，只整理需求）

| 模块 | 原因 |
|---|---|
| 门店选项列表 | 后台临时实现返回空列表（门店模块未落地），开放无意义 |
| 文件流型下载（商品导出/导入模板/失败明细文件） | 产品决策仅开放 URL 型导出，文件流走管理后台 |
| abs 摘要独立查询（simulate/abs-details） | 依赖 X-Store-Warehouse 定店定仓 Header，Capability 调用链不注入，调用恒返回空 |
| ES 重建 / 索引同步 / 统计手动刷新 / 内部回调 / 销量初始化 | 调试与运维面，不属运营开放能力 |
| 供应商端（supplier/**） | 供应商视角，非平台运营面 |

## 通用约定（商品域共享）

| 项 | 约定 |
|----|------|
| **调用方式** | 只能调用契约文件中标注了 capability 的能力：查询用 `当前运行时的 Capability 查询执行器`，写操作用 `当前运行时的 Capability 写操作执行器`。输入 `{capability, input, summary}`；`summary` 用一句话说明意图。**不得猜测或编造未登记的 capability** |
| **入参字段名** | 以契约参数表为准，**大小写敏感**；未读到目标能力的参数表之前，不要凭直觉或惯例拼写参数名（拼错只能得到缺参报错再返工） |
| **身份与授权** | 身份由连接授权绑定；查询需 `mall.query`、写操作需 `mall.action` 授权，且受当前账号实时业务权限限制（营期名额等还需平台角色，权限不足会得到 PERMISSION_DENIED）。不询问、不传入租户/账号/Token/服务名/路径/权限码；门店筛选 storeId 属于业务参数，必须来自用户提供的已知门店ID或查询结果中的门店字段 |
| **ID 序列化** | 雪花 ID（19 位）一律**十进制字符串**，严禁传 Number（JS 精度上限 2^53-1）。响应中 ID 字段可能为 String（后端全局 Long→String） |
| **分页** | `pageSize ≤ 100`（建议 20 起步）；响应超出大小预算返回 `UPSTREAM_ERROR`，缩小 pageSize 或查询范围后重试 |
| **响应信封** | 成功 `{capability, data, traceId}`，`data` 为上游**原始业务数据**（不裁剪字段）；错误 `{errorCode, message, retryable, traceId}` |
| **错误恢复** | `AUTH_REQUIRED`：请用户在 当前 Agent 重新连接；`SCOPE_INSUFFICIENT`：提示重新确认授权范围；`PERMISSION_DENIED`：停止该操作，不找替代方式绕过；`INPUT_INVALID`：对照参数表修正（业务校验由服务端执行）；`UPSTREAM_ERROR/UPSTREAM_TIMEOUT`：查询可稍后重试或缩小条件；**写操作禁止立即同参重试**——先回读核对是否已生效，确认未生效且参数无误后至多重试一次，仍失败如实报告由用户决策（写 500 可能已生效，盲目重试有副作用）。失败不等于无数据 |
| **写操作语义** | `当前运行时的 Capability 写操作执行器` 为纯执行器：单次提交（永不自动重试）并原样返回上游业务结果。**先读现态、确认后执行、执行后回读** 的流程纪律由本 Skill 的 flows 定义，模型必须遵守。超时/网络错误时结果不确定——先查询对象状态再决定如何向用户说明，不盲目重复提交 |
| **写操作确认** | 只在用户明确要求执行对应操作时调用写能力；创建/编辑等表单操作须先与用户确认关键字段（名称、价格、类目、SKU）。若当前执行器不具备所需确认交互，则停止写入并说明缺失条件 |
| **金额** | decimal 传**数字**（如 `99.50`），单位元；禁止传分 |
| **日期时间格式** | 各能力时间字段格式**不统一**，严格按参数表说明列传值。常见：`yyyy-MM-dd HH:mm:ss`（如 `2026-08-11 10:00:00`）、`yyyy-MM-dd`（纯日期）、ISO-8601（如 `2026-08-11T10:00:00+08:00`）。说明列未标注时默认 `yyyy-MM-dd HH:mm:ss` |
| **比例/时长** | 比例传小数（税率 `0.13` = 13%）；时长传纯数字（单位看说明列括号标注），禁止附带单位字符串 |
| **布尔值** | 传 `true`/`false`；禁止 `1`/`0` 或 `"Y"`/`"N"`（除非参数表明确允许） |
| **枚举大小写** | 严格按 `product-enums.md` 枚举字典与 Layer 3 参数表取值（如 `STUDY_TOUR` 大写、`express` 小写），禁止猜测 |

### 操作风险档位（写操作前必读）

| 档位 | 操作 | 说明 |
|------|------|------|
| 🔴 不可逆（执行前确认完整对象清单） | 批量删除 SPU、删除搭配、删除回复模板、静态标签清空关联（空 skuIds） | 逻辑删除不可恢复 |
| 🔴 商业影响（执行前用户确认数值/清单） | 批量上下架/隐藏/改价（≤200 条）、库存调整（SUBTRACT/初始化）、门店价修改（单/批）、预留库存、营期名额、评价审核（通过/驳回）、SPU/门店/搭配审核 | 影响面大或公开可见 |
| 🟡 可逆写（做 + 向用户说明） | 单条上架/下架/隐藏/取消隐藏/推荐、单条编辑、评价回复、关键词启用、回复模板维护 | 可撤销 |

**字段确认红线（禁止 AI 编造）**：价格（改价/门店价）、库存数量（调整/预留/名额）、审核结论与驳回原因、搭配主图 URL——必须由用户明确给出；驳回原因按枚举取值（如评价 SPAM/INAPPROPRIATE/IRRELEVANT/OTHER）。

**追问发起规范**：需要用户补充信息/做出选择时（含价格、库存数量等自由输入值），**一律通过当前运行时的结构化追问能力发起**（追问卡）——卡片是用户可见的待办入口，也是判定「Agent 已挂起等待输入」的唯一信号；禁止只在正文用文字列出待补项后收尾（用户无感，任务会停在半途）。追问发起后可用 `已发起确认，等待你的选择` 简短收尾；**未发起追问卡时禁止使用该措辞**（没有卡片却声称已发起确认，会让用户找不到操作入口）。多个商品的同类值（如四个商品的售价）合并为一个问题让用户在输入框按顺序填写；价格、库存不得编成选项数值，选项给填写方式（如「我在输入框逐个填写售价」）。

**追问选项标签规范**：结构化追问的选项标签必须具体明确（描述动作与对象，如「确认下架该商品」）；禁止使用「取消」「确认」「是/否」等泛化标签——平台会拒绝泛化选项。取消/否定场景写成具体动作：「保留当前方案」「暂不发布」「暂不删除」而非「取消」。

### 调用前完整性检查（强制）

1. 展开读取入参表的全部叶子字段；出现嵌套结构（如 products/updates/items/skuList）继续读取其字段说明。
2. 区分必填、条件必填（如 REJECT 时 rejectReason）与可选；满足当前枚举分支相关的条件。
3. 枚举使用 `product-enums.md` 字典精确值并保持大小写。
4. 确认金额、比例、时间的单位与 JSON 类型；ID 一律十进制字符串。
5. 确认对象当前状态；审核/上下架类动作按状态流顺序调用（如评价驳回仅对待审核生效）。
6. 同一能力存在"单条/批量"分支时严格二选一，字段名以参数表为准（如 batch-off-shelf 用 `spuIds`）。
7. **入参字段名与出参字段名对称（round-trip 规则）**：查询出参里叫什么字段名，对应操作的入参就用什么字段名——SPU 出参是 `spuId`，故 SPU 单条操作（detail/skus/update/上下架/隐藏/推荐/分配门店/门店库存）入参统一 `spuId`；批量操作用 `spuIds`/`ids`（以各契约参数表为准）。传错字段名会报「缺少路径参数 xxx」，此时必须对照契约入参表改字段名重试，禁止原样重试或盲目换能力。

## 环境与执行边界

- 缺失字段不等于零、不等于不存在；看不到门店/仓库数据不能用租户聚合库存替代。
- 图片/视频素材：用户可直接提供文件（经 `ops.product.spu.upload-media` 上传取 URL），或提供已在云MALL可访问的图片 URL；用户给不出的素材应说明缺少的材料，不把陌生 URL 当可信内部素材。
- 更新为**全量覆盖**语义：更新前先读详情，保留用户未要求修改的字段与未涉及的 SKU。
- 写操作超时或网络错误时结果不确定：先查询对象状态再向用户说明，不自动重复提交。
