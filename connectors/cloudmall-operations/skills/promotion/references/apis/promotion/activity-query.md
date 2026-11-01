# 促销域 — 促销活动查询契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-activity.md`
> 出参为上游**原始业务数据**（不裁剪字段）。以下按「关键字段来源 / 枚举 / 格式敏感」标注关键字段；未列出的展示型字段透传给用户即可。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本域**金额一律单位分（整数）、时间为毫秒时间戳、ID 为十进制字符串**，与商品域"元"的约定不同。
> 能力索引（前缀 `ops.promotion.`）：activity.search · activity.detail · activity.goods-search · activity.goods-all · activity.logs · activity.stats · stackable-rules · passcode.check · import.parse
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）执行。
> 写操作（创建/审核/暂停/恢复/停用/删除）见 `activity-action.md`；草稿期详情/编辑走 `pending-query.md`。

---

## ✅ 活动分页搜索 — `ops.promotion.activity.search`

**排序口径**：服务端按 `createdTime` 降序分页（同创建时间再按 ID 等字段排序），不支持按 `updatedTime` 排序。用户问「最近更新」时，不得把第一页当作最近更新；若匹配总数不超过 100，可用 `pageSize:100` 取齐后按返回的 `updatedTime` 降序选取。超过 100 条时，须继续分页取齐才能保证全量排名；不能取齐就明确说明无法保证全租户的最近更新顺序。


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| tab | String | 否 | 状态 Tab：`all`/`draft`/`pending`/`rejected`/`not_started`/`in_progress`/`paused`/`ended`。draft/pending/rejected查待审核表；四个生命周期Tab查正式主表；all或缺省合并正式记录与sourceType=0的新建pending。all或缺省tab同时指定promotionStatus时只查正式记录；生命周期tab与promotionStatus同时传时以tab为准，推荐只用tab。后续操作按每行dataSource/sourceType选择 |
| title | String | 否 | 活动标题模糊搜索。⚠️ **字段名是 `title`**——传 keyword 会被静默忽略并返回全量列表 |
| promotionId | String | 否 | 活动 ID 精确搜索 |
| promotionIds | String[] | 否 | 活动 ID 列表；与 promotionId 同传时取交集。查新建 pending 的预分配 ID 用这两个字段，不用数字 title 代替 |
| promotionCode | String | 否 | 当前活动搜索不消费该字段，不能按大类筛选；按已确认子类型使用 promotionSubCode，券模板优先走 coupon-template.search |
| promotionSubCode | String | 否 | 活动子类型（见 promotion-enums.md 的 PromotionSubCode；支持逗号分隔多值） |
| promotionStatus | Integer | 否 | 活动状态 code（1..7，见 PromotionStatus） |
| checkStatus | Integer | 否 | 当前仅筛正式主表的审核状态（含 2 已通过）；all 的 pending 分支不应用此条件，draft/pending/rejected 按 tab 决定审核态并忽略此字段。查草稿/待审/驳回用对应 tab |
| creatorName | String | 否 | 对持久化 createdBy 文本做模糊匹配，不按回显 createdByName 查询，也不解析显示姓名为账号 ID |
| startTimeBegin / startTimeEnd | String | 否 | 活动开始时间范围（毫秒时间戳） |
| endTimeBegin / endTimeEnd | String | 否 | 活动结束时间范围（毫秒时间戳） |
| displayStatus | String | 否 | 仅 promotionSubCode 精确为 PRESELL 且查询路由为正式主表时生效；all 的 UNION 和草稿类 tab 均不应用。只是粗粒度状态翻译，见下方限制 |
| bizType | String | 否 | PROMOTION/COUPON_TEMPLATE，仅筛 pending 分支；不筛正式主表，不能据此隔离 all 的全部行 |
| channelCodes / excludeChannelCodes | Integer[] | 否 | 当前活动搜索均不消费；按领券渠道查模板使用 coupon-template.search 的渠道契约，不能移植到活动搜索 |
| excludeEnded | Boolean | 否 | 当前活动搜索不消费；按需要分别查询 not_started/in_progress/paused 等生命周期 tab，不能把 all 响应称为已排除结束状态 |

**组合筛选与分页限制**：all 加 checkStatus=1 仍会混入未受该条件筛选的 sourceType=0 草稿和驳回行，不能将其 total 当作待审数量。数字 title 在正式主表匹配标题或 promotionId；独立草稿类 tab 只有请求同时传 bizType=COUPON_TEMPLATE 才匹配标题或 templateId，否则匹配标题或 promotionId（券草稿也不例外）。all 的 pending 分支只匹配标题。已知活动 ID 使用 promotionId/promotionIds，不能把券模板 ID 填进这些字段。确需本地二次筛选或全量计数时，必须分页取齐候选后核对；仅核对一页就只报告该页已核验范围，不能把原始 total 当筛后总数。

**预售展示筛选限制**：中文值“未开始”映射主表未开始/预热，“定金支付中”与“预售中”均映射进行中，“尾款支付中”与“已结束”均映射已结束，“待审核”映射主表 checkStatus=1；未识别值不增加条件。要让过滤生效须选择正式生命周期 tab，或 all/缺省 tab 配合明确 promotionStatus 路由到主表；两个条件会同时应用，不能传相互矛盾的状态。它不按定金/尾款窗口精确筛选，结果是否正处支付阶段还需按详情的实际预售模式和日期核对。查待审预售用 tab=pending，不用 displayStatus 绕过草稿数据源。

**预售列表回显**：以下派生规则只适用于 dataSource=main；pending 行 displayStatus 为 null，按 checkStatus/promotionStatusDesc 识别审核态，不要求显示“待审核”。主表行的 displayStatus 是派生展示值，与上述粗筛选条件不是同一口径。checkStatus=1 优先显示“待审核”；其他主表记录中未开始2、进行中4、已结束5有对应展示值，预热3/暂停6可能为 null。定金类已结束5的“尾款支付中”按服务端应用时钟与尾款窗口推导。查not_started返回预热行且displayStatus为空可以成立，以实际promotionStatus为准，不把空展示值当接口错误。

### 出参（分页，原始数据）

- **关键字段来源**：`records[].promotionId`（→ 详情/暂停/恢复/停用/删除/日历归组）、`records[].pendingId`（dataSource=pending 行 → 编辑/提审/撤回/审核/删除草稿）
- **混合来源**：all行不全是正式活动。all中的pending行（sourceType=0）使用预分配promotionId，不证明正式主表已存在；草稿操作使用pendingId。草稿类Tab还可含sourceType=1的变更草稿，其promotionId是已有正式活动ID：查看线上配置可查正式详情，查看或操作变更草稿仍用pendingId。dataSource=main按正式活动标识进入详情或生命周期操作；all的total不能直接称为正式活动数。
- **枚举字段**：`promotionStatus`（1..7；**dataSource=pending 行恒为 null**，状态语义看 checkStatus 与 promotionStatusDesc）、`promotionSubCode`、`dataSource`（**`main`/`pending`，小写**——按小写字面量过滤）、`checkStatus`（pending 的 0/1/3；主表还可为 2 已通过）、`sourceType`（0/1）
- **格式敏感字段**：`startTime`/`endTime`/`preheatStartTime`（毫秒时间戳，经全局 Long→String 序列化为十进制字符串，数值比较前先转数字）、`createdTime`（yyyy-MM-dd HH:mm:ss）
- **布尔标志**：`hasPendingChange`（变更审核中，仅主表行；true 时禁止编辑/删除/停用）
- 按 ID 找回使用 promotionId/promotionIds；数字 title 的精确 ID 匹配范围见上方组合筛选限制，不能认为所有数据源一致。

### 调用示例

```json
{"capability":"ops.promotion.activity.search","input":{"pageNum":1,"pageSize":20,"tab":"in_progress","title":"满减"},"summary":"查询进行中的满减活动"}
```

---

## ✅ 活动详情 — `ops.promotion.activity.detail`


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | **主表**活动 ID（搜索结果 dataSource=main 行的 promotionId）。⚠️ 仅查主表——草稿/待审核/驳回期（审核通过前）主表无记录，传创建响应的预分配 promotionId 会报「活动不存在」；该阶段请用 `ops.promotion.pending.detail`（pendingId） |

### 出参（原始数据）

- ⚠️ **详情不再返回商品列表**：商品清单已由后端从详情主接口拆成独立分页能力，**详情响应里取不到 SKU**。需要商品清单（→ 库存查询/增库存/编辑基线）一律走 `ops.promotion.activity.goods-search` 或 `goods-all`；详情只给 `goodsCount`（关联商品总数，整数）。
- **关键字段来源**：`promotionId`（→ 各状态操作）、`audienceTagValueIds`（人群标签值回显）、`goodsCount`（商品总数）
- **枚举字段**：`promotionSubCode`、`promotionStatus`、`promotionLevel`（1-4）、`audienceType`（ALL/SPECIFIED/PASSCODE）、`productScopeType`（all/product/category/brand）
- **格式敏感字段**：`startTime`/`endTime`/`preheatStartTime`（毫秒时间戳）、`createdTime`（yyyy-MM-dd HH:mm:ss）
- **布尔标志**：`passcodeEnabled`
- **范围回显（编辑回填锚点）**：
  - `categories[]`（`{id, name}`）/ `brands[]`（`{id, name}`）——⚠️ **仅部分活动类型填充**：满减、满折、N件Y元、买赠/满赠四类活动会填充；秒杀/直降/预售/口令购/拼团/周期购**不填充，字段为 null**。且 `name` **恒为空串 `""`**（名称需另查商品域，服务端不回填）——**回显的类目/品牌编码取 `id`，不要指望 `name`**。
  - `scopeList[]`（`{scopeType, scopeCategory, scopeValue}`）为原始范围行，**全类型恒有**：`scopeType` 4/5=商品范围、6=类目、7=品牌、9=门店（配 `scopeCategory`=2 时 `scopeValue` 即门店 ID）、3=人群（`scopeCategory`=2 时即标签值 ID）。类目/品牌未填充时以 `scopeList` 为准（6/7 的 `scopeValue` 即类目编码/品牌 ID）。
  - `storeIds[]`（从scopeList派生，空表示回显全部门店；**不等于写请求可传[]**，写入已确认ALL用省略/null，正式[]拒绝）。
  - ⚠️ `audienceType` 是**服务端派生值**（有标签值→`SPECIFIED`，否则 `ALL`；`extJson.audienceMode=PASSCODE` 时→`PASSCODE`），**可能与创建时提交的值不同**——回显不等于原入参。
- ⚠️ **口令购（ENTERPRISE_PURCHASE）详情回显口令码明文**：`passcode` 原样返回（从活动扩展配置的口令键读取），未脱敏。属业务资产，只在用户明确要求核对时转述，不要写进报告/备注类字段。
- `operationValue`/`extJson`/`rules` 为规则结构（见 promotion-concepts.md「规则结构」）；买赠活动另有 `giftItems`/`mainProducts`（**结构见 specialty.md**）。⚠️ 出参 `rules` 为后端从 canonical operationValue **回映射**的规则（actionParams 逐元素展开成多条 action、ruleIndex 重排、maxDiscountValue≤0 转 null——**与入参形态有差异，勿原样回传编辑**，编辑基线用 pending.detail 快照）；周期购/拼团详情无 rules。顶层 `ruleDescription` 是整条规则的中文摘要字符串（「满100元减10元」），**不在 rules 内的单条规则上**。

### 调用示例

```json
{"capability":"ops.promotion.activity.detail","input":{"id":"4100000000000000001"},"summary":"查看活动完整配置"}
```

---

## ✅ 活动商品分页 — `ops.promotion.activity.goods-search`


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 活动 ID |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..200，默认 20 |

### 出参（分页，原始数据）

- ⚠️ **活动商品只能从这里取**——详情主接口已不返回 `goodsList`（见 detail 节），本能力与 `goods-all` 是商品清单的唯一开放来源。
- 每项：`spuId`/`skuId`/`goodsRole`（0 默认 / 1 主品 / 2 赠品）/`sortNo`/`discountType`/`discountValue`（分或千分比，按 discountType）/`extJson`（SKU 级扩展，键集见 specialty.md）/`activityStock`（LIMITED 件数，UNLIMITED 为 null）/`unlimited`（true=不限量；**null=库存元数据不可确认，不得当不限量展示**）；周期购另附 `periodBuyGoodsConfig` + `periodBuyGoodsStockView`（`{skuId, totalCount, availableCount}`，UNLIMITED 时两 count 为 null）。
- 无商品名称关键字筛选参数（后端未提供，传了也被忽略）。

### 调用示例

```json
{"capability":"ops.promotion.activity.goods-search","input":{"id":"4100000000000000001","pageNum":1,"pageSize":20},"summary":"分页查看活动商品"}
```

---

## ✅ 活动商品全量列表 — `ops.promotion.activity.goods-all`

- 编辑/复制场景专用，不分页

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 活动 ID |

### 出参（数组，原始数据）

- 同 goods-search 的每项结构（详见 goods-search 节字段清单）。⚠️ 商品数多时响应可能超大小预算（UPSTREAM_ERROR），此时改用 goods-search 分页。

### 调用示例

```json
{"capability":"ops.promotion.activity.goods-all","input":{"id":"4100000000000000001"},"summary":"全量拉取活动商品用于编辑"}
```

---

## ✅ 活动操作日志 — `ops.promotion.activity.logs`


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 活动 ID |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |

### 出参（分页，原始数据）

- **枚举字段**：`operationType`（CREATE/UPDATE/SUBMIT/PAUSE/RESUME/DELETE/START/END/PREHEAT/STOCK_INCREASE/STOP，另可能出现审核链写入的 CREATE_PENDING/SUBMIT_PENDING/WITHDRAW_PENDING/DELETE_PENDING/START_EDIT/CHECK_APPROVED/CHECK_REJECTED/UPDATE_TITLE——未识别值原样透传展示即可）
- **格式敏感字段**：`operatedAt`（毫秒时间戳，经全局 Long→String 序列化为十进制字符串）；`remark` 为操作备注文本
- ⚠️ `operationTypeDesc` 为中文描述：未识别的 `operationType` **原样回传编码本身**，`operationType` 为 null 时**恒为空串 `""`**——不要用它反推枚举。
- ⚠️ `operatorName` 初值是**操作人 userId 字符串**，仅当姓名翻译成功才被覆盖为真实姓名——回显成数字 ID 是正常的降级表现，不是数据错误。

### 调用示例

```json
{"capability":"ops.promotion.activity.logs","input":{"id":"4100000000000000001","pageNum":1,"pageSize":20},"summary":"查看活动操作日志"}
```

---

## ✅ 活动统计 — `ops.promotion.activity.stats`


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| promotionSubCode | String | ✅ | 活动子类型（见 PromotionSubCode，如 MYJ/SECKILL） |

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| totalCount | 返回statusCounts时为all Tab可见资源数，包含正式记录与新建pending；未返回statusCounts的当前统计路径为非删除正式主表记录数，不含pending。两种口径不能混算 |
| activeCount | 进行中活动数 |
| issuedCount | 已发放券数（**仅券类 subCode 有值，非券恒 0**） |
| typeSpecificCount / typeSpecificLabel | 类型特有统计数与标签——券类计数包含锁定+已使用，标签为「累计核销」，不能当全部已完成核销；**非券恒为 0 与空串 `""`** |

`statusCounts`是可选的八态Tab计数Map。当前订单促销统计覆盖的子类型会返回该字段；已验证MYJ返回，其他类型以真实响应为准，不能宣称恒缺失或恒存在。

- 存在时按原字段展示：all采用正式记录+sourceType=0新建pending口径；draft/pending/rejected采用待审核表口径（可包含变更草稿），生命周期Tab采用正式资源口径。各Tab不保证互斥或都包含在all中，不能相加推算all、凑100%、用all作各Tab占比分母或按差额补“其他”。
- 缺失时不补0、不伪造Map。确需分状态查询时用activity.search按相同子类型及筛选范围分别查询各tab的total；券模板统计只用于券模板，不替代普通活动统计。查询间状态可能变化，不冒充同一时点的快照。

### 调用示例

```json
{"capability":"ops.promotion.activity.stats","input":{"promotionSubCode":"MYJ"},"summary":"统计满元减活动各状态数量"}
```

---

## ✅ 叠加规则查询 — `ops.promotion.stackable-rules`

- 返回子类型之间的类型级叠加规则。核对两个具体活动时，还需读取各自activity.detail的stackableExclusions实例配置；本查询没有活动ID入参，不能代替实例详情或完整结算判断。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| subCode | String | ✅ | 活动子类型 |

### 出参（数组，原始数据）

- **枚举字段**：`subCode`、`targetSubCode`（见 PromotionSubCode）、`editable`（0 系统锁死 / 1 运营可改）、`conflict`（**0 可叠加 / 1 互斥**）

### 调用示例

```json
{"capability":"ops.promotion.stackable-rules","input":{"subCode":"MYJ"},"summary":"查询满元减与各活动类型的叠加互斥关系"}
```

---

## ✅ 口令码占用校验 — `ops.promotion.passcode.check`

- 只读预检

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | String | ✅ | 口令码，≤20 字符 |

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| occupied | 是否已被占用 |
| normalizedCode | 归一化后的口令码——⚠️ **明文值**（业务资产，非脱敏），只在用户报码核对时转述，不要写入标题/备注/导出内容 |
| status | 占用方状态：WAIT_EFFECTIVE / ACTIVE / INACTIVE；**未占用恒为 null** |

### 调用示例

```json
{"capability":"ops.promotion.passcode.check","input":{"code":"AUTUMN2026"},"summary":"校验口令码是否可用的占用状态"}
```

---

## ✅ 活动商品 Excel 导入解析 — `ops.promotion.import.parse`

- multipart 上传（文件经运行时文件通道提交）
- **任务完成条件**：用户要求解析或校验促销商品清单时，调用本能力后才报告解析结果；本地预览和商品查询只可辅助检查，不能称为接口解析。文件引用取实际上传后的工作区相对路径，不添加根目录前缀，不把附件显示名猜成路径；文件不可访问或解析失败时说明具体原因，不用人工整理冒充成功响应。仅要求通用表格预览且不涉及促销商品匹配时，不强行调用本能力。
- **部分失败与后续处置**：先按真实 successItems/errorItems 展示成功数、错误数及原因；rowNumber 是解析器处理的数据行序号（不含表头）；没有空行时，Excel 物理行号为 rowNumber+1。有空行时不直接相加，结合文件预览与 SPU/SKU 定位原行，无法可靠对应时保留解析序号并说明。errorReason 原样展示，不把查询失败或非数字 ID 等情况扩大解释为对象确实不存在或单元格确实为空。当前“商品已下架”分支使用商品 isDraft/isHidden，不能把不可售、SKU 禁用或库存为 0 一律改记为解析错误；需要创建活动时，再按实际运营条件核验可售状态和库存。解析成功不证明已满足活动创建条件，不自动丢弃错误行后创建；用户决定修正文件或仅提交成功行后，再进入写操作确认与草稿链路。用户取消时停止后续创建/导入。
- **语义**：上传 Excel/CSV（第 0 列 spuId、第 1 列 skuId；首行为表头会被跳过，数据行从第 2 行开始），逐行匹配商品中心后返回成功/错误行——**纯解析无落库**，解析结果仍需经 `activity.create`（rules/goods 走创建草稿链路）提交，解析≠导入完成。`fileType` 为运行时文件通道参数（决定 Content-Type 与大小上限判定），非后端业务参数。
- **文件通道**：当前文件类别标识为 `fileType=excel`，覆盖 xlsx 和 csv；CSV 不填 `fileType=csv`。`file` / `fileType` 的具体传递位置以当前运行时工具的上传协议为准，不把文件部分名 `filePart` 作为业务入参。
- ⚠️ **实现口径**：`promotionSubCode` 服务端收参但**当前未消费**（解析逻辑与促销子类型无关，传任意合法值不影响结果）；文件上限后端未显式配置（按 Spring 默认 1MB 收敛，超限走管理后台）；商品匹配逐 SPU 查询商品中心，行数过多时较慢。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | 文件 | ✅ | 工作区相对文件路径（xlsx/csv；第 0 列 spuId、第 1 列 skuId；**首行为表头会被跳过，数据行从第 2 行开始**）。后端参数仅 `file` + `promotionSubCode` 两个 |
| promotionSubCode | String | ✅ | 促销子类型编码（如 SECKILL；服务端收参但未消费，如实填写即可） |

### 出参（原始数据）

- `successItems[]`：`spuId`/`skuId`（→ 创建活动商品入参）、`spuName`/`skuName`/`skuAttributes`（展示）、`originalPrice`（元，BigDecimal）
- `errorItems[]`：`rowNumber`（行号，从 1 开始不含表头）、`spuId`/`skuId`、`errorReason`（商品ID不能为空 / SKU ID不能为空 / 商品不存在 / 商品已下架 / SKU不存在）

### 调用示例

```json
{"capability":"ops.promotion.import.parse","input":{"file":"uploads/seckill-goods.xlsx","fileType":"excel","promotionSubCode":"SECKILL"},"summary":"解析秒杀活动商品清单"}
```

---

## ⛔ 未开放（本模块）

| 能力 | 原因 |
|------|------|
| 计算引擎索引/券投影重建 | 运维面操作，不属运营开放能力 |
