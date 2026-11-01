# 营销域 — 导购话术写操作契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-content-flow.md`
> 话术库：运营编辑多条内容块话术，按分组管理，供导购在工作台查阅/分享（分享计数存于缓存计数器）。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `guide-speech-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：guide-speech.create 创建话术 🟡 · guide-speech.update 更新话术 🟡 · guide-speech.delete 删除话术 🔴 · guide-speech.batch-update-group 批量修改话术分组 🟡 · guide-speech.batch-delete 批量删除话术 🔴 · guide-speech.share 话术分享计数 🟡 · guide-speech.toggle-top 话术置顶/取消 🟡 · guide.speech.import 话术 Excel 批量导入 🟡

---

## ✅ 创建话术 — `ops.marketing.guide-speech.create`

- **风险**：🟡 可逆写（可编辑/删除）
- **前置**：标题必填 ≤100 字；内容块 1..9 条。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | String | ✅ | 话术标题，≤100 字 |
| groupId | String | 否 | 分组 ID（素材分组树 bizType=speech 的分组） |
| scope | Object | 否 | 适用范围 `{userTag/user/store/guide: {type: all\|specified, ids}}` |
| contentBlocks | Array | ✅ | 内容块，1..9 条 |
| contentBlocks[].content | String | 否 | 内容块文本 |
| contentBlocks[].sortOrder | Integer | 否 | 排序序号（详情按升序返回） |

### 出参（原始数据）

新话术 ID（String，十进制）。

### 调用示例

```json
{"capability":"ops.marketing.guide-speech.create","input":{"title":"秋冬新品开场话术","groupId":"5200000000000000001","scope":{"userTag":{"type":"all","ids":[]}},"contentBlocks":[{"content":"您好，本季新品已到店，欢迎体验","sortOrder":1}]},"summary":"创建秋冬新品开场话术"}
```

---

## ✅ 更新话术 — `ops.marketing.guide-speech.update`

- **风险**：🟡 可逆写
- **前置**：话术存在；部分更新（仅非空字段生效）；**contentBlocks 一旦传入即全量替换**（先删后插）——只想改标题时不要带 contentBlocks。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 话术 ID |
| title | String | 否 | ≤100 字 |
| groupId | String | 否 | 分组 ID |
| scope | Object | 否 | 适用范围（结构同创建） |
| contentBlocks | Array | 否 | 全量替换，1..9 条（结构同创建） |

### 出参（原始数据）

无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.guide-speech.update","input":{"id":"5300000000000000001","title":"秋冬新品开场话术（修订）"},"summary":"仅修订话术标题"}
```

---

## ✅ 删除话术 — `ops.marketing.guide-speech.delete`

- **风险**：🔴 不可逆（物理删除）
- **前置**：话术存在；同时删除其全部内容块记录。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 话术 ID |

### 出参（原始数据）

无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.guide-speech.delete","input":{"id":"5300000000000000001"},"summary":"删除话术及其内容块"}
```

---

## ✅ 批量修改分组 — `ops.marketing.guide-speech.batch-update-group`

- **风险**：🟡 可逆写（可再改回）
- **前置**：speechIds 非空；targetGroupId 必填（bizType=speech 的分组）。`action` 为必填占位字段（校验要求非空，服务端不使用其取值，固定传 `move_group`）。
- **返回**：successCount 为实际存在并更新成功的条数（不存在的 ID 被跳过）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| action | String | ✅ | 固定 `move_group`（校验占位） |
| speechIds | String[] | ✅ | 话术 ID 列表（来自列表 records[].id） |
| targetGroupId | String | ✅ | 目标分组 ID |

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| successCount | 成功条数 |

### 调用示例

```json
{"capability":"ops.marketing.guide-speech.batch-update-group","input":{"action":"move_group","speechIds":["5300000000000000001","5300000000000000002"],"targetGroupId":"5200000000000000002"},"summary":"把两条话术移动到目标分组"}
```

---

## ✅ 批量删除话术 — `ops.marketing.guide-speech.batch-delete`

- **风险**：🔴 不可逆（物理删除，含内容块）
- **前置**：speechIds 非空。`action` 为必填占位字段（固定传 `delete`）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| action | String | ✅ | 固定 `delete`（校验占位） |
| speechIds | String[] | ✅ | 话术 ID 列表 |

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| successCount | 成功条数 |

### 调用示例

```json
{"capability":"ops.marketing.guide-speech.batch-delete","input":{"action":"delete","speechIds":["5300000000000000001","5300000000000000002"]},"summary":"批量删除两条话术"}
```

---

## ✅ 话术分享计数 — `ops.marketing.guide-speech.share`

- **风险**：🟡 计数自增（缓存计数器 +1，可逆性弱）
- **前置**：话术存在。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 话术 ID |

### 出参（原始数据）

无业务数据（计数已自增，可通过列表/详情的 shareCount 回读）。

### 调用示例

```json
{"capability":"ops.marketing.guide-speech.share","input":{"id":"5300000000000000001"},"summary":"记录一次话术分享"}
```

---

## ✅ 话术置顶/取消置顶 — `ops.marketing.guide-speech.toggle-top`

- **风险**：🟡 可逆写（再调一次即反转）
- **前置**：话术存在。置顶后列表排序优先展示。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 话术 ID |

### 出参（原始数据）

无业务数据；当前是否置顶以列表/详情的 isTop 回读为准。

### 调用示例

```json
{"capability":"ops.marketing.guide-speech.toggle-top","input":{"id":"5300000000000000001"},"summary":"置顶该话术"}
```

---

## ✅ 话术批量导入 — `ops.marketing.guide.speech.import`

- **风险**：🟡 可逆写——导入条目可逐条删除，但不自动回滚整批
- **说明**：按导入模板 Excel 批量创建话术。仅**文件型 capability** 可执行；导入结果含成功/失败明细，失败行修正后可重导。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | 文件（multipart） | ✅ | .xlsx（≤10MiB），列结构与运营端导入模板一致 |

### 出参（原始数据）

- **展示字段**：导入结果（成功数/失败数/失败行明细，`SpeechImportResultVO`）

### 调用示例

```json
{"capability":"ops.marketing.guide.speech.import","input":{"file":"uploads/批量导入模板.xlsx", "fileType":"excel"},"summary":"按模板批量导入双11话术"}
```

---
