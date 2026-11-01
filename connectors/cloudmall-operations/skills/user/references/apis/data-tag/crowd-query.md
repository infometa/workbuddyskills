# 数据标签域 — 人群包查询契约

> 概念知识：`references/domains/data-tag.md`（人群包状态机与规则表达式），运营流程：`references/flows/data-tag.md`；人群包写操作（创建/更新/上下线/删除/上传）见 `crowd-action.md`，动态人群包与批量加用户见 `manual-tag-action.md`，标签见 `tag-query.md` / `tag-action.md`。`queryCondition` 是 JSON 字符串且规则项只接受 `tagId`。ID 均为十进制字符串。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：data-tag.crowd.search 人群包分页 · data-tag.crowd.detail 人群包详情 · data-tag.crowd.task-records 任务记录 · data-tag.crowd.members 成员列表 · data-tag.crowd.members-detail 成员导入明细 · data-tag.crowd.download 成员明细下载 · data-tag.crowd.download-fail 最近一次导入失败明细下载 · data-tag.crowd.task-download-fail 指定任务失败明细下载

---

## ✅ 人群包分页 — ops.data-tag.crowd.search

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | — | pageNum 默认 1；pageSize 默认 20、**上限 100**（@Max 校验，超限直接报错） |
| crowdId | String | — | 人群包 ID |
| crowdName | String | — | 人群包名称 |
| crowdType | Integer | — | 1=规则圈选 / 2=文件上传 / 3=动态 |
| status | Integer | — | 人群包状态 |
| updateFrequency | String | — | 更新频率 |

### 出参（原始返回）

返回 `id`、状态、匹配人数及 `hasActiveLinkedTag`（仅提示关联，不能替代下线前的业务确认）。

### 调用示例

```json
{"capability":"ops.data-tag.crowd.search","input":{"pageNum":1,"pageSize":20,"crowdType":1,"status":2},"summary":"查询已上线规则圈选人群包"}
```

---

## ✅ 人群包详情 — ops.data-tag.crowd.detail

- 执行任何写操作前先读

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 人群包 ID |

### 出参（原始返回）

返回 crowdType、status（附 statusDesc）、计算周期（calcPeriodType/calcPeriodValue）、totalCount/matchCount、lastCalcTime、fileUrl（文件上传型源文件）、failReason、`queryCondition`（**创建时传入的 JSON 原文字符串回显**——编辑回显用，结构见 crowd-action.md create-rule-select 的展开表）与 `tagValueId`（关联手工标签值）。

### 调用示例

```json
{"capability":"ops.data-tag.crowd.detail","input":{"id":"6300000000000000001"},"summary":"查看人群包状态和圈选配置"}
```

---

## ✅ 任务记录 — ops.data-tag.crowd.task-records

- 规则圈选提交或规则变更后轮询此能力

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 人群包 ID |

### 出参（原始返回）

任务记录字段：`id`（⚠️ 字段名为 `id`，不是 `taskId`——`task-download-fail` 的入参 `taskId` 取本字段的值）、`status`（当前运行时写入：`0` 处理中、`1` 成功、`2` 失败——不要套用同模块另一个六值 `CrowdTaskStatus` 枚举）、`taskType`（`1`=计算 / `2`=导入 / `11`=追加导入 / `10`=动态加入）、`hasFailRecords`（Boolean，true 时 `download-fail`/`task-download-fail` 才有文件可下）、`resultData`（成功=COS 文件 key、失败=失败原因文本）、`importData`（**恒 null**，预留字段）、操作人/时间。只有最新任务为 1 且人群详情为 ONLINE 才报告生效。

### 调用示例

```json
{"capability":"ops.data-tag.crowd.task-records","input":{"id":"6300000000000000001"},"summary":"查看人群包最新计算任务状态"}
```

---

## ✅ 成员列表 — ops.data-tag.crowd.members

- **uid 与 phone 匹配口径不同（源码核验）**：`uid` 为**模糊匹配**（contains，支持传 UID 片段）；`phone` 为**精确匹配**（服务端按完整手机号反查 UID 再与人群求交——传手机号片段会得到空结果而非部分匹配），且 phone 模式**不受分页控制**（一次返回全部命中）。成员是个人数据，应只在用户有业务权限和必要性时展示

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 人群包 ID |
| pageNum / pageSize | Integer | — | pageSize 上限 200（超限回落 50，默认 50） |
| uid | String | — | UID 筛选（模糊） |
| phone | String | — | 手机号筛选（精确，不受分页控制） |

### 调用示例

```json
{"capability":"ops.data-tag.crowd.members","input":{"id":"6300000000000000001","pageNum":1,"pageSize":50},"summary":"分页查看人群包成员UID"}
```

---

## ✅ 成员导入明细 — ops.data-tag.crowd.members-detail

- 用于手工导入类型的人群包，返回成员及导入审计字段。行结构（Map）：`uid`（十进制字符串）、`createdBy`（导入人）、`createdTime`（导入时间，yyyy-MM-dd HH:mm:ss）、`taskId`（导入任务 ID，十进制字符串）；同样支持 uid（模糊）/phone（精确，不分页）筛选

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 人群包 ID |
| pageNum / pageSize | Integer | — | pageSize 1..200 超限回落 50（默认 20） |
| uid | String | — | UID 筛选（模糊） |
| phone | String | — | 手机号筛选（精确，不分页） |

### 调用示例

```json
{"capability":"ops.data-tag.crowd.members-detail","input":{"id":"6300000000000000001","pageNum":1,"pageSize":20},"summary":"查看人群包成员导入明细"}
```

---

## ✅ 下载人群包成员明细 — ops.data-tag.crowd.download

- URL 型导出（COS 预签名 URL，**5 分钟时效**，取得后尽快转告用户）。⚠️ 前置与语义（源码核验）：仅 **ONLINE 状态**人群包可下载（否则业务错误 1731）；FILE_UPLOAD 类型返回的是**从当前人群 Bitmap 实时导出的匹配成功明细**（非上传原文件）；人群包无成员数据时报业务错误 1732

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 人群包 ID |

### 调用示例

```json
{"capability":"ops.data-tag.crowd.download","input":{"id":"6300000000000000001"},"summary":"获取人群包成员明细下载链接"}
```

---

## ✅ 下载最近一次导入失败明细 — ops.data-tag.crowd.download-fail

- **人群包级别**，始终为"最近一次导入"的失败明细；无失败明细时返回业务错误。预签名 URL 5 分钟时效

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 人群包 ID |

### 调用示例

```json
{"capability":"ops.data-tag.crowd.download-fail","input":{"id":"6300000000000000001"},"summary":"获取人群包最近一次导入失败明细链接"}
```

---

## ✅ 下载指定任务失败明细 — ops.data-tag.crowd.task-download-fail

- 按次下载（历史任务互不覆盖）；`taskId` 来自 `crowd.task-records`；校验 taskId 归属该人群包（不归属报 1730）。预签名 URL 5 分钟时效

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | String | ✅ | 人群包 ID |
| taskId | String | ✅ | 任务 ID（来自 `crowd.task-records`） |

### 调用示例

```json
{"capability":"ops.data-tag.crowd.task-download-fail","input":{"id":"6300000000000000001","taskId":"6500000000000000001"},"summary":"获取指定导入任务的失败明细链接"}
```
