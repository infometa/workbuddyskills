# 会员域 — 会员导入导出查询契约（导出与任务查询）

> 概念知识：`references/domains/member-concepts.md`（会员导入导出任务口径），状态与枚举：`references/domains/member-enums.md`；运营流程：`references/flows/member-import-export.md`；导入会员/导入黑名单（写操作）见 `member-import-export-action.md`，会员档案查询见 `member-query.md`。
> 出参为上游**原始业务数据**（不裁剪字段）。任务归属为**租户维度**（非仅创建人可见）。
> **工具**：`当前运行时的 Capability 查询执行器`（`mall.query`）。
> 能力索引：member.member.export 导出会员（URL 型） · member.member.export-task.latest 最近一次导出任务 · member.member.export-task.list 导出任务列表 · member.member.export-task.status 导出任务状态轮询 · member.member.import-task.latest 最近一次导入任务 · member.member.import-task.list 导入任务列表 · member.member.import-task.status 导入任务状态轮询

---

## ✅ 导出会员 — ops.member.member.export

- URL 型导出（COS 预签名 URL）；⚠️ 导出内容含会员批量 PII（手机号等），后端已按 IMPORTANT 级审计留痕——只把下载 URL 转告用户，不在答复中复述文件内容

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nickname | String | — | 昵称（模糊） |
| memberNo | String | — | 会员编号（精确） |
| uid | String | — | UID（精确） |
| phone | String | — | 手机号（精确） |
| source | String | — | 注册来源 |
| registerTimeStart / registerTimeEnd | String | — | 注册时间范围（yyyy-MM-dd HH:mm:ss） |
| level | Integer | — | 会员等级数值 |
| status | Integer | — | 会员状态：0=正常 1=冻结 2=黑名单 3=已注销 |
| hasPhone | Boolean | — | 三态：true=已绑手机号 / false=未绑 / 不传=不过滤 |
| unionId | String | — | 微信 UnionID（精确） |

不传任何筛选条件 = 导出全量会员（注意数据量）。

### 出参（原始返回）

导出结果对象。**关键字段**：`mode`（sync/async 双模式——**命中行数 ≤5000 同步**，直接返回 `downloadUrl`；**>5000 异步**，返回 `taskId` 用 `export-task.status` 轮询）、`downloadUrl`（sync 时有值；60 分钟时效预签名 URL）、`taskId`（async 时有值，→ export-task 路径参数）、`fileName`（导出文件名，sync 模式返回，供转告用户下载命名）、`expireTime`（async 时文件过期时间，文件保留 7 天）；**格式敏感字段**：`taskId`（Long→string）、`expireTime`（yyyy-MM-dd HH:mm:ss）。

### 调用示例

```json
{"capability":"ops.member.member.export","input":{"status":0,"registerTimeStart":"2026-09-01 00:00:00"},"summary":"导出 9 月注册的正常状态会员"}
```

---

## ✅ 最近一次导出任务 — ops.member.member.export-task.latest

- 无入参；返回**租户维度**最近一次导出任务（含 sync/async 全部模式记录，**非仅本人创建**）；无任务返回 `null`

### 调用示例

```json
{"capability":"ops.member.member.export-task.latest","input":{},"summary":"查看最近一次会员导出任务"}
```

---

## ✅ 导出任务列表 — ops.member.member.export-task.list

- 租户维度任务历史（按创建时间倒序）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | — | 分页（默认 1 / 10） |

### 出参（原始返回）

分页对象，`records[]` 为导出任务视图。**关键字段**：`taskId`（→ status 路径参数）、`status`（**字符串**：pending/processing/completed/expired——与导入任务的整数状态不同）、`mode`（sync/async）、`totalCount`（导出总条数）、`fileName`（导出文件名）、`downloadUrl`（completed 时有值，60 分钟时效）、`errorMessage`；**格式敏感字段**：`expireTime`/`createdTime`（yyyy-MM-dd HH:mm:ss）。

### 调用示例

```json
{"capability":"ops.member.member.export-task.list","input":{"pageNum":1,"pageSize":10},"summary":"查看会员导出任务历史"}
```

---

## ✅ 导出任务状态 — ops.member.member.export-task.status

- 异步导出后轮询用（未完成时不得当作失败）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| taskId | String | ✅ | 任务 ID（来自 export 响应或 list 的 `taskId`） |

### 出参（原始返回）

单个导出任务对象（结构同 list 条目）。`status=completed` 时取 `downloadUrl` 转告用户；`expired` 表示文件已过 7 天保留期，需重新导出。

### 调用示例

```json
{"capability":"ops.member.member.export-task.status","input":{"taskId":"6800000000000000001"},"summary":"查询导出任务进度"}
```

---

## ✅ 最近一次导入任务 — ops.member.member.import-task.latest

- 无入参；返回租户维度最近一次**会员导入**（type=member）任务；无任务返回 `null`

### 调用示例

```json
{"capability":"ops.member.member.import-task.latest","input":{},"summary":"查看最近一次会员导入任务"}
```

---

## ✅ 导入任务列表 — ops.member.member.import-task.list

- 会员导入与黑名单导入任务混排（按创建时间倒序），`type` 字段区分（member/blacklist）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| pageNum / pageSize | Integer | — | 分页（默认 1 / 10） |

### 出参（原始返回）

分页对象。**关键字段**：`taskId`、`status`（**整数**：0=处理中 1=已完成 2=失败——与导出任务的字符串状态不同，勿混）、`totalCount`/`processedCount`/`successCount`/`failureCount`（进度四计数）、`hasFailureDetail`（true=有失败明细文件，仅管理后台可下载）、`fileName`（原始上传文件名）、`errorMessage`、`type`（member/blacklist）；**格式敏感字段**：`createdTime`（yyyy-MM-dd HH:mm:ss）。

### 调用示例

```json
{"capability":"ops.member.member.import-task.list","input":{"pageNum":1,"pageSize":10},"summary":"查看导入任务历史"}
```

---

## ✅ 导入任务状态 — ops.member.member.import-task.status

- 会员导入为异步受理，提交后按此轮询（建议间隔数秒，status=0 未完成时不得当作失败）

### 入参

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| taskId | String | ✅ | 任务 ID（来自 import 响应的 `taskId`） |

### 出参（原始返回）

单个导入任务对象（结构同 list 条目）。

### 调用示例

```json
{"capability":"ops.member.member.import-task.status","input":{"taskId":"6800000000000000002"},"summary":"轮询导入任务进度"}
```

---

## ⛔ 未开放能力（后台存在，当前开放能力集未包含）

| 业务能力 | 说明 |
|------|------|
| 导出文件下载 / 导入失败明细下载 / 导入模板下载（download / failures / template） | 文件流型下载——产品决策仅开放 URL 型导出；导出任务的 `downloadUrl` 已覆盖下载需求，模板与失败明细走管理后台 |
