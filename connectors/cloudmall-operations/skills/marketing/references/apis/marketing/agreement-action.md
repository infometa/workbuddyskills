# 营销域 — 协议管理写操作契约

> 概念知识：`references/domains/marketing-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/marketing-support-flow.md`
> 协议按类型管理（9 类），同类型同时只有一个“已发布”版本——发布新协议会自动结束同类型旧协议。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `agreement-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：agreement.create 新建协议 🟡 · agreement.update 编辑协议 🟡 · agreement.publish 发布协议 🔴 · agreement.end 结束协议 🔴 · agreement.delete 删除协议 🔴 · agreement.upload-image 上传协议插图 🟡

---

## ✅ 新建协议 — `ops.marketing.agreement.create`

- **风险**：🟡 可逆写（创建为未发布草稿）
- **说明**：内容为富文本 HTML，服务端会做安全净化（脚本等危险标签被移除）；创建后状态 0（未发布）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | String | ✅ | 协议标题，≤15 字 |
| content | String | ✅ | 协议内容（富文本 HTML），≤30000 字符 |
| type | Integer | ✅ | 协议类型 1..9 |

### 出参（原始数据）

- **关键字段来源**：返回对象含 `id`（新协议 ID）→ 后续编辑/发布。

### 调用示例

```json
{"capability":"ops.marketing.agreement.create","input":{"title":"隐私政策","content":"<p>我们高度重视您的个人信息保护……</p>","type":2},"summary":"创建新的隐私政策草稿"}
```

---

## ✅ 编辑协议 — `ops.marketing.agreement.update`

- **风险**：🟡 可逆写
- **前置**：仅未发布（status=0）可编辑；已发布需先结束（终态不可再编辑）。先读详情做基线。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 协议 ID（路径参数） |
| title | String | ✅ | 协议标题，≤15 字 |
| content | String | ✅ | 协议内容（富文本 HTML），≤30000 字符 |

### 出参

- 无 data（成功即已保存）。

### 调用示例

```json
{"capability":"ops.marketing.agreement.update","input":{"id":"5300000000000000001","title":"隐私政策","content":"<p>更新后的隐私政策全文……</p>"},"summary":"修订未发布的隐私政策内容"}
```

---

## ✅ 发布协议 — `ops.marketing.agreement.publish`

- **风险**：🔴 生效动作（C 端即刻按新版本展示）
- **前置**：仅未发布（0）。**硬门禁（未确认不得调用）**：发布会自动结束同类型当前"已发布"的旧协议——调用前必须先用 `agreement.search` 查出该类型现行协议标题，向用户复述「同类型已发布的《{现行协议标题}》将被自动结束且不可恢复，确认发布？」并取得明确确认；用户指令本身含"发布"二字不豁免此确认。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 协议 ID |

### 调用示例

```json
{"capability":"ops.marketing.agreement.publish","input":{"id":"5300000000000000001"},"summary":"发布新版隐私政策（自动结束旧版）"}
```

---

## ✅ 结束协议 — `ops.marketing.agreement.end`

- **风险**：🔴 不可逆（已结束终态，仅可删除）
- **前置**：仅已发布（1）。结束后该类型 C 端无生效协议（如需替换请发布新协议）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 协议 ID |

### 调用示例

```json
{"capability":"ops.marketing.agreement.end","input":{"id":"5300000000000000001"},"summary":"下线当前生效的隐私政策"}
```

---

## ✅ 删除协议 — `ops.marketing.agreement.delete`

- **风险**：🔴 不可逆（物理删除）
- **前置**：已发布（1）不可删除，需先结束。
- **删除后必须回读**：delete 成功响应为空——**必须再 `agreement.search` 确认目标已不在列表**，以搜索空集为核验，不以"操作成功"为证。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 协议 ID |

### 调用示例

```json
{"capability":"ops.marketing.agreement.delete","input":{"id":"5300000000000000001"},"summary":"删除废弃的协议草稿"}
```

---

## ✅ 上传协议图片 — `ops.marketing.agreement.upload-image`

- **风险**：🟡 可逆写（图片未引用前可忽略）
- **说明**：为协议富文本正文上传插图。仅**文件型 capability**（当前运行时提供文件输入时）可执行，本地路径不得放入结构化 input；返回的图片 URL 嵌入协议 `content` 的富文本中。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | 文件（multipart） | ✅ | 图片文件（≤5MiB） |

### 出参（原始数据）

- **路径参数来源**：返回的图片 URL（→ 嵌入协议 content 富文本）

### 调用示例

```json
{"capability":"ops.marketing.agreement.upload-image","input":{"file":"uploads/图片素材.png", "fileType":"image"},"summary":"上传协议正文插图"}
```

---
