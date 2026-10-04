---
name: leads-cloud-crm
description: 询盘云 CRM 只读查询技能 - 分页查询线索、客户、联系人、商机、触点联系人、SKU、订单、订单明细，按对象查跟进记录与互动时间线，按触点值或对象查画像，查询 WhatsApp 会话与消息
version: "1.0.0"
author: "Leads Cloud"
---

# 询盘云 CRM Skill

本 Skill 通过已配置的 Leads Cloud MCP（`https://mcp.leadscloud.com/mcp`，Streamable HTTP）查询询盘云 CRM 与 WhatsApp 数据。全部 12 个 Tool 均为只读；服务端按 PAT 实时向 CRM 认证，并固定租户、组织、用户、对象、数据域和权限。若在线 Tool Schema 与本文不一致，以在线 Schema 为准。

## 认证与安全

- WorkBuddy 在本机保存用户填写的 PAT，并在每次请求注入 `Authorization: Bearer <PAT>`；PAT 由用户在 CRM「个人设置 → MCP Token」创建。
- Token 失效、被禁用或权限不足时，提示用户到 CRM 重新创建 Token 或在 WorkBuddy 中更新配置；不要向用户索要 PAT 明文。
- 禁止把 PAT、Authorization Header、Token、密码写入对话、报告、示例或 Tool 参数。
- 禁止在 Tool 参数中传入 `tenantId`、`orgId`、CRM 调用方 `userId`、`objApiKey`、数据域、下游 URL 或数据库信息；所有 Tool Schema 均为 `additionalProperties=false`，多余字段会被拒绝。
- 每个 Tool 对应一个 CRM 权限码，由 CRM 实时判定；缺少权限时 Tool 返回拒绝，而不是空结果。

| Tool | 数据域 | 权限码 |
|------|--------|--------|
| crm_query_leads | 公海 lead | `crm.lead.read` |
| crm_query_customers | 公海 customer | `crm.customer.read` |
| crm_query_contacts | 私海 contact | `crm.contact.read` |
| crm_query_opportunities | 私海 opportunity | `crm.opportunity.read` |
| crm_query_touchpoint_contacts | 私海 touchPointContact | `crm.touchpoint-contact.read` |
| crm_query_touchpoint_profiles | 私海 touchPointContact | `crm.touchpoint-contact.read` |
| crm_query_skus | 私海 stockKeepingUnit | `crm.sku.read` |
| crm_query_orders | 私海 order | `crm.order.read` |
| crm_query_order_items | 私海 orderProduct | `crm.order-item.read` |
| crm_query_follow_up_records | 私海 followUpRecord | `crm.follow-up.read` |
| customer_development_query_whatsapp_conversations | WhatsApp 会话 | `customer-development.communication.read` |
| customer_development_query_whatsapp_messages | WhatsApp 消息 | `customer-development.communication.read`；`includeContent=true` 时额外需要 `customer-development.communication.content.read` |

## 通用约定

- 分页：默认 `offset=0`、`size=20`；`size` 范围 1~100，下一页使用 `offset + size`。实际条数以返回列表长度为准，`total` 是授权范围内的总数。
- 时间字段：原时间字段保持 CRM 原始格式与精度；服务端附加 `<原字段名>Display` 仅供展示（日期 `yyyy-MM-dd`，日期时间 `yyyy-MM-dd HH:mm:ss`，默认 GMT+8）。筛选、排序、分页和下钻一律使用原字段，不能使用 `Display` 字段。
- 关系字段：各 Tool 声明的关系字段（如 `owner`、`ownerId`、`dimDepart`、`customer`、`order`）会投影为稳定的 `{dataId, name}` 对象；CRM 内部 `auto_column_*` 和 `*_valueResourceKey` 字段不会返回。
- 下钻参数只能来自同一任务中前序真实 Tool 输出；不要编造 `dataId`、触点值、成员 ID、账号或会话 ID。
- 只调用回答当前问题所需的最少 Tool；不要为得到非空结果而扩大范围、切换身份或放宽条件。

## 通用错误处理

| 场景 | 表现 | 处理 |
|------|------|------|
| 参数错误 | 参数校验/Schema 错误消息 | 按在线 Schema 修正一次后重试；不要反复重放相同请求，也不要补身份字段。参数错误不表示没有数据 |
| 认证失败 | HTTP 401 Problem Details（`MCP Bearer 凭据缺失或无效`） | 提示用户检查或重建 PAT；不要索要凭证 |
| 鉴权依赖故障 | HTTP 503 Problem Details（`CRM 鉴权服务暂时不可用`） | 稍后重试一次；持续失败时如实报告服务不可用 |
| 权限或范围拒绝 | 拒绝类错误（ACCESS_DENIED） | 说明缺少的权限码或对象不可见，请用户使用已授权账号；不要换参数绕过 |
| 请求额度耗尽 | `MCP 请求额度已耗尽…reason=organization-daily` 或 `user-daily` | 告知用户组织或个人日额度已用完，等待窗口恢复；不要循环重试 |
| 空结果 | 成功返回且 `total=0` / 空列表 | 这是当前授权范围内的有效结果；不要推断全系统无数据 |
| CRM metadata、布局、下游错误 | 带 CRM 错误码/消息 | 保留 Tool 名、安全输入和精确错误信息报告；不要绕过 MCP 直接查库或调下游 |

缺失字段、显式 `null`、空数组和调用失败是四种不同结果，不要互相混淆或补造字段。

## 标准 CRM 列表参数

以下 8 个 Tool 共用同一套输入 Schema：`crm_query_leads`、`crm_query_customers`、`crm_query_contacts`、`crm_query_opportunities`、`crm_query_touchpoint_contacts`、`crm_query_skus`、`crm_query_orders`、`crm_query_order_items`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| offset | integer | - | 从 0 开始的记录偏移量，默认 0 |
| size | integer | - | 每页数量，1~100，默认 20 |
| filters | object[] | - | 最多 10 个筛选条件，默认 `[]`；每项 `{field, operator, values?}` |
| sort | object | - | 单字段排序 `{field, direction}`，`direction` 为 `asc`/`desc`，两者必填；同值记录无隐含第二排序 |

`filters` 项字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| field | string | ✅ | 当前固定 CRM 对象在线 metadata 声明的字段 apiKey，`^[A-Za-z_][A-Za-z0-9_]*$`，最长 128；`dataId` 自动映射到 CRM 原生 id |
| operator | string | ✅ | `eq`、`contains`、`not_contains`、`lt`、`lte`、`gt`、`gte`、`ne`、`in`、`not_in`、`between`、`is_null`、`not_null` |
| values | (string\|number\|boolean)[] | 条件 | 最多 100 个标量，每项序列化后最长 1024 字符，禁止 `null` |

值规则：

- `eq`、`contains`、`not_contains`、`lt`、`lte`、`gt`、`gte`、`ne`、`in`、`not_in` 至少一个值；`between` 恰好两个边界值；`is_null`、`not_null` 省略 `values` 或传空数组。
- 关系字段用正整数 `dataId`；布尔字段推荐 `true`/`false`（兼容 `0`/`1`）。
- 日期用 `yyyy-MM-dd`；日期时间必须含时间，如 `2026-09-01T00:00:00` 或 `2026-09-01 00:00:00`，小数秒可选。
- 不能用 `Display` 字段筛选或排序；禁止筛选凭证、密码、Token、MCP、租户 Header 类字段。

标准列表返回结构：

```json
{
  "data": {
    "offset": 0,
    "size": 20,
    "total": 1,
    "list": [
      {
        "dataId": 123,
        "name": "Example",
        "ownerId": {"dataId": 1001, "name": "张三"},
        "createdTime": "2026-09-01 10:20:30",
        "createdTimeDisplay": "2026-09-01 10:20:30"
      }
    ]
  }
}
```

## 可用工具

### crm_query_leads - 查询公海线索

分页查询当前 CRM 用户有权查看的公海线索。

**参数**：标准 CRM 列表参数。

**返回**：标准列表结构；行内含 `dataId` 与当前租户布局授权的线索字段，`owner`、`ownerId`、`dimDepart`、`createdUser`、`updatedUser`、`infoUpdatedUser`、`objectType`、`sourceType` 投影为 `{dataId, name}`。

**使用示例**：

- 最近创建的线索：

```json
{"offset": 0, "size": 20, "sort": {"field": "createdTime", "direction": "desc"}}
```

- 按名称搜索：`{"filters": [{"field": "name", "operator": "contains", "values": ["Acme"]}]}`
- 下钻跟进：复用实际返回行的 `dataId`，调用 `crm_query_follow_up_records`，`objectType=lead`、`publicPool=true`。

### crm_query_customers - 查询公海客户

分页查询当前 CRM 用户有权查看的公海客户。

**参数**：标准 CRM 列表参数。

**返回**：标准列表结构；关系字段投影与线索相同（`owner`、`ownerId`、`dimDepart`、`createdUser`、`updatedUser`、`infoUpdatedUser`、`objectType`、`sourceType`）。

**使用示例**：

- 第一页客户：`{"offset": 0, "size": 20}`
- 按创建时间区间：`{"filters": [{"field": "createdTime", "operator": "between", "values": ["2026-09-01 00:00:00", "2026-09-30 23:59:59"]}]}`
- 下钻跟进：将实际 `dataId` 传给 `crm_query_follow_up_records`，`objectType=customer`、`publicPool=true`；下钻画像：传给 `crm_query_touchpoint_profiles` 的 `objectRefs`，`publicPool=true`。

### crm_query_contacts - 查询联系人

分页查询当前 CRM 用户有权查看的私海联系人。

**参数**：标准 CRM 列表参数。

**返回**：标准列表结构；`customer`、`owner`、`ownerId`、`dimDepart`、`position`、`country`、`gender`、`religion`、`createdUser`、`updatedUser`、`infoUpdatedUser`、`objectType` 投影为 `{dataId, name}`。

**使用示例**：

- 某客户下的联系人：`{"filters": [{"field": "customer", "operator": "eq", "values": [123]}]}`（`123` 为 `crm_query_customers` 实际返回的 `dataId`）。
- 下钻画像：将联系人 `dataId` 传入 `crm_query_touchpoint_profiles` 的 `objectRefs`，`objectType=contact`、`publicPool=false`。

### crm_query_opportunities - 查询商机

分页查询当前 CRM 用户有权查看的私海商机。

**参数**：标准 CRM 列表参数。

**返回**：标准列表结构；`customer`、`owner`、`ownerId`、`dimDepart`、`saleStageId`、`createdUser`、`updatedUser`、`infoUpdatedUser`、`objectType` 投影为 `{dataId, name}`。

**使用示例**：

- 第一页商机：`{"offset": 0, "size": 20}`
- 按阶段筛选：使用在线 metadata 中的阶段字段（如 `saleStageId`）与阶段 `dataId` 做 `eq`/`in`。
- 下钻跟进：复制实际 `dataId`，调用 `crm_query_follow_up_records`，`objectType=opportunity`、`publicPool=false`（商机只能为 `false`）。

### crm_query_touchpoint_contacts - 查询触点联系人

分页查询当前 CRM 用户有权查看的归档触点联系人（邮箱、手机、WhatsApp 等触点与其关联业务对象）。

**参数**：标准 CRM 列表参数。

**返回**：标准列表结构；`ownerId`、`dimDepart`、`objectType`、`touchPoint`、`sourceType`、`archiveStatus`、`position`、`country`、`gender`、`religion`、`infoUpdatedUser`、`updatedUser` 投影为 `{dataId, name}`。

**使用示例**：

- 第一页：`{"offset": 0, "size": 20}`
- 返回行中的精确触点值（邮箱、手机号、WhatsApp 账号）可传给 `crm_query_touchpoint_profiles` 的 `targetValues`。

### crm_query_skus - 查询 SKU

分页查询当前 CRM 用户有权查看的私海 SKU（`stockKeepingUnit`）。

**参数**：标准 CRM 列表参数。

**返回**：标准列表结构；`catalog`、`standardProductUnit`、`unit`、`priceUnitCurrency`、`ownerId`、`dimDepart`、`createdUser`、`updatedUser`、`infoUpdatedUser`、`objectType` 投影为 `{dataId, name}`。

**使用示例**：

- 从订单明细拿到 `stockKeepingUnit.dataId` 后精确查询：`{"filters": [{"field": "dataId", "operator": "eq", "values": [456]}]}`
- `skuNumber` 是产品编号，不是 `dataId`；两者不能互相替代。

### crm_query_orders - 查询订单

分页查询当前 CRM 用户有权查看的私海订单头。

**参数**：标准 CRM 列表参数。

**返回**：标准列表结构；`customer`、`opportunity`、`quotation`、`shipToContact`、`ownerId`、`dimDepart`、`modeOfPayment`、`shippingCountry`、`createdUser`、`updatedUser`、`infoUpdatedUser`、`objectType` 投影为 `{dataId, name}`。

**使用示例**：

- 最近订单：`{"sort": {"field": "createdTime", "direction": "desc"}}`
- 某客户订单：`{"filters": [{"field": "customer", "operator": "eq", "values": [123]}]}`
- 复制实际订单 `dataId`，再调用 `crm_query_order_items` 查明细。

### crm_query_order_items - 查询订单商品明细

分页查询父订单在当前用户范围内的订单商品行（`orderProduct`）；父订单可见范围由服务端验证后编码为 `order` 关系条件。

**参数**：标准 CRM 列表参数。

**返回**：标准列表结构；`order`、`stockKeepingUnit`、`catalog`、`unit`、`priceList`、`priceListRecord`、`ownerId`、`dimDepart`、`createdUser`、`updatedUser`、`infoUpdatedUser`、`objectType` 投影为 `{dataId, name}`；`skuNumber`、`skuState` 为 SKU 引用映射值，未解析时为 `null`。

**使用示例**：

```json
{
  "filters": [{"field": "order", "operator": "eq", "values": [789]}],
  "offset": 0,
  "size": 20
}
```

- `789` 必须是 `crm_query_orders` 实际返回的 `dataId`。
- 查询关联 SKU 使用行内 `stockKeepingUnit.dataId`；`skuNumber`/`skuState` 为 `null` 只表示引用值未解析，不代表 SKU 关联缺失，也不能用明细 ID 代替产品编号。

### crm_query_follow_up_records - 查询跟进记录或互动时间线

查询一个可见线索、客户或商机的原生跟进记录（`source=native`）或互动时间线（`source=timeline`）。服务端先验证来源记录可见，再查询。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| objectType | string | ✅ | `lead`、`customer`、`opportunity`；必须与 `dataId` 的前序查询一致 |
| dataId | integer | ✅ | 来源对象的正整数 `dataId`，不是跟进记录 ID |
| source | string | - | `native`（默认）原生跟进记录；`timeline` WhatsApp、邮件、业务操作等互动时间线 |
| publicPool | boolean | - | 来源对象是否来自公海，默认 `false`；`opportunity` 只能为 `false` |
| offset | integer | - | 从 0 开始，默认 0 |
| size | integer | - | 1~100，默认 20 |

**返回**：

- 公共字段：`objectType`、`dataId`、`publicPool`、`source`、`offset`、`size`、`total`、`records`、`countMeaning`。
- `source=native`：`records` 为原生跟进记录，`objectType`、`ownerId`、`dimDepart`、`followUpObject`、`createdUser`、`updatedUser`、`infoUpdatedUser` 投影为 `{dataId, name}`。
- `source=timeline`：额外返回 `hasMore`、`contentIncluded=false`，以及来源记录存在时的 `followUpCount`。每条事件含 `id`、`eventId`、`eventType`、`eventTypeName`、`eventAction`、`eventActionName`、`eventTime`、`gmtCreate`、`gmtModified`（各带 `Display`）、`userId`、`userName`、`fromSourceType`、`hasAttachment`、`hasDetail`、`eventCallType`、`contentRedacted=true`；不返回消息正文、摘要、媒体或评论。

**使用示例**：

- 原生跟进：

```json
{"objectType": "customer", "dataId": 123, "publicPool": true, "offset": 0, "size": 20}
```

- 互动时间线：

```json
{"source": "timeline", "objectType": "opportunity", "dataId": 456, "publicPool": false}
```

**注意**：父记录的 `followUpCount` 是 CRM 规则累计值，不等于任一来源的 `total`，不要强行对齐；原生记录为空但需要了解互动过程时改用 `timeline`；需要 WhatsApp 正文时走 `customer_development_query_whatsapp_messages` 的内容权限。

### crm_query_touchpoint_profiles - 查询触点画像

按精确触点值，或按可见 CRM 对象引用解析其触点后，查询触点画像。本 Tool 不分页。

**参数**（两种模式互斥，必须且只能选一种）：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| targetType | string | 精确值模式 ✅ | `whatsapp`、`whatsapp_group`、`phone`、`email`、`wecom`、`wecom_group`、`facebook`、`facebook_form`、`instagram`、`web_visitor` |
| targetValues | string[] | 精确值模式 ✅ | 1~100 个去重非空值，每项最长 512 字符 |
| objectRefs | object[] | 对象引用模式 ✅ | 1~20 个去重引用 `{objectType, dataId, publicPool}` |

`objectRefs` 项字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| objectType | string | ✅ | `lead`、`customer`、`contact` |
| dataId | integer | ✅ | 前序查询实际返回的正整数 `dataId` |
| publicPool | boolean | ✅ | 线索/客户按其来源填写；联系人固定 `false` |

**返回**：

- 精确值模式：`targetType`、`requestedValues`、`total`、`profiles`。
- 对象引用模式：`objectRefs`、`resolvedTouchpoints`（每项含 `objectType`、`dataId`、`publicPool`、`targetType`、`targetValue`）、`total`、`profiles`。
- `profiles` 每项含 `targetValue`（对象引用模式还含 `targetType`）及 `status`、`statusDesc`、`touchPointContactId`、`touchPointContactName`、`customerId`、`companyName`、`shortName`、`leadId`、`leadName`、`contactId`、`objectId`、`objectTypeId`、`contactNo`、`encryptFlag`、`nickName`、`contactsName`、`rightUsers`、`saleIds`、`saleId`、`saleNames`、`hasRight`、`waManageIsWaGroup` 中存在的字段。

**使用示例**：

- 精确值模式：

```json
{"targetType": "email", "targetValues": ["buyer@example.com"]}
```

- 对象引用模式：

```json
{"objectRefs": [{"objectType": "customer", "dataId": 123, "publicPool": true}]}
```

**注意**：`resolvedTouchpoints` 非空不代表一定有画像，可见对象可能有触点值但没有归档画像；同时传入 `targetType`/`targetValues` 和 `objectRefs` 会被 Schema 拒绝。

### customer_development_query_whatsapp_conversations - 查询 WhatsApp 会话

查询当前 PAT 与 CRM 实时权限交集内有效成员的 WhatsApp 会话；省略 `memberUserId` 时服务端枚举全部有效成员并逐成员解析真实绑定账号。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| memberUserId | integer | - | 只能把范围收窄到一个 CRM 有效正式成员；首次发现会话时应省略 |
| keyword | string | - | 会话名称或账号模糊关键词，最长 256 字符 |
| offset | integer | - | 跨账号结果偏移量，从 0 开始，默认 0 |
| size | integer | - | 1~100，默认 20 |

**返回**：`memberUserId`（传入时回显）、`effectiveMemberCount`、`queriedMemberCount`、`accounts`、`routes`（`{memberUserId, userBindWaAccount}` 列表）、`complete`、`unsupportedShadowMemberUserIds`、`unboundMemberUserIds`、`offset`、`size`、`total`、`conversations`。每条会话含 `id`、`memberUserId`、`userBindWaAccount`、`chatWaAccount`、`conversationType`（`private`/`group`）、`chatWaName`、`chatWaAvatar`、`unreadCount`、`lastMessageTimeStamp`（含 `Display`）、`lastMessageFromMe`、`lastChatType`、`archive`、`shield`、`chatTop`、`chatPinTime`（含 `Display`）、`lid`、`username`、`countryName`、`countryCode`、`remark`、`contentRedacted`；不返回会话预览正文。

**使用示例**：

- 首次发现会话：

```json
{"offset": 0, "size": 20}
```

- 按关键词收窄：`{"keyword": "Acme", "size": 50}`

**注意**：

- `complete=false` 表示存在 Shadow 成员未覆盖（列于 `unsupportedShadowMemberUserIds`），需在回答中说明范围不完整；`unboundMemberUserIds` 是未绑定 WhatsApp 的有效成员。
- 消息下钻时完整复制所选行的 `memberUserId + userBindWaAccount + chatWaAccount`；账号展示打码或同号多会话时，同时复制该行 `id` 作为 `conversationId`，不能把显示相同打码号码的不同会话混用。

### customer_development_query_whatsapp_messages - 查询 WhatsApp 消息

按会话列表返回的成员、绑定账号和对方账号查询消息；调用前服务端重新验证 CRM 成员、真实账号和会话存在性。默认只返回消息元数据。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| memberUserId | integer | ✅ | 会话行返回的 CRM 正式成员 ID |
| userBindWaAccount | string | ✅ | 会话行返回的真实绑定账号，1~256 字符 |
| chatWaAccount | string | ✅ | 会话行返回的客户或群组账号，1~256 字符；须与所选行原始账号或当前展示账号一致 |
| conversationId | integer | - | 所选会话行 `id`；打码账号或同号多会话时必须传入，服务端按其获取密文账号查询 |
| offset | integer | - | 从 0 开始，默认 0 |
| size | integer | - | 1~100，默认 20 |
| startTimeStamp | integer \| string | - | 非负 64 位 Unix 毫秒时间戳，接受整数或纯数字字符串（最长 19 位）；使用原始 `timeStamp`，不要传秒、日期文本或 `Display` |
| endTimeStamp | integer \| string | - | 同上；起始时间不能晚于结束时间。按日查询时按用户指定时区（默认 GMT+8）计算边界 |
| includeContent | boolean | - | 是否返回正文与媒体字段，默认 `false`；`true` 时需要 `customer-development.communication.content.read` 权限 |

**返回**：`memberUserId`、`userBindWaAccount`、`chatWaAccount`、`conversationId`（传入时回显）、`offset`、`size`、`total`、`contentIncluded`、`messages`。每条消息含 `id`、`userId`、`userBindWaAccount`、`fromWaAccount`、`toWaAccount`、`messageId`、`fromMe`、`type`、`timeStamp`、`createTime`、`updateTime`（时间字段含 `Display`）、`readFlag`、`deleteFlag`、`participant`、`readFlagSync`、`contentRedacted`；`includeContent=true` 且有权限时额外返回 `content`、`contentUrl`、`contentThumbnail`、`contentQiniuUrl`、`contentQiniuUrlUpdateTime`、`mediaKey`、`extendedJson`、`fileLength`。

**使用示例**：

- 元数据查询（先通过会话 Tool 获得实际行）：

```json
{
  "memberUserId": 10001,
  "userBindWaAccount": "actual-binding-account",
  "chatWaAccount": "actual-chat-account",
  "conversationId": 123,
  "offset": 0,
  "size": 20,
  "includeContent": false
}
```

- 某日消息正文：保持账号三元组与 `conversationId` 不变，增加 `startTimeStamp`/`endTimeStamp`（当日 GMT+8 零点至次日零点的毫秒值）并将 `includeContent` 改为 `true`。

**注意**：

- `contentRedacted=true` 表示消息存在正文/媒体但因未请求或无权限被移除；`contentIncluded` 回显本次是否请求正文。
- 消息行 `userId` 不是当前用户查看权限的判断条件；`timeStamp` 是消息时间，`createTime` 是记录创建时间，两者可能不同，不要强制对齐。
- Shadow 成员路由当前被拒绝；禁止把 Shadow 用户、虚拟号码或行 `id` 当作 `memberUserId`，禁止复用其他会话的账号对。

## 注意事项

- 本 Connector 仅有查询能力，没有创建、更新、删除或发送消息能力。
- WhatsApp 消息默认先查元数据；只有用户明确需要正文或媒体且当前 PAT 有内容权限时才设置 `includeContent=true`。
- 权限范围内没有数据时如实报告空结果和范围（含 `complete=false`、`unboundMemberUserIds` 等范围提示）。
- 回答先给业务结论，再说明关键 Tool、筛选条件、分页覆盖和授权范围；严格区分返回事实与推断。
