# 营销域 — CPS 分销员与绑定关系写操作契约

> 概念知识：`references/domains/cps-concepts.md`；状态与枚举：`references/domains/marketing-enums.md`；运营流程：`references/flows/cps-distributor-flow.md`
> 分销员是 CPS 分佣的主体（员工或普通用户），通过分组与佣金率体系决定分佣水平；绑定关系记录「消费者 ↔ 分销员」的推广归属。
> 出参为上游**原始业务数据**（不裁剪字段）。
> 状态标记：✅ 已开放（可调用）；⛔ 未开放（只整理需求，调用会得到 CAPABILITY_NOT_FOUND）。
> 本文件全部能力经 `当前运行时的 Capability 写操作执行器`（`mall.action`）调用，入参 `{capability, input, summary}`；只在用户明确要求执行对应操作时调用，风险档位与字段确认红线见入口 SKILL.md。
> **先读现值**：本模块查询能力（含状态机与未开放清单）均在 `cps-distributor-query.md`——整表覆盖式接口与编辑基线一律先读查询锚点，再全量提交。
> 能力索引（前缀 `ops.marketing.`）：cps-distributor.create 新建分销员（员工） 🔴 · cps-distributor.set-status 启用/禁用分销员 🔴 · cps-distributor.batch-status 批量启停分销员 🔴 · cps-distributor.batch-group 批量修改分销员分组 🔴 · cps.distributor.import 分销员 Excel 批量导入 🔴

---

## ✅ 新建分销员 — `ops.marketing.cps-distributor.create`

- **风险**：🔴 商业影响（创建分佣主体）
- **前置**：`employeeId` 必须是 B 端员工账号 ID；姓名/手机号由服务端通过用户中心自动获取，**不要传 name/phone**。
- **后果**：创建后即为启用状态，可参与分佣（受佣金率配置约束）。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| employeeId | String | ✅ | B 端员工 ID（员工账号主键），≤64 字符 |
| groupId | String | 否 | 关联分组 ID（影响分组佣金率命中） |

### 出参（原始数据）

- **路径参数来源**：`uid`（新建分销员的用户 UID，可用于后续详情/启停操作）
- 其余为展示型字段（name/contactPhone/level/groupName 等），可直接透传。

### 调用示例

```json
{"capability":"ops.marketing.cps-distributor.create","input":{"employeeId":"1000000000000000001","groupId":"5300000000000000001"},"summary":"将B端员工添加为高佣金分组分销员"}
```

---

## ✅ 启用/禁用分销员 — `ops.marketing.cps-distributor.set-status`

- **风险**：🔴 商业影响（禁用后停止分佣资格）
- **前置**：分销员存在。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uid | String | ✅ | 分销员 UID（路径参数） |
| status | Integer | ✅ | 目标状态：0=启用，1=禁用 |

### 出参（原始数据）

- 无业务数据（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.cps-distributor.set-status","input":{"uid":"900000000000000001","status":1},"summary":"禁用该分销员"}
```

---

## ✅ 批量启用/禁用分销员 — `ops.marketing.cps-distributor.batch-status`

- **风险**：🔴 商业影响（批量变更分佣资格）
- **前置**：UID 列表 1..500 条，不允许为空。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uids | String[] | ✅ | 分销员 UID 列表，1..500 条 |
| status | Integer | ✅ | 目标状态：0=启用，1=禁用 |

### 出参（原始数据）

- 布尔结果（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.cps-distributor.batch-status","input":{"uids":["900000000000000001","900000000000000002"],"status":1},"summary":"批量禁用两名分销员"}
```

---

## ✅ 批量修改分销员分组 — `ops.marketing.cps-distributor.batch-group`

- **风险**：🔴 商业影响（分组变更会影响分组佣金率命中，进而改变分佣水平）
- **前置**：UID 列表 1..500 条；目标分组必须已存在。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| uids | String[] | ✅ | 分销员 UID 列表，1..500 条 |
| groupId | String | ✅ | 目标分组 ID |

### 出参（原始数据）

- 布尔结果（成功即生效）。

### 调用示例

```json
{"capability":"ops.marketing.cps-distributor.batch-group","input":{"uids":["900000000000000001","900000000000000002"],"groupId":"5300000000000000001"},"summary":"将两名分销员调整到高佣金分组"}
```

---

## ✅ 分销员批量导入 — `ops.marketing.cps.distributor.import`

- **风险**：🔴 批量创建分佣主体（同申请审核「通过即建分销员」档位）——导入的分销员可逐条停用，但不自动回滚整批
- **说明**：按导入模板 Excel 批量创建分销员（openChannel=运营端导入）。仅**文件型 capability** 可执行；导入结果含成功/失败明细，失败行修正后可重导。

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | 文件（multipart） | ✅ | .xlsx（≤10MiB），列结构与运营端导入模板一致 |

### 出参（原始数据）

- **展示字段**：导入结果（成功数/失败数/失败行明细，`DistributorImportResultVO`）

### 调用示例

```json
{"capability":"ops.marketing.cps.distributor.import","input":{"file":"uploads/批量导入模板.xlsx", "fileType":"excel"},"summary":"按模板批量导入分销员名单"}
```

---
