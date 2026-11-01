# 营销域 — 首页弹窗写操作契约

> 概念知识：`references/domains/marketing-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/popup-review-flow.md`
> 弹窗带完整审核链（草稿 → 提审 → 审核 → 投放/驳回）；创建/编辑/审核是三种不同角色动作，AI 不得代替用户做审核结论。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `popup-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：popup.create 创建弹窗 🟡 · popup.update 编辑弹窗 🟡 · popup.submit 提交弹窗审核 🟡 · popup.review 弹窗审核 🔴 · popup.pause 暂停弹窗 🟡 · popup.resume 恢复弹窗 🟡 · popup.offline 下线弹窗 🔴 · popup.batch-offline 批量下线弹窗 🔴 · popup.delete 删除弹窗 🔴 · popup.batch-delete 批量删除弹窗 🔴 · popup.update-global-strategy 更新全局弹窗策略 🔴

---

## ✅ 创建弹窗 — `ops.marketing.popup.create`

- **风险**：🟡 可逆写（草稿模式；isDraft=false 时为强校验直发创建）
- **前置**：isDraft=true 走宽松保存（仅名称查重）；isDraft=false 服务端强校验：名称/合法模板类型/开始时间必须晚于当前/结束晚于开始/优先级/完整 ruleConfig（人群、频次、页面、门店四要素）。弹窗名称租户内不可重复。

### 入参（顶层）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | 条件 | 弹窗名称，≤50 字（非草稿必填；租户内唯一） |
| title | String | 否 | 弹窗标题，≤100 字 |
| description | String | 否 | 描述文案，≤500 字 |
| templateType | String | 条件 | 模板类型：CENTER_IMAGE/FULLSCREEN/CAROUSEL/CAROUSEL_FULLSCREEN/VIDEO/COUPON |
| templateConfig | Object | 条件 | 模板配置（按 templateType 只填对应子结构，见下） |
| startTime | String | 条件 | 投放开始时间（yyyy-MM-dd HH:mm:ss） |
| endTime | String | 否 | 投放结束时间（yyyy-MM-dd HH:mm:ss，须晚于开始） |
| ruleConfig | Object | 条件 | 投放规则（人群+频次+页面+门店，见下） |
| priority | Integer | 否 | 1..100，默认 50，越大越优先 |
| isDraft | Boolean | ✅ | true=草稿保存；false=强校验创建（仍落 DRAFT 状态，需提审后投放） |

### templateConfig 子结构（按 templateType 只填对应一项）

- `centerImage` / `fullscreen`：`{ imageUrl, link }`
- `carousel` / `carouselFullscreen`：`{ images: [{ imageUrl, sortOrder, link }], interval }`（images 2..10 张，服务端不校验张数、以前端为准；interval 轮播间隔秒 1..10 默认 3）
- `video`：`{ videoUrl, coverUrl, play: { autoPlay, muted, loop }, link }`
- `coupon`：`{ styleMode: SYSTEM/CUSTOM, couponTemplateIds: [String]（1..3 张，服务端不校验数量、以前端为准）, customImageUrl }`（无跳转 link）

`link`（跳转配置）子字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| linkType | String | ✅ | SYSTEM_PAGE/PROMOTION_PAGE/DECORATION_PAGE/EXTERNAL_MINIPROGRAM/H5_LINK/NONE |
| systemPageType | String | 条件 | linkType=SYSTEM_PAGE 必填：HOME/CATEGORY/PRODUCT_DETAIL/PROFILE/POINTS_MALL/MY_ORDERS/MY_COUPONS |
| targetId | String | 条件 | SYSTEM_PAGE+PRODUCT_DETAIL=商品 SPU ID；PROMOTION_PAGE=促销活动 ID；DECORATION_PAGE=装修页 ID |
| externalAppId | String | 条件 | linkType=EXTERNAL_MINIPROGRAM 必填 |
| externalPath | String | 条件 | 外部小程序页面路径 |
| h5Url | String | 条件 | linkType=H5_LINK 必填（https://） |

### ruleConfig 子结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| audience.targetAudience | String | ✅ | ALL=全部用户 / TAG=指定人群 |
| audience.tagIds | String[] | 条件 | 标签 ID 列表（targetAudience=TAG 时使用，来自数据标签域标签查询） |
| frequency.type | String | ✅ | EVERY_VISIT/ONCE/DAILY/CUSTOM |
| frequency.days | Integer | 条件 | type=CUSTOM：每 N 天（正整数） |
| frequency.times | Integer | 条件 | type=CUSTOM：弹 M 次（正整数） |
| page.pages[].type | String | ✅ | HOME/PRODUCT_DETAIL/CATEGORY/CART/PROFILE/CUSTOM |
| page.pages[].path | String | 条件 | type=CUSTOM 必填，必须以 /pages/ 开头 |
| store.scope | String | ✅ | ALL=全部门店 / SPECIFIED=指定门店 |
| store.storeIds | String[] | 条件 | 门店 ID 列表（scope=SPECIFIED 时使用，来自商户域门店列表） |

### 出参（原始数据）

- **关键字段来源**：返回值为新弹窗 ID（十进制字符串）→ 提审/详情/编辑。

### 调用示例

```json
{"capability":"ops.marketing.popup.create","input":{"name":"十一大促首页弹窗","title":"会员日专属福利","templateType":"CENTER_IMAGE","templateConfig":{"centerImage":{"imageUrl":"https://cos.rmall-solution.com/popup/hero-1015.png","link":{"linkType":"SYSTEM_PAGE","systemPageType":"POINTS_MALL"}}},"startTime":"2026-10-01 00:00:00","endTime":"2026-10-08 23:59:59","ruleConfig":{"audience":{"targetAudience":"ALL"},"frequency":{"type":"EVERY_VISIT"},"page":{"pages":[{"type":"HOME"}]},"store":{"scope":"ALL"}},"priority":50,"isDraft":true},"summary":"创建十一大促首页弹窗草稿"}
```

---

## ✅ 编辑弹窗 — `ops.marketing.popup.update`

- **风险**：🟡 可逆写
- **前置**：仅 DRAFT / REJECTED 状态可编辑；先读详情以现有配置为基线，保留未改动字段。字段全部可选（非 null 才覆盖）；名称仍查重。
- **注意**：请求体要求携带 `id`（与路径同值的弹窗 ID），同时 `popupId` 渲染路径——两个 ID 字段必须同值传入。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| popupId | String | ✅ | 弹窗 ID（路径参数） |
| id | String | ✅ | 弹窗 ID（请求体必填，与 popupId 同值） |
| (其余字段) | - | 否 | 结构同创建（name/title/description/templateType/templateConfig/startTime/endTime/ruleConfig/priority），非 null 覆盖 |

### 出参

- 无 data（成功即已保存）。执行后可回读详情核验。

### 调用示例

```json
{"capability":"ops.marketing.popup.update","input":{"popupId":"5100000000000000001","id":"5100000000000000001","name":"十一大促首页弹窗","title":"会员日专属福利","priority":60},"summary":"调整弹窗优先级并保存"}
```

---

## ✅ 提交审核 — `ops.marketing.popup.submit`

- **风险**：🟡 状态流转（进入待审核，审核前可被驳回回到可编辑态）
- **前置**：仅 DRAFT / REJECTED。提审即完整性强校验（名称/模板类型/开始时间/优先级/ruleConfig 四要素），不完整会报具体缺失项。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 弹窗 ID |

### 调用示例

```json
{"capability":"ops.marketing.popup.submit","input":{"id":"5100000000000000001"},"summary":"提交弹窗审核"}
```

---

## ✅ 审核 — `ops.marketing.popup.review`

- **风险**：🔴 审核动作——通过即决定弹窗可否投放
- **前置**：仅 PENDING_REVIEW。**审核结论必须来自用户的明确指示，禁止 AI 自行判断通过或驳回；驳回原因禁止编造，须依据用户给出的理由。**
- 审核动作语义：
  - `APPROVE`：直接通过。开始时间已过 → 直接 ACTIVE（投放中）；未到 → APPROVED（待投放）。
  - `EDIT_APPROVE`：先应用 `popupData` 内的修改再通过（结构与编辑入参一致，且须含 `id`）。
  - `REJECT`：驳回 → REJECTED。`reason` 必填且不少于 10 字（驳回原因会展示给创建人）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 弹窗 ID |
| action | String | ✅ | APPROVE / EDIT_APPROVE / REJECT |
| reason | String | 条件 | REJECT 时必填，≥10 字 |
| popupData | Object | 否 | EDIT_APPROVE 时的修改内容（结构同编辑入参） |

### 调用示例

```json
{"capability":"ops.marketing.popup.review","input":{"id":"5100000000000000001","action":"APPROVE"},"summary":"按用户指示通过弹窗审核"}
```

---

## ✅ 暂停弹窗 — `ops.marketing.popup.pause`

- **风险**：🟡 可逆（可恢复）
- **前置**：仅 ACTIVE（投放中）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 弹窗 ID |

### 调用示例

```json
{"capability":"ops.marketing.popup.pause","input":{"id":"5100000000000000001"},"summary":"暂停投放中的弹窗"}
```

---

## ✅ 恢复弹窗 — `ops.marketing.popup.resume`

- **风险**：🟡 可逆
- **前置**：仅 PAUSED，且投放结束时间未过期（已过期报错）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 弹窗 ID |

### 调用示例

```json
{"capability":"ops.marketing.popup.resume","input":{"id":"5100000000000000001"},"summary":"恢复已暂停的弹窗投放"}
```

---

## ✅ 下线弹窗 — `ops.marketing.popup.offline`

- **风险**：🔴 不可逆（下线后为 ENDED 终态，不可再投放）
- **前置**：ACTIVE / PAUSED / APPROVED（待投放可撤下）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 弹窗 ID |

### 调用示例

```json
{"capability":"ops.marketing.popup.offline","input":{"id":"5100000000000000001"},"summary":"手动下线该弹窗"}
```

---

## ✅ 批量下线 — `ops.marketing.popup.batch-offline`

- **风险**：🔴 不可逆（逐条下线）
- **前置**：同单条下线。**批量为逐条执行、失败跳过（部分成功），响应无逐项回执——执行后必须回读列表/状态计数核验实际结果。**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | 弹窗 ID 列表，至少 1 项 |

### 调用示例

```json
{"capability":"ops.marketing.popup.batch-offline","input":{"ids":["5100000000000000001","5100000000000000002"]},"summary":"批量下线两个到期弹窗"}
```

---

## ✅ 删除弹窗 — `ops.marketing.popup.delete`

- **风险**：🔴 不可逆（物理删除）
- **前置**：投放中（ACTIVE）不可删除，需先下线。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 弹窗 ID |

### 调用示例

```json
{"capability":"ops.marketing.popup.delete","input":{"id":"5100000000000000001"},"summary":"删除已下线的废弃弹窗"}
```

---

## ✅ 批量删除 — `ops.marketing.popup.batch-delete`

- **风险**：🔴 不可逆（逐条物理删除）
- **前置**：同单条删除。**逐条执行、失败跳过（投放中的项被跳过），执行后必须回读核验。**

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ids | String[] | ✅ | 弹窗 ID 列表，至少 1 项 |

### 调用示例

```json
{"capability":"ops.marketing.popup.batch-delete","input":{"ids":["5100000000000000001","5100000000000000002"]},"summary":"批量清理草稿与已结束弹窗"}
```

---

## ✅ 更新全局弹窗策略 — `ops.marketing.popup.update-global-strategy`

- **风险**：🔴 全租户生效（影响所有弹窗的弹出频控）
- **前置**：先查当前策略；更新为整包覆盖（四个字段全部必填），未传字段会校验失败。**硬门禁：提交前必须发确认卡复述「现值 → 目标值」（四字段逐项），取得用户明确确认后才可执行——指令参数齐全不豁免**。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| maxPopupsPerVisit | Integer | ✅ | 单次访问最多弹出数，1..10000 |
| maxPopupsPerDay | Integer | ✅ | 每日最多弹出数，1..10000 |
| intervalSeconds | Integer | ✅ | 两次弹窗最小间隔秒数，≥0 |
| sameWeightSort | String | ✅ | 同优先级排序：CREATED_DESC / CREATED_ASC / RANDOM |

### 调用示例

```json
{"capability":"ops.marketing.popup.update-global-strategy","input":{"maxPopupsPerVisit":3,"maxPopupsPerDay":10,"intervalSeconds":30,"sameWeightSort":"RANDOM"},"summary":"收紧全租户弹窗弹出频控"}
```

---
