# 营销域 — 导购推广素材（业务素材 / 内容素材 / 素材分组）写操作契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-content-flow.md`
> 三类对象：**业务素材**（对优惠券/促销活动/页面/游戏/直播/种草等既有业务对象的引用，控制其在导购工作台的展示）、**内容素材**（运营原创图文/视频内容，带发布生命周期与传播统计）、**素材分组**（content_material 与 speech 各自独立的两级分组树）。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `guide-material-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：guide-material.business-batch-add 批量添加业务素材 🟡 · guide-material.business-toggle-display 切换业务素材显示 🟡 · guide-material.business-batch-remove 批量移除业务素材 🔴 · guide-material.business-toggle-top 业务素材置顶切换 🟡 · guide-material.content-create 创建内容素材 🟡 · guide-material.content-update 更新内容素材 🟡 · guide-material.content-publish 发布内容素材 🔴 · guide-material.content-unpublish 取消发布内容素材 🔴 · guide-material.content-delete 删除内容素材 🔴 · guide-material.content-toggle-top 内容素材置顶切换 🟡 · guide-material-group.create 创建素材分组 🟡 · guide-material-group.update 更新素材分组 🟡 · guide-material-group.delete 删除素材分组 🔴

---

## ✅ 批量添加业务素材 — `ops.marketing.guide-material.business-batch-add`

- **风险**：🟡 可逆写（可移除）
- **前置**：materialType 必填；items 非空。同类型+同 sourceId 已存在时**自动跳过**（不报错）；新增默认「显示+有效」。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| materialType | String | ✅ | coupon/promotion/page/game/live/grass |
| items | Array | ✅ | 素材来源项列表 |
| items[].sourceId | String | ✅ | 关联源业务对象 ID（如券模板 ID） |
| items[].title | String | 否 | 冗余标题（列表会按类型实时回源覆盖） |

### 出参（原始数据）

无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.guide-material.business-batch-add","input":{"materialType":"coupon","items":[{"sourceId":"4300000000000000001","title":"满100减20券"}]},"summary":"把满减券加入导购业务素材库"}
```

---

## ✅ 切换业务素材显示状态 — `ops.marketing.guide-material.business-toggle-display`

- **风险**：🟡 可逆写（隐藏/显示互切）
- **前置**：素材存在；displayStatus 为目标状态（true=显示，false=隐藏）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 业务素材 ID |
| displayStatus | Boolean | 否 | true=显示 / false=隐藏；缺省按 false 处理 |

### 出参（原始数据）

无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.guide-material.business-toggle-display","input":{"id":"5600000000000000001","displayStatus":true},"summary":"恢复该业务素材在导购端展示"}
```

---

## ✅ 批量移除业务素材 — `ops.marketing.guide-material.business-batch-remove`

- **风险**：🔴 不可逆（物理删除）
- **前置**：materialIds 非空；逐条删除，不存在 ID 不报错。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| materialIds | String[] | ✅ | 业务素材 ID 列表（来自列表 records[].id） |

### 出参（原始数据）

无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.guide-material.business-batch-remove","input":{"materialIds":["5600000000000000001","5600000000000000002"]},"summary":"批量移除两条过期业务素材"}
```

---

## ✅ 业务素材置顶/取消置顶 — `ops.marketing.guide-material.business-toggle-top`

- **风险**：🟡 可逆写（再调一次即反转）
- **前置**：素材存在。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 业务素材 ID |

### 出参（原始数据）

无业务数据；当前置顶态以列表 isTop 回读为准。

### 调用示例

```json
{"capability":"ops.marketing.guide-material.business-toggle-top","input":{"id":"5600000000000000001"},"summary":"置顶该业务素材"}
```

---

## ✅ 创建内容素材 — `ops.marketing.guide-material.content-create`

- **风险**：🟡 可逆写（草稿态，未发布不对导购端可见）
- **前置**：title ≤100 字必填；contentType 必填；copyText ≤5000 字；attachment 必填（type 必填）；scope 必填；publishTimeType 必填（scheduled 时建议提供 publishStartTime）。创建后为 draft 状态，需另行调用发布。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | String | ✅ | 标题，≤100 字 |
| contentType | String | ✅ | image/poster/video/image_poster/custom |
| copyText | String | 否 | 文案，≤5000 字 |
| attachment | Object | ✅ | 附件（见下方展开） |
| relatedContent | Object | 否 | 关联内容：`product`（`{scope, goodsList}`，goodsList 为 `{spuId, skuList: [{skuId}]}`）/`coupon`/`promotion`/`page`/`contentMaterial`（各 `{scope, ids}`）——**注意与推广任务不同，这里没有 contentType 外层字段** |
| groupId | String | 否 | 分组 ID（bizType=content_material 的分组） |
| scope | Object | ✅ | 适用范围 `{userTag/user/store/guide: {type: all\|specified, ids}}` |
| publishTimeType | String | ✅ | permanent（永久）/scheduled（定时） |
| publishStartTime / publishEndTime | String | 否 | scheduled 时传，yyyy-MM-dd HH:mm:ss |

**attachment 附件展开**：

| 字段 | 类型 | 说明 |
|------|------|------|
| type | String | ✅ image/poster/video/image_poster/custom |
| images | Array | 图片列表：`{url, width, height}`（image/image_poster 用，最多 9 张） |
| posters | Array | 海报列表：`{templateId, params}`（poster 用；params 为模板参数键值对） |
| videos | Array | 视频列表：`{url, coverUrl, duration}`（video 用，一段） |
| links | Array | 链接列表：`{url, title, icon}`（custom 用） |

### 出参（原始数据）

新素材 ID（String，十进制）。

### 调用示例

```json
{"capability":"ops.marketing.guide-material.content-create","input":{"title":"秋装上新素材","contentType":"image","copyText":"秋装新品上市，欢迎到店选购","attachment":{"type":"image","images":[{"width":800,"height":600}]},"relatedContent":{"product":{"scope":"all"}},"groupId":"5200000000000000001","scope":{"store":{"type":"all","ids":[]}},"publishTimeType":"permanent"},"summary":"创建秋装图片素材草稿"}
```

---

## ✅ 更新内容素材 — `ops.marketing.guide-material.content-update`

- **风险**：🟡 可逆写
- **前置**：素材存在；部分更新（仅非空字段生效）。**任何发布状态下都可更新**（含已发布——更新立即生效，注意先确认影响）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 素材 ID |
| title | String | 否 | ≤100 字 |
| contentType | String | 否 | image/poster/video/image_poster/custom |
| copyText | String | 否 | ≤5000 字 |
| attachment | Object | 否 | 整体替换（结构同创建） |
| relatedContent | Object | 否 | 整体替换（结构同创建） |
| groupId | String | 否 | 分组 ID |
| scope | Object | 否 | 适用范围 |
| publishTimeType | String | 否 | permanent/scheduled |
| publishStartTime / publishEndTime | String | 否 | yyyy-MM-dd HH:mm:ss |

### 出参（原始数据）

无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.guide-material.content-update","input":{"id":"5400000000000000001","title":"秋装上新素材（修订）","copyText":"秋装新品上市，全场满减"},"summary":"修订素材标题与文案"}
```

---

## ✅ 发布内容素材 — `ops.marketing.guide-material.content-publish`

- **风险**：🔴 商业影响（对导购端立即可见）
- **前置**：当前状态为 draft 或 unpublished；published 状态重复发布会报业务错误。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 素材 ID |

### 出参（原始数据）

无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.guide-material.content-publish","input":{"id":"5400000000000000001"},"summary":"发布素材给导购端"}
```

---

## ✅ 取消发布内容素材 — `ops.marketing.guide-material.content-unpublish`

- **风险**：🔴 商业影响（导购端立即不可见）
- **前置**：当前状态为 published；取消后可再次发布。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 素材 ID |

### 出参（原始数据）

无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.guide-material.content-unpublish","input":{"id":"5400000000000000001"},"summary":"下架已发布素材"}
```

---

## ✅ 删除内容素材 — `ops.marketing.guide-material.content-delete`

- **风险**：🔴 不可逆（物理删除）
- **前置**：素材**非 published**——已发布素材需先取消发布。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 素材 ID |

### 出参（原始数据）

无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.guide-material.content-delete","input":{"id":"5400000000000000001"},"summary":"删除草稿素材"}
```

---

## ✅ 内容素材置顶/取消置顶 — `ops.marketing.guide-material.content-toggle-top`

- **风险**：🟡 可逆写（再调一次即反转）
- **前置**：素材存在；对发布状态无要求。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 素材 ID |

### 出参（原始数据）

无业务数据；当前置顶态以列表 isTop 回读为准。

### 调用示例

```json
{"capability":"ops.marketing.guide-material.content-toggle-top","input":{"id":"5400000000000000001"},"summary":"置顶该素材"}
```

---

## ✅ 创建分组 — `ops.marketing.guide-material-group.create`

- **风险**：🟡 可逆写（无子分组且无素材时可删）
- **前置**：groupName ≤100 字必填；bizType 必填；**最多两级**（只能在一级分组下建子分组）；同一父级下子分组不超过 10 个；children 仅在创建一级分组（parentId 为空）时有效。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| groupName | String | ✅ | 分组名，≤100 字 |
| parentId | String | 否 | 父分组 ID（一级分组不传） |
| bizType | String | ✅ | content_material/speech |
| sortOrder | Integer | 否 | 排序值 |
| children | String[] | 否 | 子分组名列表（≤10 个，仅一级分组时批量创建二级） |

### 出参（原始数据）

新分组 ID（String，十进制）。

### 调用示例

```json
{"capability":"ops.marketing.guide-material-group.create","input":{"groupName":"秋冬季素材","bizType":"content_material","sortOrder":0,"children":["新品图","活动图"]},"summary":"创建秋冬季一级分组并带两个子分组"}
```

---

## ✅ 更新分组 — `ops.marketing.guide-material-group.update`

- **风险**：🟡 可逆写
- **前置**：分组存在；仅支持改分组名与排序值（不能移动层级/换父分组）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| groupId | String | ✅ | 分组 ID |
| groupName | String | 否 | ≤100 字 |
| sortOrder | Integer | 否 | 排序值 |

### 出参（原始数据）

无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.guide-material-group.update","input":{"groupId":"5200000000000000001","groupName":"秋冬季素材（改）","sortOrder":1},"summary":"改分组名并调排序"}
```

---

## ✅ 删除分组 — `ops.marketing.guide-material-group.delete`

- **风险**：🔴 不可逆（物理删除）
- **前置**：三重校验全过才可删——①无子分组（先删子分组）；②分组下无内容素材；③分组下无话术（两套业务都校验，即使 bizType 不同）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| groupId | String | ✅ | 分组 ID |

### 出参（原始数据）

无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.guide-material-group.delete","input":{"groupId":"5200000000000000001"},"summary":"删除空分组"}
```

---
