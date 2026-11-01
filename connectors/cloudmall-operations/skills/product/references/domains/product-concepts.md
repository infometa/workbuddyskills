# 商品域 — 实体模型与业务概念

> 实体模型、关键实体语义、各模块业务规则。
> 状态机迁移与枚举值查 `product-enums.md`（文中枚举名均在该表）。
> 能力契约见 `references/apis/product/`，操作流程见 `references/flows/`。

---

## 核心实体

### SPU（商品标准化单元）
- SPU 是商品的最小可管理单元，包含商品名称、类目、品牌、图片、规格模式等基础信息。
- 一个 SPU 可包含多个 SKU（1~500 个），SKU 是实际可购买的规格单元。
- 实体关系：`SPU 1:N SKU`，`SPU N:1 Category`，`SPU N:1 Brand`
- 关键字段语义：
  - `spuId`：业务雪花 ID（非 DB 主键），所有能力中的 `{id}`/`spuId` 均为此值
  - `productType`：商品类型（实物/服务/研学及兼容虚拟类型），影响配送和库存逻辑
  - `specMode`：规格模式（统一/多规格），决定 SKU 配置方式
  - `isDraft` + `isHidden`：双布尔状态控制（旧 SpuStatus 已废弃）
  - `source`：商品来源（运营端创建/导购发品），影响审核流程
  - `auditStatus`：审核状态（仅导购发品需要审核）
  - `sortOrder`：排序值，影响列表展示顺序

### SKU（库存量单位）
- SKU 是 SPU 下的具体规格单元，是用户实际购买和库存管理的最小粒度。
- 实体关系：`SKU 1:N Inventory`（一个 SKU 在多个仓库有库存记录）
- 关键字段：
  - `skuId`：业务雪花 ID
  - `specInfo`：规格信息 JSON 字符串（多规格模式下的颜色/尺寸等）
  - `price`：售价（元），始终必填，≥0.01，精度(8,2)
  - `status`：可售/禁售状态
  - `externalSkuId`：商家 ERP 编码（可选）
  - `weight`/`volume`：重量(kg)/体积(m³)，影响运费计算
  - `minPurchaseQty`/`purchaseLimit`：起购/限购数量（件）；`purchaseLimit ≥ minPurchaseQty`（服务端跨字段校验）；编辑时新增的 SKU 若 SPU 处于禁售态则继承禁售

### 库存（Inventory）
- 库存按 SKU + 仓库维度管理，每个 SKU 在每个仓库有独立的库存记录。
- 实体关系：`SKU 1:N Inventory N:1 Warehouse`
- 仓库库存模型：
  - `physicalQty`：总库存（物理库存）
  - `lockedQty`：订单占用库存
  - `availableQty`：可用库存 = `physicalQty - lockedQty`（系统计算，不可直接设置）
  - `version`：库存更新的乐观锁版本；`reservedQty` 是门店分配预留量，不能代替订单占用量。
- 仓库类型：`STORE_WAREHOUSE`（门店仓）/ `FRONT_WAREHOUSE`（前置仓）/ `MAIN_WAREHOUSE`（主仓）

### 门店商品（StoreProduct）
- 门店商品是 SPU 在特定门店的上架实例，独立于 SPU 本身的上下架状态。
- 实体关系：`SPU 1:N StoreProduct N:1 Store`，`StoreProduct 1:N StoreProductSku`
- 门店商品 SKU 可有独立的门店价（`storePrice`），为 null 时使用全局价。
- 门店商品 SKU 有独立的预留库存（`reservedQty`）。
- 门店商品的上下架影响该门店 C 端展示，不影响 SPU 本身。

### 类目（Category）
- 类目是商品的分类体系，支持 1~5 级树形结构。
- 类目编码（`categoryCode`）是业务标识，支持递归子孙查询。
- 类目可从平台模板同步（`sync-from-platform`）。

### 品牌（Brand）
- 品牌关联到 SPU，一个 SPU 只有一个品牌。
- 品牌可绑定/解绑 SPU（批量操作）。

### 草稿（Draft）
- 草稿是商品创建表单的 JSON 快照（`productData`），按当前用户隔离；每用户上限 50 份。

### 平台共享商品（跨租户商品）
- 平台共享商品（如「沃尔玛精选」类目下的外部供货商品）由平台统一维护，对当前租户**部分可见**：
  - `spu.search` / `spu.search-simulate` 等列表检索**可以搜到**（含数量统计）；
  - `spu.detail` / `spu.skus` / `inventory.search` 等单笔详情与库存类能力**按租户隔离，查不到**（业务码「商品不存在」）。
- 「列表可搜到、详情查不到」**不止一种根因，先判别再定话术**：
  - **根因一 · 平台共享商品**：商品挂平台共享类目（如沃尔玛精选）——话术：「该商品为平台共享商品，租户侧详情/库存暂不可查」，**不得**表述为「商品不存在/已删除/ID 有误」误导排查方向。
  - **根因二 · 商品已不可经本端操作（如已删除后索引数据滞后于实际状态）**：本租户普通类目商品出现同症状时，索引可见 ≠ 商品可操作——话术：「列表可见为索引数据，该商品当前无法经本端读取/操作，可能已被删除或状态已变更」，引导用户在管理后台核实；**不得**凭索引可见断言商品在售，也**不得**未核实即断言商品不存在。
- **通用纪律**：两种根因下该商品均不可经本端写操作（编辑/删除等会同样被拒）；**禁止凭列表/搜索出参构造对该商品的写操作**。

---

## 业务规则

### 商品创建与编辑
- 商品媒体（主图/详情图/视频）经 upload-media 上传取 URL：图片 jpg/jpeg/png/gif/bmp ≤5MB、视频 mp4/flv ≤200MB；也接受用户提供的云MALL 可访问 URL。
- VIRTUAL（虚拟商品）强约束：仅 SINGLE 规格 + 单 SKU，`benefitConfig`（关联券模板）必填（服务端实时校验券可用性）；编辑不可改 productType。
- 审核入参幂等键（idempotencyKey）服务端未实现（仅记录日志）——防重靠流程纪律。
- 商品名称 4~256 字符。
- 主图 1~5 张，第一张为主图。
- 规格模式为 SINGLE 时 SPU 顶层 `price` 必填；MULTI 时各 SKU `price` 必填。
- SKU 数量 1~500 个。
- 创建时不传 `skuId`（系统生成）；更新时已有 SKU 传 `skuId`，新增 SKU 不传。
- 更新为**全量覆盖**语义：须传完整 SKU 列表，未传的已有 SKU 会被**归档**（下架保留数据，非物理删除）。
- 更新能力不接收 `source` 和 `isHidden`（这两个只在创建/专用能力控制）。
- 品牌条件必填：PHYSICAL/VIRTUAL 必填；SERVICE/STUDY_TOUR 可空。
- 开放能力只走 ADMIN 来源；`source`/`supplierId`/`skipReAudit` 不在开放契约内。

### 商品上下架
- SPU 上架（on-shelf）= 启用可售；下架（off-shelf）= 禁售。
- SPU 隐藏（hide）= 前端不展示但不删除；取消隐藏（unhide）= 恢复展示。
- 上/下架均要求非草稿、未隐藏；隐藏商品须先取消隐藏。
- SPU 上架 ≠ 在 C 端可售，还需门店上架 + 有库存。
- 批量操作上限 200 条 SPU；SPU 侧批量结果含 `failures[]` 逐条失败明细（门店商品侧批量仅计数，无明细——两域口径不同）。

### 库存管理
- 库存按 SKU + 仓库维度管理，需先初始化（init）才能调整。
- 总库存调整需传乐观锁 `version`，避免并发冲突。
- 调低总库存可能导致预留库存被自动调低（返回 warning）。
- 库存查询返回的是仓库维度记录；SKU 行的 `totalStock` 是跨仓库聚合；仓库类型三值中 `MAIN_WAREHOUSE` 语义为「大仓」。
- 批量导入有两种模式：商品导入（spu.import）**同步**返回结果计数；库存导入（inventory.import）**异步受理**返回 taskId，经 import-task 轮询（PENDING/PROCESSING → SUCCESS/PARTIAL_FAIL/FAIL）。
- 导出为 COS 预签名 URL 型（60 分钟时效）：inventory.export（exportScope=ALL/FILTERED 必填）、store-product.export；商品列表导出（spu/export）为文件流型，不开放。

### 类目与品牌
- 类目支持 1~5 级，通过 `parentCode` 关联；一级类目 `parentCode` 为空字符串。
- 类目批量维护（batch-save）为四组操作混合提交（additions/updates/deletions/sortChanges）：删除**有子类目**或**挂有商品**的类目被拒绝；同级类目名称唯一；层级上限 5 级。
- 品牌：名称 ≤50 字符、全局重名拒绝；logo 仅 jpg/jpeg/png、≤2MB（upload-logo 上传取 URL）；**品牌下挂有 SPU 时删除被拒绝**，须先解绑全部商品。
- 品牌绑定/解绑 SPU 直接改写 SPU 的品牌归属；入参为裸 `{spuIds:[...]}`（无表单 DTO）。
- 平台类目一键同步（sync-from-platform）为一次性初始化运维操作，不开放。

### 门店商品运营
- 门店价（storePrice）为门店维度覆盖价；storePrice 必传——当前版本省略传值不会恢复全局价（后端置空更新不生效），恢复全局价请在管理后台操作。
- 预留库存（reservedQty）从可售中扣留；单条更新支持 `expectedOldQty` 乐观锁。
- 门店商品审核（audit）针对导购发品（GUIDE_PUBLISH）：APPROVE/REJECT，驳回原因必填。

### 评价管理
- 评价含首评与追评；追评审核用 append-audit（驳回原因必填）。
- 回复（reply）以运营方身份公开展示；可先查回复模板（reply-templates）起草，但回复传最终文案（content），不传模板ID。
- 审核决定评价是否展示（APPROVE 展示 / REJECT 隐藏）。
- 统计聚合为 admin 模块每 5 分钟定时任务自动执行（查询另有约 5 分钟缓存，数据略有延迟属正常）。

### 研学营期名额
- 按「场次」管理：`totalQuota`（总量）、`reservedQty`（预留）、已售、锁定（locked，下单未支付）；可售 = 总量 − 预留 − 已售 − 锁定（口径与后端 safeAvailable 一致，lockedQty 见 list 返回）。
- 批量更新带乐观锁版本（expectedVersion），版本冲突项需重查后重试。
- 仅平台管理员/运营角色可操作（权限不足返回 PERMISSION_DENIED）。

### 静态标签
- 标签为 SKU 级关联；绑定（bind-skus）为**全量提交语义**——`skuIds` 是最终关联全集，服务端差量增删；空数组 = 清空关联。
- 标签定义：名称 ≤10 字符（租户内唯一）、优先级 1~9999、有效期 `PERMANENT`（永久）/ `CUSTOM`（validFrom~validTo 必填且成对）；删除不可逆（关联关系随之失效），单批 ≤200。

### 搭配（Collocation）
- 单店维度的商品组合营销实体：归属门店 + 商品列表（含主图锚点坐标/标签/方向）。
- 状态：上线（online）/ 下线（offline）/ DELETED（逻辑删除态）；编辑为全量覆盖语义（先读详情）。
- 海报链路：主图须经专用 `poster-image` 上传（独立租户目录 `product/collocation-poster/{租户ID}/`，JPEG/PNG/WebP ≤2MB，30 分钟签名 URL）；`poster-config-save` **强校验 mainImageUrl 归属本租户该目录**——素材中心 URL、跨租户 URL、陌生外链一律被拒。无 AI 生成链路。
- 投放物料：`launch-material` 聚合微信太阳码（MySQL 状态源）+ URL Link/短链（Redis TTL 单飞）；物料异步生成，首屏可返回 GENERATING；`launch-material-retry` 仅 FAILED 可重试（否则 409）。

### 商详装修（DetailLayout）
- 商详页 9 模块（benefit_info/delivery_info/nearby_store/product_params/product_review/faq/collocation/product_detail/price_explanation）的排序与启停配置；按模块逐行存 DB，保存为全量替换（删旧+插新+写日志）；**至少启用 1 个模块**。
- **编辑锁协议**：保存强校验持锁（Redis SETNX，租户级，TTL 600 秒；同 userId 重复 acquire=续租；被他人持有时 acquire 返回 locked=true+lockedBy）。流程：acquire → 读现态确认 → save → release。
- 读侧兼容：benefit_info 为 2026-09 新增模块，存量配置读取时自动补全（enabled=true 追加尾部）。

### FAQ（商详常见问题）
- 问题 ≤30 字、答案 ≤300 字纯文本；`sort` 越大越靠前，create 不传 sort 追加末尾（MAX+10）、update 不传保留原值；FAQ 总数上限 50（创建时拦截）。
- 生效期：effectiveStart/End 均可空（=永久）；生效状态三态 IN_EFFECT / NOT_STARTED / EXPIRED。
- reorder 为 `faqIds` 数组顺序=最终顺序（≤50）；toggle 返回切换后新状态。

### 到店服务（StoreService）与预约模板
- 到店服务 = 到店履约的预约类服务配置面（服务定义 + 预约模板 + 门店投放 + 时段容量 + 确认模式），非核销类。
- 三态 `draft`/`online`/`offline`（小写枚举）；`isDraft` 控制草稿/发布，**发布时 templateId 必填**；`confirmMode`：auto（自动确认）/ store_confirm（门店确认）。
- 门店差异化模板分配（storeAssignments：storeId→templateId，两级回退到服务级 templateId）；旧 storeIds 已 @Deprecated。
- **update 返回超卖警告**：被预约引用时段下调 maxPerSlot 时返回 overBookedSlots（门店/日期/时段/当前预约数/新上限）——属保护机制（预约修改保护 v1.1），警告须如实转告。
- 预约模板：名称**租户内唯一**；营业时段 HH:mm、粒度 30/60/120 分钟、适用星期 1~7、提前预约规则（day/hour）、最长预约天数（默认 7）、预约信息字段 name/phone。
- **模板删除引用校验**：被到店服务（默认模板或门店分配）引用时拒绝删除，须先解除关联。
- 跨域依赖：trade 域预约规则/记录运行时经 Feign 回查本域模板（内部面）。

### 赠品（送礼玩法）配置
- 租户级开关 + 可送礼商品范围：金额区间（minAmount~maxAmount，元）∩ 排除类目（excludedCategoryCodes）∪ 白名单（whitelistSkuIds）。
- 分享素材（分享图/海报/领取结果图 URL）+ 默认祝福语（≤100 字）+ 分享文案（≤20 字）；保存**不做内容审核**。
- 白名单配置前用 `validate-skus` 批量校验候选资格（纯校验无副作用，返回 selectable/reason）。

### 商品通用配置（GeneralConfig）
- 人工审核时效（reviewTimeout，秒，≤31622400）+ 默认好评时间（defaultPraiseTime，秒）+ 商品列表缺货过滤（filterOutOfStockProduct，不传保留现有值）；upsert 保存。
- 首次未配置时查询返回 null（如实告知）。
- ⚠️ **与评价设置（review/setting）同源**：两者读写同一张配置表同一行 JSON（`reviewTimeout` 是同一个字段）——评价设置保存会直接改写商品通用配置的审核时效，两处操作需向用户说明会互相影响。

### 搜索模拟
- 运营端只读验证面：C 端同款搜索请求（keyword/分页/排序/debug/disableCache）+ 联想词查询（外部 Suggest 转发 + 静默降级，空/失败均 200 空列表）。
- abs 摘要独立查询依赖 X-Store-Warehouse 定店定仓 Header（Capability 调用链不注入 → 恒空），不开放。

### 描述属性（DescriptionAttribute）
- 按类目配置的发品描述模板（属性 + 预设值）；按类目查询（发品参考）与增改删维护均已开放。
- 交互方式四种：`TEXT_INPUT` / `NUMBER_INPUT` / `SELECT_SINGLE` / `SELECT_MULTIPLE`。
- **同一类目下属性名称唯一**；编辑时 `attributeValues` 为全量覆盖（≤20 个，未保留的旧值被删除）。

### 商品扩展字段（ExtensionField）
- 发品表单的可配置自定义字段：`fieldCode + targetLevel` 组合唯一（编码小写字母开头 2-64 位）。
- 字段层级 `ALL`/`SPU`/`SKU`；字段类型 12 种（TEXT/TEXTAREA/NUMBER/MONEY/DATE/DATETIME/BOOLEAN/SINGLE_SELECT/MULTI_SELECT/CASCADE/IMAGE/FILE）。
- 必填规则 `NONE`/`ALWAYS`/`CONDITION`（条件必填配 linkageConfig：`[{field,operator,value}]` JSON 数组；**服务端仅强制 ALWAYS**，CONDITION/linkageConfig 服务端不解析）；选择类字段选项 optionConfig 为 `[{code,label}]` JSON 数组。
- 字段总数上限 10；停用（set-enabled=false）优先于删除；删除不可逆。
- 存在 5 个系统预置字段（bizType/serviceDuration/servicePickupMethod/platformSaleForbidden/storeSlotCapacity），`editable=false` 为系统行为，种入端点（batch）属运维面不开放。
