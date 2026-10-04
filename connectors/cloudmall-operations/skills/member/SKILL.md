---
name: member
display_name: 云MALL会员
display_name_en: CloudMall Members
description: 云MALL会员域查询。当用户要求查会员、按手机号/昵称/会员号/uid 找会员、查会员列表、会员注册时间、会员详情时使用。
description_zh: 查询当前授权租户的云MALL会员：会员列表、多条件检索、会员详情。
description_en: Query CloudMall members for the authorized tenant: member list, multi-condition search, and member details.
allowed-tools: cloudmall_query
version: 0.1.0
author: 云MALL
---

# 云MALL会员域

以当前运营账号的实时接口权限与数据权限，查询云MALL会员数据。第一期提供会员分页查询与会员详情两项能力，本 Skill 随域内能力扩展持续更新。

## 域内能力与参数

### ops.member.member.search — 会员分页查询

| 参数 | 必填 | 说明 |
|---|---|---|
| pageNum / pageSize | 是 | 分页参数；pageSize 上限 100，默认建议 20 |
| nickname | 否 | 昵称 |
| memberNo | 否 | 会员号 |
| uid | 否 | 会员 uid，十进制字符串 |
| phone | 否 | 手机号（1 开头 11 位） |
| source | 否 | 注册来源 |
| registerTimeStart / registerTimeEnd | 否 | 注册时间范围，格式 yyyy-MM-dd HH:mm:ss |
| status | 否 | 会员状态（数字 0~3） |
| sortField | 否 | 排序字段：register_time / last_consume_time |
| sortOrder | 否 | 排序方向：ASC / DESC |

### ops.member.member.detail — 会员详情

| 参数 | 必填 | 说明 |
|---|---|---|
| id | 是 | 会员 ID，正数十进制字符串 |

## 调用流程（固定）

1. 手机号查询：search 携带 phone → 唯一命中 → 用返回的 id 调 detail；多命中 → 先向用户确认目标会员。
2. memberNo 与 uid 是两个不同字段：用户只给「编号」时，先确认是会员号（memberNo）还是 uid（较长的一串数字），存在歧义必须先追问，不要猜测。
3. 昵称等模糊条件多命中时，先向用户确认目标会员再继续。

## 调用示例

```json
{"capability": "ops.member.member.search", "input": {"pageNum": 1, "pageSize": 20, "phone": "13800000001"}, "summary": "按手机号查询会员"}
```

```json
{"capability": "ops.member.member.detail", "input": {"id": "900000000000000001"}, "summary": "查询会员详情"}
```

## 输出

统一成功结构 `{ capability, data, traceId, truncated }`。search 的 data 为分页对象（records/total/pageNum/pageSize/totalPages/hasMore）；detail 为单个会员对象。字段以服务端 allowlist 为准：列表含 id/nickname/memberNo/uid/phone/sourceText/registerTime/lastConsumeTime/statusText/levelName 等，详情另含 gender/birthday/pointsBalance/growthValue（头像等媒体字段不开放）。phone 是后端脱敏展示字段，不得尝试还原或追问完整号码。

## 翻页与 truncated

truncated=true 表示响应预算触发精确重定位：MCP 已按原 offset 返回较小完整页。必须改用 truncation 中的 effectivePageNum/effectivePageSize/nextPageNum 继续翻页，不能沿用原 pageNum/pageSize。

## 错误恢复

- AUTH_REQUIRED：授权已失效，提示用户在 WorkBuddy 重新连接，不要求粘贴任何 Token。
- PERMISSION_DENIED：当前账号没有该接口权限，向用户说明后停止，不尝试其他权限码或接口。
- INPUT_INVALID：按参数表检查字段与枚举（例如 phone 必须 1 开头 11 位；status 是数字不是字符串），修正后重试。
- UPSTREAM_TIMEOUT：稍后重试，并缩小查询范围（补充 phone/memberNo 等条件或减小 pageSize）。

## 禁止事项与边界

- 不得询问或传入租户、账号、Token、接口路径、权限码等身份/路由信息；身份由连接授权自动绑定。
- Snowflake ID（uid/id）一律按十进制字符串处理，禁止转成数字。
- 第一期本域仅开放只读查询：物流、售后、报表及任何写操作（调整积分、变更等级、禁用会员等）均不支持。用户提出时明确说明不支持，不得尝试绕过。
