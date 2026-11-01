# 营销域 — 导购目标计划写操作契约

> 概念知识：`references/domains/guide-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/guide-incentive-flow.md`
> 目标计划 = 考核周期容器（仅周期信息），导购目标行独立管理（新增空白行 → 填值/导入/按上期填充）。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `guide-target-plan-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：guide-target-plan.create 新建目标计划 🟡 · guide-target-plan.update 编辑目标计划周期 🟡 · guide-target-plan.delete 删除目标计划 🔴 · guide-target-plan.update-target 更新单条导购目标 🟡 · guide-target-plan.batch-add-targets 批量新增空白目标行 🟡 · guide-target-plan.fill-by-last-period 按上期 N% 填充目标 🔴 · guide-target-plan.clear-targets 清空全部目标值 🔴 · guide-target-plan.delete-target 删除单条目标行 🟡 · guide.target-plan.import 目标行 Excel 批量导入 🟡

---

## ✅ 新建目标计划 — `ops.marketing.guide-target-plan.create`

- **风险**：🟡 可逆写（未开始状态可编辑/删除）
- **前置**：同租户下该周期（periodType+year+period）不存在目标计划，重复报「该周期已存在目标计划」。
- 创建只保存周期信息；起止日期与初始状态自动计算（按当前日期判定未开始/进行中/已结束）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| periodType | String | ✅ | `monthly` 月度 / `quarterly` 季度 |
| year | Integer | ✅ | 年度，如 2026 |
| period | Integer | ✅ | 月度填月份 1..12；季度填季数 1..4 |

### 出参（原始数据）

- 新建计划的基本信息（同详情：id/periodType/year/period/periodLabel/startDate/endDate/status）。
- **关键字段来源**：返回 `id`（十进制字符串）→ 后续添加导购目标、查汇总等均用它。

### 调用示例

```json
{"capability":"ops.marketing.guide-target-plan.create","input":{"periodType":"monthly","year":2026,"period":11},"summary":"创建2026年11月月度目标计划"}
```

---

## ✅ 编辑目标计划 — `ops.marketing.guide-target-plan.update`

- **风险**：🟡 可逆写
- **前置**：计划存在；新周期（periodType+year+period）不与其他计划重复（排除自身）。起止日期与状态按新周期重算。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 目标计划 ID |
| periodType | String | ✅ | 同新建 |
| year | Integer | ✅ | 同新建 |
| period | Integer | ✅ | 同新建 |

### 调用示例

```json
{"capability":"ops.marketing.guide-target-plan.update","input":{"id":"5100000000000000001","periodType":"monthly","year":2026,"period":12},"summary":"把目标计划周期改为2026年12月"}
```

---

## ✅ 删除目标计划 — `ops.marketing.guide-target-plan.delete`

- **风险**：🔴 不可逆——级联删除该计划下**所有导购目标记录**。
- **前置**：仅 `not_started`（未开始）状态的计划可删；进行中/已结束报「仅未开始的目标计划可以删除」。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 目标计划 ID |

### 调用示例

```json
{"capability":"ops.marketing.guide-target-plan.delete","input":{"id":"5100000000000000001"},"summary":"删除未开始的错误周期计划"}
```

---

## ✅ 更新单条导购目标 — `ops.marketing.guide-target-plan.update-target`

- **风险**：🟡 可逆写
- **前置**：该计划下此导购的目标行已存在（先用 batch-add-targets 添加）；不存在报「该导购目标不存在」。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| planId | String | ✅ | 目标计划 ID |
| guideId | String | ✅ | 导购 ID |
| salesTarget | Number | 否 | 销售额目标（元） |
| customerTarget | Integer | 否 | 客户目标（人数） |

- 两个字段均可选，未传的字段会被置空（整体覆盖语义）。

### 调用示例

```json
{"capability":"ops.marketing.guide-target-plan.update-target","input":{"planId":"5100000000000000001","guideId":"5300000000000000001","salesTarget":50000,"customerTarget":30},"summary":"设定该导购销售额目标5万元、客户目标30人"}
```

---

## ✅ 批量新增空白导购目标 — `ops.marketing.guide-target-plan.batch-add-targets`

- **风险**：🟡 可逆写（可逐条删除）
- **前置**：计划存在。已在计划中的导购自动跳过；不存在的导购 ID 静默跳过（不报错）——执行后建议回查 targets 列表核验实际新增。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| planId | String | ✅ | 目标计划 ID |
| guideIds | String[] | ✅ | 导购 ID 列表，至少 1 个 |

### 调用示例

```json
{"capability":"ops.marketing.guide-target-plan.batch-add-targets","input":{"planId":"5100000000000000001","guideIds":["5300000000000000001","5300000000000000002"]},"summary":"为计划批量添加两名导购的目标行"}
```

---

## ✅ 按上期 N% 填充目标 — `ops.marketing.guide-target-plan.fill-by-last-period`

- **风险**：🔴 覆盖性写——当期**全部**目标行的目标值被按上期实际业绩 × N% 重算覆盖；无上期数据的导购目标被置为 0。
- **前置**：percentage 为正整数；能推算上期（月度的上月 / 季度的上季度，1 月/1 季度自动跨年）。销售额保留 2 位小数，客户数四舍五入取整。
- 执行后建议回查 targets 列表核验填充结果。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| planId | String | ✅ | 目标计划 ID |
| percentage | Integer | ✅ | 填充百分比，>0（如 100 表示按上期 100%） |

### 调用示例

```json
{"capability":"ops.marketing.guide-target-plan.fill-by-last-period","input":{"planId":"5100000000000000001","percentage":100},"summary":"按上期实际业绩100%填充当期全部目标"}
```

---

## ✅ 清空全部目标值 — `ops.marketing.guide-target-plan.clear-targets`

- **风险**：🔴 不可逆——计划下所有导购目标的销售额目标与客户目标置空（目标行保留，可重新填值）。
- **前置**：计划存在即执行（不校验状态）；执行后建议回查 target-summary 核验。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| planId | String | ✅ | 目标计划 ID |

### 调用示例

```json
{"capability":"ops.marketing.guide-target-plan.clear-targets","input":{"planId":"5100000000000000001"},"summary":"清空该计划全部导购目标值以便重新设定"}
```

---

## ✅ 删除单条导购目标 — `ops.marketing.guide-target-plan.delete-target`

- **风险**：🟡 可通过批量新增重建
- **前置**：无状态校验（记录不存在时静默成功）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| planId | String | ✅ | 目标计划 ID |
| guideId | String | ✅ | 导购 ID |

### 调用示例

```json
{"capability":"ops.marketing.guide-target-plan.delete-target","input":{"planId":"5100000000000000001","guideId":"5300000000000000001"},"summary":"移除该导购的目标行"}
```

---

## ✅ 批量导入目标行 — `ops.marketing.guide.target-plan.import`

- **风险**：🟡 可逆写——导入的目标行可逐条删除或覆盖填值，但不自动回滚整批
- **说明**：向指定**目标计划**批量导入导购目标行（.xlsx）。仅**文件型 capability** 可执行；`planId` 为路径参数。导入结果含成功/失败明细，失败行修正后可重导；也可用 `batch-add-targets` + `update-target` 手工组合替代。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| planId | String | ✅ | 目标计划 ID（路径参数） |
| file | 文件（multipart） | ✅ | .xlsx（≤10MiB），列结构与运营端导入模板一致 |

### 出参（原始数据）

- **展示字段**：导入结果（成功数/失败数/失败行明细）

### 调用示例

```json
{"capability":"ops.marketing.guide.target-plan.import","input":{"file":"uploads/批量导入模板.xlsx", "planId":"5300000000000000001","fileType":"excel"},"summary":"按模板向11月目标计划导入目标行"}
```

---
