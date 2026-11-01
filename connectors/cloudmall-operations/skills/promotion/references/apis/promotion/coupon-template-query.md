# 促销域 — 券模板查询契约

> 概念知识：`references/domains/promotion-concepts.md`；运营流程：`references/flows/promotion-coupon.md`
> 券模板生命周期操作（stop/pause/resume/delete/logs/报表/分享）用 **templateId**（正式 ID）；审核链（create/update/submit/check）用 **pendingId**——写操作见 `coupon-template-action.md` 与 `pending-action.md`。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 能力索引（前缀 `ops.promotion.`）：查询 coupon-template.search · detail · stats · logs · share-capability
> 本文件全部能力经 `当前运行时的 Capability 查询执行器`（`mall.query`）执行。
> 分享物料生成（太阳码/短链）前先查本文件 share-capability 确认 shareAllowed。
>
> ⚠️ **ID 格式口径**：`templateId`/`promotionId` 必须使用用户明确提供或查询返回的十进制字符串 ID，保持原值，不转 Number，不补齐/截断。约 19 位只是常见外形，不能据长度断言对象不存在或必然 400；参数合法性按当前工具契约处理。非十进制标识先消歧，不猜 ID。写操作仍须读取现值并核对状态、权限与完整对象，不以 ID 能解析代替业务前置。

---

## ✅ 券模板分页搜索 — `ops.promotion.coupon-template.search`


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |
| title | String | 否 | 券名称搜索。⚠️ **字段名是 `title`**——传 keyword 会被静默忽略。传纯数字时额外按 templateId 精确匹配，**不按 promotionId 匹配**；由活动 ID 找模板时，按已知名称搜索后核对 records[].promotionId |
| promotionSubCode | String | 否 | 券类型：`MJ_COUPON`/`ZK_COUPON`/`DH_COUPON`/`MYF_COUPON` |
| promotionStatus | Integer | 否 | 状态code（1..7，4=进行中），只过滤正式模板分支。未传tab或tab=all且没有渠道筛选时，新建pending仍会并入，与活动查询不同；与生命周期tab同时传时以promotionStatus为准。按状态查询或计数推荐只传对应生命周期tab，不同时传promotionStatus |
| tab | String | 否 | 8项Tab：draft/pending/rejected查待审核表；四个生命周期Tab查正式模板；all或缺省可合并正式模板与sourceType=0的新建pending。仅all或缺省tab的有效channelCodes/excludeChannelCodes筛选会排除pending分支；draft/pending/rejected不按渠道筛选，需要时查pending.detail逐项核对渠道，不能把其total称为指定渠道的待审数量。不用虚构渠道改变统计范围。以每行dataSource/pendingId/templateId识别对象，不把all全部当正式模板 |
| checkStatus | Integer | 否 | 当前列表查询不使用此字段，传入不会筛选审核状态；按draft/pending/rejected的tab查询 |
| creatorName | String | 否 | 创建人模糊 |
| startTimeBegin / startTimeEnd | String | 否 | 活动开始时间范围（毫秒时间戳） |
| channelCodes | Integer[] | 否 | 业务领券渠道（1 自然曝光 / 2 分销），ANY 匹配 |
| excludeChannelCodes | Integer[] | 否 | 排除渠道 |
| excludeEnded | Boolean | 否 | 排除已结束 |

### 出参（分页，原始数据）

- **关键字段来源**：`records[].templateId`（正式main行 → 生命周期操作/报表/分享）、`records[].pendingId`（dataSource=pending行 → 编辑/提审/审核）、`records[].promotionId`。pending行的新建预分配标识不当作正式模板；变更草稿按sourceType区分。
- **券专属数字段（列表行）**：`totalStock`（发行量；**不限量时为 null**）/ `unlimited`（true=不限量）/ `usedStock`（扣减水位）/ `claimedCount` / `usedCount` / `maxStack` / `acquireExpireStart` / `acquireExpireEnd` / `useExpireType` / `useExpireStart` / `useExpireEnd` / `useExpireDuration`（秒）/ `description`
- **券码占用（列表行，条件返回）**：`couponCodeOccupationStatus` 恒有值，取值 `NONE`（无占用口径/不限量/无账本）/ `PENDING`（账本待确认）/ `EXACT`（精确值）；`couponCodeOccupiedCount` **仅 `EXACT` 时为数字，其余恒为 null**（即使状态是 EXACT，若计数为负也会降级为 PENDING 并置空）。不要把它当「已占用=0」使用。
- **格式与形态差异**：⚠️ 列表行的 `operationValue` / `extJson` 是 **JSON 字符串**（需二次解析），而 **detail 返回的是 JSON 对象**——两种形态不同，编辑回填请取 detail。
- **其他**：`updatedBy` / `updatedByName` / `updatedTime`（最近修改人与时间）
- **枚举/格式敏感字段**：同活动搜索（promotionStatus/promotionSubCode/dataSource/checkStatus/sourceType；startTime/endTime 毫秒时间戳、createdTime yyyy-MM-dd HH:mm:ss）。

### 券量、库存与当前可用性

| 数据 | 能说明什么 | 不能据此推断什么 |
|---|---|---|
| totalStock / unlimited | 发行配置与是否不限量，按列表/详情各自的回显规则解释 | 当前真实可领取余量；不限量不代表当前可领取 |
| claimedCount / usedCount | claimedCount为累计领取；列表usedCount只计已使用，详情usedCount包含锁定+已使用 | 当前有效券数量或某会员可用券数量；列表与详情、报表的使用数不能直接混比 |
| usedStock | 库存扣减水位 | 实时领取余量、累计领取数或当前有效券数 |
| couponCodeOccupiedCount / couponCodeOccupationStatus | 兑换码占用账本及其确认程度 | 当前可领取张数；null或PENDING不能当0 |
| coupon-code.templates.reservableStock | 该能力定义的可建批次余量 | 普通发券或会员当前可领取余量 |
| coupon.detail / coupon.library运行态字段 | 指定券实例当前可用状态及原因 | 全模板有效券总数或完整订单结算结果 |

禁止用totalStock−claimedCount或totalStock−usedStock代替实时可领余量，也不能用累计领取数代表有效券数。当前可领取还受活动/模板状态、领取窗口、渠道、会员资格、限领及真实库存影响；缺少相应证据时说明尚未核验，不承诺“还可领N张”。暂停/恢复不改变累计已领的统计含义，当前券能否使用按实例运行态核对。

- 新建pending行的totalStock是草稿回显；quantity未填且无库存池时可回退为0、unlimited=false，不代表已发行0张。先查pending.detail中的quantity及对应默认契约；不得从该0推断发行量或库存。采用默认发行量前仍按写操作约定确认。
- coupon.report.totalUsed、活动统计的券类typeSpecificCount及券模板详情usedCount包含锁定+已使用，与券模板列表usedCount不同。差值可能来自锁定券；先核对能力口径、对象范围和查询时点，不仅凭差值断言数据异常。

### 调用示例

```json
{"capability":"ops.promotion.coupon-template.search","input":{"pageNum":1,"pageSize":20,"promotionSubCode":"MJ_COUPON","tab":"in_progress"},"summary":"查询进行中的满减券模板"}
```

---

## ✅ 券模板详情 — `ops.promotion.coupon-template.detail`


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateId | String | ✅ | 券模板 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |

### 出参（原始数据）

出参是**活动详情结构的券模板扩展**（活动详情的全部字段——含 categories/brands/scopeList/audienceType 派生规则，见 activity-query.md detail 节——这里都有），另加：

| 字段 | 类型 | 说明 |
|------|------|------|
| templateId | String | 券模板 ID（→ 生命周期操作/报表/分享） |
| checkStatus / rejectReason | Integer / String | 审核状态与被驳回原因（主表口径） |
| totalStock | 数字 | 发行量（库存池 total_count） |
| usedStock | 数字 | 库存扣减水位 |
| claimedCount / usedCount | 数字 | 累计领取 / 锁定+已使用量（取自券统计表，非库存推导）；详情usedCount与列表只计已使用的口径不同 |
| maxStack | Integer | 同券最大叠加张数1..50；兑换券固定1 |
| acquireExpireStart / acquireExpireEnd | 毫秒时间戳 | 可领取时间窗 |
| useExpireType | Integer | 1 固定时段 / 2 领取后 N 秒 |
| useExpireStart / useExpireEnd / useExpireDuration | 毫秒 / 毫秒 / 秒 | 使用有效期；⚠️ `useExpireEnd` 是**算出来的**——固定时段模式下等于 `useExpireStart + useExpireDuration×1000`，不是独立存储值，改期时改 `useExpireStart` 即可 |
| couponType | Integer | 券种（1 满减 / 2 折扣 / 3 兑换 / 4 运费） |
| personalLimit / personDailyLimit | Integer | 每人总限领 / 每人每日限领（0=不限）——**详情直接返回**，无需回 pending 快照 |
| limitRules[] | 数组 | 限领规则明细 `{limitKey, limitValue}`；`limitKey` 取值 `PERSONAL`/`DAILY`/`PERSON_DAILY` |
| channelCodes | Integer[] | 业务领券渠道（1 自然曝光 / 2 分销） |

- ⚠️ **不限量语义与列表行不同**：详情**没有 `unlimited` 字段**，`totalStock` 一律取库存池实际值（不区分是否不限量）；**列表行**才是不限量时 `totalStock=null` 且 `unlimited=true`。判断券是否不限量请以**搜索列表行**为准。
- ⚠️ 详情的 `goodsList` **恒为空数组**——券的适用商品同样走 `activity.goods-search` / `goods-all`（传 templateId 会反查到活动）。
- **关键字段来源**：`promotionId`、`templateId`；**枚举字段**：`promotionSubCode`/`promotionStatus`/`channelCodes`/`couponType`/`useExpireType`；**格式敏感字段**：startTime/endTime/acquireExpire*/useExpire* 毫秒时间戳、createdTime yyyy-MM-dd HH:mm:ss。

### 调用示例

```json
{"capability":"ops.promotion.coupon-template.detail","input":{"templateId":"4300000000000000001"},"summary":"查看满减券模板配置"}
```

---

## ✅ 券模板统计 — `ops.promotion.coupon-template.stats`


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| promotionSubCode | String | 否 | 券类型；**不传聚合全部券种**（与活动统计的必填不同） |

### 出参（原始数据）

- 字段包括totalCount/activeCount/issuedCount/typeSpecificCount/typeSpecificLabel/statusCounts八态Map，但口径不完全等同活动统计：totalCount取statusCounts.all，包含sourceType=0的新建pending；其他通用统计主要来自主表，空字段不能按0解释。
- `statusCounts` 各项按各Tab独立查询；草稿/待审/驳回来自pending口径，未开始/进行中/暂停/结束来自正式资源口径，all采用前述包含新建pending的口径。它们**不保证互斥，也不保证各项都包含在all中**。各子项不可相加推算all，all缺失时也不由子项相加补出；子项之和与all不一致，不据此断言数据异常。
- 展示时将 `totalCount/statusCounts.all` 单列为“全部Tab可见资源数”，各子项按“Tab/数量”列示，**不能把all标成各子项的合计、不凑100%、不以all为分母算各Tab占比、不据差额补“其他”**。这些计数不足以给出跨Tab去重合计；用户确需去重结果时，说明需要按资源标识另行查询，不能拿现有计数推算。

### 调用示例

```json
{"capability":"ops.promotion.coupon-template.stats","input":{"promotionSubCode":"MJ_COUPON"},"summary":"统计满减券模板各状态数量"}
```

---

## ✅ 券模板操作日志 — `ops.promotion.coupon-template.logs`


### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateId | String | ✅ | 券模板 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |
| pageNum | Integer | 否 | ≥1，默认 1 |
| pageSize | Integer | 否 | 1..100，默认 20 |

### 出参（分页，原始数据）

- 同活动日志（operationType 枚举；operatedAt 毫秒时间戳）。

### 调用示例

```json
{"capability":"ops.promotion.coupon-template.logs","input":{"templateId":"4300000000000000001","pageNum":1,"pageSize":20},"summary":"查看券模板操作日志"}
```

---

## ✅ 分享能力查询 — `ops.promotion.coupon-template.share-capability`

- 生成物料前的只读预检

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| templateId | String | ✅ | 券模板 ID（字符串雪花 ID，约 19 位纯数字；非纯数字格式必 400） |

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| shareAllowed | 是否可分享（分销券恒 false，其余恒 true） |
| disabledReason | 禁止原因——⚠️ **仅分销券有值**（固定文案「分销券不支持生成通用推广物料」），非分销券**恒为 null** |
| pagePath | 分享页面路径——⚠️ **分销券为 null**，仅非分销券返回 |
| runtimeStatus | 运行状态（两种情况都有值） |
| warning | 警告——⚠️ **仅非分销券可能非空**，分销券**恒为 null** |

### 调用示例

```json
{"capability":"ops.promotion.coupon-template.share-capability","input":{"templateId":"4300000000000000001"},"summary":"查询券是否可生成分享物料"}
```

---

## ⛔ 未开放（本模块）

| 能力 | 原因 |
|------|------|
| 券订单明细导出链路（导出任务创建/列表/取消/下载） | 创建/下载端点要求调用方额外携带端侧操作权限标识参与券种鉴权（能力链不提供该入参 → 必然 400）；下载本身为 URL 型，待后端改造后评估 |
| 券模板领用记录（claim-records） | 端点要求调用方额外携带端侧操作权限标识参与券种鉴权（能力链不提供该入参 → 必然 400），待后端改造后评估 |
