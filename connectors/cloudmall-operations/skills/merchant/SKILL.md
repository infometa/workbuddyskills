---
name: merchant
display_name: 云MALL商户
display_name_en: CloudMall Merchant
description: 本域定位：运营基础设施（门店/仓库/装修/物流），非商品/交易/营销。商户域运营：门店（建店/状态/绑定/隔离/网店）、仓库配送（方式/运费履约模板/区块）、自提点、组织节点、供应商（入驻审核/复核/OCR/字段）、素材库（查找/上传/分组）、店铺信息、装修页面、分类导航（模板/分类/商品关联/统计）、风格导航、热搜词与搜索干预、暗纹词、进店规则、渠道配置与追踪、电话客服配置（客服电话/服务时间）、推荐配置（租户级四力推荐开关与凭据）、导入导出、操作日志。防混淆：优惠券/满减/秒杀→促销域；分销/导购→营销域；价格库存→商品域；订单售后物流→交易域；微信小程序客服开关→用户域；商品推荐标记（单个商品的上架推荐位）→商品域——本域的"推荐配置"仅指租户级四力推荐开关（数据上报+推荐切换），不是商品级推荐标记；**推广追踪单/渠道追踪（追踪单停用、渠道配置）→本域**，营销域只有 CPS 推广商品与导购推广任务。
description_zh: 按任务类型路由最小加载路径，通过已登记 capability 执行查询与写操作；未开放操作只整理需求，不承诺执行。
description_en: Task-typed minimal loading paths for merchant domain operations (stores, fulfillment, suppliers, content, and operation-log audit); execute registered capabilities for queries and writes, and only organize requirements for unpublished operations.
allowed-tools: cloudmall_query,cloudmall_action
version: 0.12.1
author: 云MALL
---

# 云MALL商户域运营技能包

> 本技能按**任务类型路由最小加载路径**；下方能力路由表是本域唯一的 capability → 契约文件索引。本技能包含两个子域：**商户主域（门店/仓库/配送/组织/供应商/素材/导航/搜索运营等）**、**操作日志审计（system，只读）**。写操作的前置条件/状态约束在对应契约锚点内，本表不重复。

## 业务目的定位（本域是什么）

> 本域的业务本质是**管理运营基础设施——门店/仓库/物流/装修/素材/搜索干预是"在哪里卖、怎么送到"的底层配置**。
> 不是商品管理（商品域）、不是交易执行（交易域）、不是营销拉新（营销域）。
> 简单判断：说"门店/仓库/配送/装修/素材库/搜索干预/进店规则"→本域。

## 任务类型路由

| 任务类型 | 最小加载路径 |
|---------|-------------|
| **简单查询**（查门店/仓库/自提点/配送/组织/供应商/素材/导航/配置现值） | 能力路由表 → 定位契约文件 → 读目标 `## ✅ capability` 锚点 → 直接调用查询执行器（跳过 L1/L2） |
| **写操作**（建店/审核/发布/绑定/导入/干预规则维护等） | 通用约定 + 风险档位（本文件）→ `references/flows/` 对应业务族文件（门店与隔离=`merchant-store.md`；仓库配送与模板=`merchant-warehouse.md`；供应商=`merchant-supplier.md`；分类导航=`merchant-category-nav.md`；搜索运营=`merchant-search.md`；进店规则与固定区域=`merchant-entry.md`；渠道配置与追踪=`merchant-channel.md`；推荐/客服/店铺信息=`merchant-config.md`；视觉风格与导航=`merchant-visual.md`；素材=`merchant-material.md`；导入导出=`merchant-import-export.md`；写操作共同闭环与字段来源=`merchant-core.md`）→ 契约文件锚点 → 按风险档位确认后调用 |
| **概念咨询/异常排查**（状态含义/操作前置/枚举值） | `references/domains/merchant-enums.md`（状态机与枚举字典；操作日志子域知识见 `references/domains/system.md`）→ 契约文件锚点 |
| **概念咨询/异常排查**（实体关系/规则语义/实现缺口） | `references/domains/merchant-concepts.md` → 契约文件锚点 |

## 能力路由表（唯一索引）

> 所有 capability 完整 id = `ops.` + 下表短名（如 `ops.` + `merchant.store.search`）；操作日志子域为 `ops.system.` 前缀。契约文件均在 `references/apis/merchant/` 下（操作日志在 `references/apis/system/`）。🔴 = 风险档位高危（见下方操作风险档位）。

### 查询能力（Capability 查询执行器）

| 契约文件 | capabilities |
|---|---|
| `store-query.md` | merchant.store.search 门店分页搜索 · merchant.store.detail 门店详情 · merchant.store.options 营业中门店选项 · merchant.store.picker 门店选择器 · merchant.store.warehouses 门店已绑仓库 · merchant.store.pickup-sites 门店已绑自提点 · merchant.store.available-warehouses 门店可绑仓库 · merchant.store.available-pickup-sites 门店可绑自提点 · merchant.store.fulfillment-tree 全局履约树 · merchant.store.fulfillment-blocks 履约区块聚合 · merchant.store.export 导出门店列表 |
| `store-isolation-query.md` | merchant.store-isolation.search 门店隔离分页 · merchant.store-isolation.store-ids 已隔离门店ID全集 · merchant.store-mode.get 网店模式查询 |
| `warehouse-query.md` | merchant.warehouse.search 仓库分页搜索 · merchant.warehouse.stats 仓库配置统计 · merchant.warehouse.detail 仓库详情 · merchant.warehouse.delivery-methods 仓库已绑配送方式 · merchant.warehouse.delivery-blocks 仓库区块配置查询 |
| `pickup-site-query.md` | merchant.pickup-site.search 自提点分页搜索 · merchant.pickup-site.detail 自提点详情 |
| `delivery-query.md` | merchant.delivery-method.list 配送方式列表（全部） · merchant.delivery-method.list-enabled 配送方式列表（仅启用） · merchant.freight-template.search 运费模板分页 · merchant.freight-template.detail 运费模板详情 · merchant.fulfillment-template.search 履约模板分页 · merchant.fulfillment-template.detail 履约模板详情 |
| `area-config-query.md` | merchant.delivery-area-block.search 配送区块分页 · merchant.delivery-area-block.detail 配送区块详情 · merchant.delivery-area-block.all-regions 全部区块区域 · merchant.fixed-area.search 固定区域分页 · merchant.region.tree 行政区划树 |
| `org-query.md` | merchant.org.tree 组织树 · merchant.org.search 组织节点搜索 |
| `channel-config-query.md` | merchant.channel-config.search 渠道配置分页 · merchant.channel-config.select 渠道级联下拉 |
| `recommend-config-query.md` | merchant.recommend-config.get 推荐配置查询 |
| `call-service-config-query.md` | merchant.call-service-config.get 客服配置查询 |
| `entry-rule-query.md` | merchant.entry-rule.list 进店规则列表 |
| `search-intervention-query.md` | merchant.hot-keyword.search 热搜词分页 · merchant.search-intervention.nlu.search NLU干预规则分页 · merchant.search-intervention.rerank.search Rerank干预规则分页 · merchant.search-intervention.operation-logs 干预规则操作日志 |
| `decoration-page.md` | merchant.decoration-page.search 装修页面分页 · merchant.decoration-page.detail 装修页面详情 · merchant.decoration-page.versions 版本列表 · merchant.decoration-page.version-detail 版本详情 · merchant.decoration-page.bindings 门店绑定列表 · merchant.decoration-page.binding-check 发布前置校验 · merchant.decoration-page.invalid-bindings 无效绑定检测 |
| `material-query.md` | merchant.material.search 素材分页 · merchant.material.group-tree 素材分组树 · merchant.material.batch-get-urls 批量获取签名URL · merchant.material.group-preset-mapping 预置分组映射 |
| `shop-info-query.md` | merchant.shop-info.get 店铺信息查询 |
| `supplier-query.md` | merchant.supplier.search 供应商分页 · merchant.supplier.detail 供应商详情 · merchant.supplier.draft.get 草稿状态查询 · merchant.supplier.field-config.get 字段配置查询 · merchant.supplier.export 导出供应商列表 |
| `category-nav-query.md` | merchant.category-nav.list 模板分页 · merchant.category-nav.detail 模板详情 · merchant.category-nav.store-visibility.get 门店可见性查询 · merchant.category-nav.invalid-store-bindings.check 无效绑定检测 · merchant.category-nav.export 导出模板 |
| `category-nav-content-query.md` | merchant.category-nav.front-category.tree 前台分类树查询 · merchant.category-nav.category-products.list 分类商品查询 |
| `category-nav-stats.md` | merchant.category-nav.stats.overview 概览统计 · merchant.category-nav.stats.core 核心指标 · merchant.category-nav.stats.trend 趋势统计 · merchant.category-nav.stats.category 分类维度统计 |
| `theme-tabbar-query.md` | merchant.theme.detail 风格配置查询 · merchant.tabbar-scheme.list 导航方案列表 · merchant.tabbar-scheme.detail 导航方案详情 |
| `map.md` | merchant.map.suggestion 地图POI搜索 |
| `placeholder-query.md` | merchant.placeholder-keyword.page 暗纹词分页 · merchant.placeholder-scene.page 场景分页 · merchant.placeholder-scene.enabled-list 启用场景列表 · merchant.placeholder-scene.detail 场景详情 |
| `channel-trace-query.md` | merchant.channel-trace.list 追踪单分页 · merchant.channel-trace.detail 追踪单详情 · merchant.channel-trace.custom-channels 自定义渠道字典 · merchant.channel-trace.export 渠道追踪导出 · merchant.channel-trace-detail.list 追踪明细查询 · merchant.channel-trace-detail.member-behaviors 会员行为查询 |
| `operation-log.md`（system） | system.operation-log.filter-options 筛选选项 · system.operation-log.search 全站操作日志检索 |

### 写能力（Capability 写操作执行器）

| 契约文件 | capabilities |
|---|---|
| `store-action.md` | merchant.store.create 创建门店 · merchant.store.update 编辑门店 · merchant.store.update-status 门店状态变更 · merchant.store.batch-status 批量状态变更 🔴 · merchant.store.batch-delete 批量删除门店 🔴 · merchant.store.set-default 设默认门店 🔴 · merchant.store.bind-warehouse 绑定仓库 · merchant.store.unbind-warehouse 解绑仓库 · merchant.store.sort-warehouses 仓库排序 · merchant.store.bind-pickup-site 绑定自提点 · merchant.store.unbind-pickup-site 解绑自提点 · merchant.store.import 导入门店 🔴 |
| `store-isolation-action.md` | merchant.store-isolation.batch-add 批量新增隔离 🔴 · merchant.store-isolation.update-status 隔离启停 · merchant.store-isolation.delete 删除隔离记录 🔴 · merchant.store-mode.update 网店模式设置 🔴 |
| `warehouse-action.md` | merchant.warehouse.create 新建仓库 · merchant.warehouse.update 编辑仓库 · merchant.warehouse.update-status 启停仓库 · merchant.warehouse.bind-delivery-methods 绑定配送方式 🔴 · merchant.warehouse.bind-delivery-blocks 绑定配送区块 · merchant.warehouse.bind-administrative-blocks 绑定行政区域 🔴 · merchant.warehouse.bind-block-template 绑定区块模板 · merchant.warehouse.complete-fulfillment-config 完成配置 · merchant.warehouse.unbind-delivery-block 解绑配送区块 |
| `pickup-site-action.md` | merchant.pickup-site.create 新增自提点 · merchant.pickup-site.update 编辑自提点 · merchant.pickup-site.update-status 自提点启停 · merchant.pickup-site.delete 删除自提点 🔴 |
| `delivery-action.md` | merchant.delivery-method.create 新增配送方式 · merchant.delivery-method.update 编辑配送方式 · merchant.delivery-method.update-status 启停配送方式 🔴 · merchant.delivery-method.sort 配送方式排序 · merchant.freight-template.create 新建运费模板 🔴 · merchant.freight-template.update 编辑运费模板 · merchant.freight-template.update-status 启停运费模板 · merchant.freight-template.delete 删除运费模板 🔴 · merchant.fulfillment-template.create 新建履约模板 · merchant.fulfillment-template.update 编辑履约模板 · merchant.fulfillment-template.update-status 启停履约模板 · merchant.fulfillment-template.delete 删除履约模板 🔴 |
| `area-config-action.md` | merchant.delivery-area-block.update-status 启停配送区块 🔴 · merchant.delivery-area-block.region-exclude 切换区域排除 · merchant.fixed-area.create 新增固定区域 · merchant.fixed-area.update 编辑固定区域 · merchant.fixed-area.delete 删除固定区域 🔴 · merchant.fixed-area.delete-area 删除单地区 |
| `org-action.md` | merchant.org.create 新建组织节点 · merchant.org.update 编辑组织节点 · merchant.org.delete 删除组织节点 🔴 · merchant.org.batch-delete 批量删除组织节点 🔴 · merchant.org.import 导入组织节点 🔴 |
| `channel-config-action.md` | merchant.channel-config.batch-add 批量新增渠道 · merchant.channel-config.batch-delete 批量删除渠道 🔴 |
| `recommend-config-action.md` | merchant.recommend-config.switches 仅切换开关 |
| `call-service-config-action.md` | merchant.call-service-config.save 保存客服配置 |
| `entry-rule-action.md` | merchant.entry-rule.sort 更新进店规则排序 🔴 · merchant.entry-rule.update-status 更新规则状态 · merchant.entry-rule.update-params 更新规则参数 |
| `search-intervention-action.md` | merchant.hot-keyword.create 新增热搜词 · merchant.hot-keyword.update 编辑热搜词 · merchant.hot-keyword.update-status 启停热搜词 · merchant.hot-keyword.delete 删除热搜词 · merchant.hot-keyword.sort 热搜词批量排序 · merchant.search-intervention.nlu.create 新增NLU规则 · merchant.search-intervention.nlu.update 编辑NLU规则 · merchant.search-intervention.nlu.delete 删除NLU规则 · merchant.search-intervention.nlu.update-status 启停NLU规则 · merchant.search-intervention.rerank.create 新增Rerank规则 · merchant.search-intervention.rerank.update 编辑Rerank规则 · merchant.search-intervention.rerank.delete 删除Rerank规则 · merchant.search-intervention.rerank.update-status 启停Rerank规则 |
| `material-action.md` | merchant.material.upload 上传素材 · merchant.material.move-group 素材移动分组 · merchant.material.batch-move-group 批量移动分组 · merchant.material.rename 素材改名 · merchant.material.delete 删除素材 🔴 · merchant.material.batch-delete 批量删除素材 🔴 · merchant.material.group.create 创建分组 · merchant.material.group.update 编辑分组 · merchant.material.group.delete 删除分组 🔴 |
| `shop-info-action.md` | merchant.shop-info.update 编辑店铺信息 🔴 · merchant.shop-info.upload-logo 上传店铺Logo · merchant.shop-info.upload-background 上传登录页背景图 |
| `supplier-action.md` | merchant.supplier.audit 入驻审核 🔴 · merchant.supplier.update 分区保存 · merchant.supplier.status 账户启停 · merchant.supplier.delete 删除供应商 🔴 · merchant.supplier.profile-review 资料变更复核 🔴 · merchant.supplier.license-ocr 营业执照OCR · merchant.supplier.draft.save 草稿保存 · merchant.supplier.draft.clear 草稿清除 · merchant.supplier.field-config.required-save 字段必填配置 🔴 · merchant.supplier.field-config.custom-field.create 自定义字段新增 · merchant.supplier.field-config.custom-field.update 自定义字段编辑 · merchant.supplier.field-config.custom-field.delete 自定义字段删除 🔴 · merchant.supplier.import 导入供应商 🔴 |
| `category-nav-action.md` | merchant.category-nav.create 创建模板 · merchant.category-nav.copy 复制模板 · merchant.category-nav.name.update 更新名称 · merchant.category-nav.icon-shape.update 更新图标形状 · merchant.category-nav.store-visibility.update 门店可见性配置 🔴 · merchant.category-nav.publish 发布 🔴 · merchant.category-nav.save-and-publish 保存并发布 🔴 · merchant.category-nav.offline 下线 🔴 · merchant.category-nav.set-default 设默认 🔴 · merchant.category-nav.delete 删除 🔴 · merchant.category-nav.invalid-store-bindings.remove 清除无效绑定 |
| `category-nav-content-action.md` | merchant.category-nav.front-category.batch-save 前台分类批量保存 🔴 · merchant.category-nav.category-products.add 分类商品添加 · merchant.category-nav.category-products.remove 分类商品移除 · merchant.category-nav.link-backend-category.preview 关联类目预览 · merchant.category-nav.link-backend-category 关联后台类目 🔴 · merchant.category-nav.clear-product-config 清空分类商品配置 🔴 |
| `theme-tabbar-action.md` | merchant.theme.save 保存风格草稿 · merchant.theme.publish 发布风格配置 🔴 · merchant.tabbar-scheme.create 创建导航方案 · merchant.tabbar-scheme.copy 复制导航方案 · merchant.tabbar-scheme.save 保存导航方案 · merchant.tabbar-scheme.publish 发布导航方案 🔴 · merchant.tabbar-scheme.offline 下线导航方案 🔴 · merchant.tabbar-scheme.set-default 设默认导航 🔴 · merchant.tabbar-scheme.delete 删除导航方案 🔴 |
| `placeholder-action.md` | merchant.placeholder-keyword.create 新增暗纹词 · merchant.placeholder-keyword.update 编辑暗纹词 · merchant.placeholder-keyword.delete 删除暗纹词 · merchant.placeholder-keyword.update-status 启停暗纹词 · merchant.placeholder-scene.create 新增场景 · merchant.placeholder-scene.update 编辑场景 · merchant.placeholder-scene.delete 删除场景 🔴 · merchant.placeholder-scene.update-status 启停场景 |
| `channel-trace-action.md` | merchant.channel-trace.add 新增追踪单 · merchant.channel-trace.edit 编辑追踪单 · merchant.channel-trace.update-status 启停追踪单 · merchant.channel-trace.custom-channel.add 新增自定义渠道 · merchant.channel-trace.import 渠道追踪导入 🔴 |

## 未开放（不调用，只整理需求）

> 本表是"不做"清单：命中的诉求**只说明当前不可执行并整理需求**，禁止拼凑多个已开放查询自行构造替代指标或替代实现（如自算"初始化完成度"、自建"完成情况清单"），引导用户到管理后台对应模块查看。

| 模块 | 原因 |
|---|---|
| 门店/组织/供应商/渠道追踪/自提点 导入模板下载、组织导出、自提点导出 | **二进制文件流响应**；产品决策仅开放 URL 型导出/下载，此型走管理后台（模板从「导入-下载模板」入口获取） |
| 地图密钥配置（map/config 系列）/ GL JS Key / GeoJSON | 租户级地图密钥管理面（SK 加密存储）与前端渲染辅助，非 Agent 面 |
| 供应商邀请码（invitations）/ 供应商选项（options）/ 凭证素材上传（materials） | 敏感凭证面或基线外新增端点，未纳入本轮盘点 |
| 配送区块创建/编辑 | 区域为地图多边形绘制产物（coordinates 顶点数组），无法可靠手工构造 |
| 渠道明细批量查询（batch-detail）/ 坐标点归属查询 / 进店规则新增删除（后端无端点） | 低频辅助面或后端未提供 |
| 首页商城信息（home/shop-info） | 访问统计字段当前为后端 Mock 数据，开放无意义 |
| 初始化引导清单（settings/init-checklist 系列） | 运维向导面，跨服务初始化路由 |
| 装修页面编辑（保存草稿/发布/下线/定时/设首页/回滚/编辑锁/设生效） | 依赖可视化装修编辑器，当前开放能力集只包含装修现态只读查询 |
| 小程序配置（内嵌授权页/小程序码） | 集成辅助与 base64 图片响应，低频非运营数据面 |
| 仓库删除 | 后端未提供端点（仅启停） |
| 素材引用注册/注销 | 业务系统间联动回调，非运营手工操作 |
| 推荐配置全量保存（save，含 appid/appsecret 修改） | **密钥明文传输风险**——appsecret 需经聊天通道明文传入，会暴露在会话记录与日志中；凭据类操作请到管理后台「推荐配置」页面 |

## 通用约定（商户域共享）

| 项 | 约定 |
|----|------|
| **调用方式** | 只能调用契约文件中标注了 capability 的能力：查询用 `当前运行时的 Capability 查询执行器`，写操作用 `当前运行时的 Capability 写操作执行器`。输入 `{capability, input, summary}`；`summary` 用一句话说明意图。**不得猜测或编造未登记的 capability** |
| **入参字段名** | 以契约参数表为准，**大小写敏感**；未读到目标能力的参数表之前，不要凭直觉或惯例拼写参数名（拼错只能得到缺参报错再返工） |
| **路径参数统一为 `id`** | 查询/写操作中以 ID 定位单一对象的能力（detail/update/delete/status 等），路径参数**一律叫 `id`**——不是 `storeId`/`warehouseId`/`categoryId`/`pickupSiteId` 等。即使能力名包含对象类型（如 `store.warehouses`），入参也传 `id` 而非 `storeId`。此为全局约定，各契约参数表不再逐个重复 |
| **身份与授权** | 身份由连接授权绑定；查询需 `mall.query`、写操作需 `mall.action` 授权，且受当前账号实时业务权限限制。不询问、不传入租户/账号/Token/服务名/路径/权限码；门店/仓库筛选 ID 属于业务参数，必须来自用户提供的已知 ID 或查询结果中的字段 |
| **ID 序列化** | 雪花 ID（19 位）一律**十进制字符串**，严禁传 Number（JS 精度上限 2^53-1）。响应中 ID 字段可能为 String（后端全局 Long→String） |
| **分页** | `pageSize ≤ 100`（建议 20 起步）；响应超出大小预算返回 `UPSTREAM_ERROR`，缩小 pageSize 或查询范围后重试 |
| **响应信封** | 成功 `{capability, data, traceId}`，`data` 为上游**原始业务数据**（不裁剪字段）；错误 `{errorCode, message, retryable, traceId}`。**导出类能力**（store.export / supplier.export / category-nav.export / channel-trace.export）已登记为查询能力（`mall.query`）——语义为只读导出，**经 Capability 查询执行器调用**，不要走写执行器 |
| **错误恢复** | `AUTH_REQUIRED`：请用户在 当前 Agent 重新连接；`SCOPE_INSUFFICIENT`：提示重新确认授权范围；`PERMISSION_DENIED`：停止该操作，不找替代方式绕过；`INPUT_INVALID`：对照参数表修正（业务校验由服务端执行）；`UPSTREAM_ERROR/UPSTREAM_TIMEOUT`：查询可稍后重试或缩小条件；**写操作禁止立即同参重试**——先回读核对是否已生效，确认未生效且参数无误后至多重试一次，仍失败如实报告由用户决策（写 500 可能已生效，盲目重试有副作用）。失败不等于无数据 |
| **写操作语义** | `当前运行时的 Capability 写操作执行器` 为纯执行器：单次提交（永不自动重试）并原样返回上游业务结果。**先读现态、确认后执行、执行后回读** 的流程纪律由本 Skill 的 flows 定义，模型必须遵守。超时/网络错误时结果不确定——先查询对象状态再决定如何向用户说明，不盲目重复提交 |
| **写操作确认** | 只在用户明确要求执行对应操作时调用写能力；创建/编辑等表单操作须先与用户确认关键字段（名称、地址、编码、绑定清单）。若当前执行器不具备所需确认交互，则停止写入并说明缺失条件。**确认选项须具体明确**——用「确认删除门店XX」而非「取消」「确认」等泛化标签 |
| **金额/容量** | decimal 传**数字**（如 `8.00`），单位元；禁止传分。库容同为数字 |
| **日期时间格式** | 各能力时间字段格式**不统一**，严格按参数表说明列传值。常见：`yyyy-MM-dd HH:mm:ss`（如 `2026-09-10 00:00:00`，空格分隔）、营业时间 `HH:MM`、渠道配置创建时间为 13 位毫秒时间戳 |
| **布尔值** | 传 `true`/`false`；禁止 `1`/`0`。⚠️ 布尔字段：运费模板 enabled、进店规则 enabled、LBS 推荐的 enableFixedAreaRecommend、推荐配置双开关、客服配置 enabled、可用列表里的 isBound/configComplete 等；**其余启停类状态字段是整数 0/1 不是布尔**（仓库/自提点/配送方式/履约模板/区块/热搜词/干预规则） |
| **枚举大小写** | 严格按 Layer 1 枚举字典取值：门店/仓库/运费计费/进店规则为**大写**（PHYSICAL、READY、BY_QUANTITY、MEMBER_STORE、LOCKED）；配送方式编码、搜索干预、固定区域层级为**小写**（express、nlu_rewrite、rerank_manual、pin_items、exact、province）。禁止猜测、禁止混用大小写 |
| **JSON 字符串字段** | 运费模板 chargeConfig、履约模板 timeConfig、自提点 businessHoursJson 为**序列化 JSON 字符串**（外层是字符串、内容是 JSON）——结构已在各参数表展开，构造时先组装对象再序列化为字符串。另有两类**回填透传** JSON 字符串：渠道追踪 pushPageInfo（链接选择器对象）、BRAND 布局分类 componentsJson（组件数组）——服务端不解析业务结构，编辑时以 detail/tree 原文回填，**不要自行构造** |
| **坐标** | 门店用 GCJ-02、自提点用 WGS84；经纬度为数字（经度 -180~180、纬度 -90~90） |

### 操作风险档位（写操作前必读）

| 档位 | 操作 | 说明 |
|------|------|------|
| 🔴 不可逆（执行前确认完整对象清单） | 批量删除门店（**级联删默认仓/自提点与全部关联，且不限草稿态**）、删除自提点、删除运费/履约模板、删除组织节点（单批）、删除固定区域、删除渠道 | 逻辑删除不可恢复 |
| 🔴 商业影响（执行前用户确认数值/清单） | 门店状态变更（尤其 CLOSED 终态）、批量状态、设默认门店（C 端兜底进店）、仓库启停、绑定/解绑配送方式（全量替换，级联删被移除方式的区块）、绑定行政区域/区块（改变实际配送范围）、解绑配送区块、完成配置（就绪生效）、运费模板创建/编辑（资损敏感）、履约模板创建/编辑（C 端时效承诺）、配送方式启停（C 端可选性）、进店规则排序/启停/参数（参数变更可切默认门店）、推荐配置保存、区块启停/区域排除、固定区域创建/编辑（全量替换地区清单） | 影响履约链路或公开可见 |
| 🟡 可逆写（做 + 向用户说明） | 创建门店（自动建默认仓/自提点，初始暂停营业）、门店编辑（建议带乐观锁 version）、仓库创建/编辑、自提点创建/编辑/启停、门店绑/解绑仓库与自提点、仓库排序、创建配送方式、配送方式编辑/排序、模板启停、绑定区块模板（null 可清除）、热搜词全操作、NLU/Rerank 增改启停删、渠道新增、客服配置保存、推荐开关切换、组织节点创建/编辑 | 可撤销或影响面小 |

**字段确认红线（禁止 AI 编造）**：门店地址与组织节点归属、仓库编码、计费金额（首费/续费/固定运费/起送价）、配送范围清单、进店规则兜底门店、推荐凭据（appid/appsecret）、客服电话、干预规则的动作目标（商品 ID/匹配值/加权倍数）——必须由用户明确给出或来自查询结果；行政区划编码必须来自行政区划树查询。**归属与类型先问后写**：门店所属区域节点（orgNodeId）、组织节点类型（type）用户未明确给出时，必须主动向用户追问确认——禁止从组织树/命名类比（如"××分部"类比 REGION）自行挑选；创建类操作任一关键参数（详细地址门牌、所属区域、类型、绑定清单）缺失时先追问，不提交。**格式前置预判**：对格式可判定的字段（客服电话等）提交前先做合法性检查，明显非法直接向用户说明格式要求，不消耗服务端拒绝。

### 调用前完整性检查（强制）

1. 展开读取入参表的全部叶子字段；出现嵌套结构（regions/recommendAreas/items/timeSlots/appointmentPeriods/list）继续读取其字段说明。
2. 区分必填、条件必填（如 PHYSICAL 门店地址、bindType=3 的 regions、rerank_manual 的动作三件套）与可选；满足当前枚举分支相关的条件。
3. 枚举使用 Layer 1 字典精确值并保持大小写；**整数 0/1 状态与布尔不要互串**。
4. 确认金额、坐标、时间的单位与 JSON 类型；ID 一律十进制字符串；JSON 字符串字段先组装对象再序列化。
5. 确认对象当前状态；门店状态按状态机流转（新建=SUSPENDED，CLOSED 为终态）；模板被引用时不可删。
6. 全量替换语义的操作（门店仓库排序、绑定配送方式/区块、固定区域编辑）先读现状，保留用户未要求移除的条目。

## 操作日志子域（system）特有纪律

- 操作日志子域**只读**：只使用 `当前运行时的 Capability 查询执行器`，本子域不开放任何写操作。结果恒为当前授权账号所属租户的操作日志。
- 日志连续浏览使用**无状态游标**：首查不传 `cursor`，后续将响应的 `nextCursor` 原样传回；`nextCursor=null` 表示没有更多。`pageSize` 为 1～100。
- 操作日志是**审计留痕**，用于回答「谁、何时、对哪个对象、做了什么」。它不等于业务单据流水：要查某个促销/商品/订单自身的变更流水，请用对应业务域能力。
- 日志只采集 `/admin/**` 的非 GET 请求，且仅覆盖已开启采集的服务；未登记语义的路由可能没有 `module`/`action`。因此**查不到不等于没发生**，结论要保守表述。
- `module`/`action` 是 ES 中真实日志的中文 distinct 值，**没有固定枚举**：先调 `ops.system.operation-log.filter-options` 取当前取值，再检索；选项为空时改用 `keyword`/`operatorName`，不猜值。
- `requestBody` 是 JSON 字符串：先解析、翻译成业务语言再讲给用户，不念英文驼峰字段名；明细先给条数摘要，不整段贴出。翻译有疑义时用 `httpMethod` + `uri` 关联到对应业务域 Skill 的接口描述（入参表与请求体字段同源），域映射表见 [system.md](references/domains/system.md)。
- 服务端脱敏只覆盖固定敏感键名且仅顶层，手机号、地址、邮箱、金额等不在其中——**回复用户前一律自行脱敏**（手机号保留前 3 后 4、地址只到省市区、令牌类一律「已隐藏」），拿不准就按敏感处理。详见 [system.md](references/domains/system.md)「输出脱敏纪律」。
- `41001` 表示 cursor 无效，应重新首查；`50001` 表示查询失败；查询幂等，超时可重试。
- 操作日志子域未开放：日志导出、日志删除与归档、数据安全审计日志、限流/熔断事件日志、AI Hub 平台操作日志。用户命中时只说明当前不可执行并整理需求。

## 环境与执行边界

- 缺失字段不等于零、不等于不存在；详情不含的字段（如门店详情不含绑定列表）用对应的列表能力查询，不要推断。
- 图片素材：相关文件能力尚未全部开放。创建配送方式等需要图标 URL 的操作，必须由用户提供已在云MALL可访问的图片 URL；用户给不出时说明缺少的材料，不把陌生 URL 当可信内部素材。
- 更新为**全量覆盖**语义的操作（编辑仓库/自提点、固定区域地区、绑定类操作）：更新前先读现态，保留用户未要求修改的字段与条目。
- 写操作超时或网络错误时结果不确定：先查询对象状态再向用户说明，不自动重复提交。
- 门店状态数据异常等报错属后端数据问题，如实转述错误信息并建议联系管理员。
