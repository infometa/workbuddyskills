# 营销域 — 导购管理写操作契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-flow.md`
> 覆盖导购主档 CRUD、状态流转、导购维度统计（月度/总量/趋势）与操作日志。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `guide-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：guide.create 新增导购 🟡 · guide.update 编辑导购（含调店） 🟡 · guide.disable 停用导购 🔴 · guide.enable 启用导购 🟡 · guide.archive 归档导购 🔴 · guide.import 导购 Excel 批量导入 🟡

---

## ✅ 新增导购 — `ops.marketing.guide.create`

- **风险**：🟡 可逆写——新档创建后可停用/归档
- **前置**：归属门店必须存在；手机号在租户内未被其他导购占用（重复报错）。创建后状态为 `pending`（待激活），需导购端完成激活后才可停用。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | String | ✅ | 导购姓名，≤50 字符 |
| phone | String | ✅ | 手机号，须匹配 `1[3-9]` 开头的 11 位大陆手机号 |
| storeId | String | ✅ | 归属门店 ID |
| gender | Integer | 否 | 0-未知（默认）/1-男/2-女 |
| weworkId | String | 否 | 企微 ID，≤100 字符 |
| joinTime | String | 否 | 入职日期 yyyy-MM-dd（也兼容 ISO 8601 带时区格式） |

### 出参（原始数据）

| 字段 | 说明 |
|------|------|
| id | 新建导购 ID |

### 调用示例

```json
{"capability":"ops.marketing.guide.create","input":{"name":"王小雅","phone":"13800138000","storeId":"1200000000000000001","gender":2,"joinTime":"2026-03-01"},"summary":"新增导购王小雅"}
```

---

## ✅ 编辑导购（含调店） — `ops.marketing.guide.update`

- **风险**：🟡 可逆写（普通编辑）/ 🔴 商业影响（**调店**触发客户归属批量处理）
- **前置**：导购存在；手机号变更时租户内唯一。仅更新非空字段（无法通过本接口清空字段）。
- **调店语义**（storeId 与当前归属门店不同即触发）：
  - `customerTransferStrategy=stay`：该导购全部客户解绑，无其他绑定关系的客户进入公共池；
  - `follow` / `individual`：本期不处理客户（客户跟随导购留在新店）。
- **注意**：普通字段编辑与调店共用一个接口——**只在用户明确要求调店时才传 storeId**，否则保持 storeId 不传。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 导购 ID（路径参数） |
| name | String | 否 | 姓名，≤50 字符 |
| phone | String | 否 | 手机号（须符合格式校验） |
| storeId | String | 否 | 归属门店 ID；**与现值不同即触发调店流程** |
| gender | Integer | 否 | 0-未知/1-男/2-女 |
| weworkId | String | 否 | 企微 ID，≤100 字符 |
| joinTime | String | 否 | 入职日期 yyyy-MM-dd |
| levelId | String | 否 | 等级 ID |
| avatar | String | 否 | 头像 URL，≤500 字符 |
| customerTransferStrategy | String | 否 | 调店时客户策略：`follow`-客户跟随/`stay`-客户留在原店/`individual`-逐一选择（本期按 follow 处理） |

### 出参（原始数据）

无（成功即空）。

### 调用示例

```json
{"capability":"ops.marketing.guide.update","input":{"id":"5100000000000000001","storeId":"1200000000000000002","customerTransferStrategy":"stay"},"summary":"将导购调到新门店，客户留在原店"}
```

---

## ✅ 停用导购 — `ops.marketing.guide.disable`

- **风险**：🔴 商业影响——**必须同时决定该导购名下全部客户的归属**
- **前置**：仅 `active`（在职）状态可停用。
- 客户转移方式见 `guide-query.md` 头部「客户转移方式」表；`admin_assign` 时 `targetGuideId` 必填（漏传报错）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 导购 ID（路径参数） |
| transferMethod | String | ✅ | `admin_assign`/`public_pool`/`store_round_robin` |
| targetGuideId | String | 条件 | 目标导购 ID，`admin_assign` 时必填 |

### 出参（原始数据）

无（成功即空）。

### 调用示例

```json
{"capability":"ops.marketing.guide.disable","input":{"id":"5100000000000000001","transferMethod":"public_pool"},"summary":"停用导购，客户释放到公共池"}
```

---

## ✅ 启用导购 — `ops.marketing.guide.enable`

- **风险**：🟡 可逆写
- **前置**：仅 `disabled`（已停用）状态可启用，恢复为在职。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 导购 ID（路径参数） |

### 出参（原始数据）

无（成功即空）。

### 调用示例

```json
{"capability":"ops.marketing.guide.enable","input":{"id":"5100000000000000001"},"summary":"重新启用已停用导购"}
```

---

## ✅ 归档导购 — `ops.marketing.guide.archive`

- **风险**：🔴 不可逆——归档为**终态**，无任何恢复端点
- **前置**：仅 `disabled`（已停用）状态可归档；请先停用并处理好客户归属再归档。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 导购 ID（路径参数） |

### 出参（原始数据）

无（成功即空）。

### 调用示例

```json
{"capability":"ops.marketing.guide.archive","input":{"id":"5100000000000000001"},"summary":"归档已停用导购"}
```

---

## ✅ 导购批量导入 — `ops.marketing.guide.import`

- **风险**：🟡 可逆写——导入的导购可逐条停用/归档，但不自动回滚整批
- **说明**：按导入模板 Excel 批量创建导购。仅**文件型 capability**（当前运行时提供文件输入时）可执行，本地路径不得放入结构化 input。导入结果含成功/失败明细，逐条核对后向用户报告，失败行修正后可重导。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | 文件（multipart） | ✅ | .xlsx（≤10MiB），列结构与运营端导入模板一致 |

### 出参（原始数据）

- **展示字段**：导入结果（成功数/失败数/失败行明细，`GuideImportResultVO`）

### 调用示例

```json
{"capability":"ops.marketing.guide.import","input":{"file":"uploads/批量导入模板.xlsx", "fileType":"excel"},"summary":"按模板批量导入导购名单"}
```

---
