# Moka 快招 MCP 工具参考（权威派生自代码）

本文件是 `moka-go` 技能的工具参考。**代码是唯一权威**：
工具名、参数、返回字段由 `apps/api-server/src/modules/**/*.ts` 的 `server.registerTool(...)`、
同目录 `schemas.ts` 和 `mcp/outputProjection.ts` 决定；副作用还须核对 application 用例。
本文件只是可读派生。代码改了这里没改，就会让 agent 按不存在的参数调用——
改工具后按 `contract-sync.md` 同步。

当前共 50 个工具。工具名形如 `{域}_{动作}`；
**MCP 面契约面向 Agent 独立于 REST**（时间用墙钟串、入参用 `<实体>Id`），但共用同一 application
用例内核（合并部署，禁止回调本进程 HTTP REST）。

---

## 通用形状（先读这节，它决定所有工具的读法）

### 分页：游标制，不是 limit/offset

`mcp__moka-go__job_list`、`mcp__moka-go__candidate_search`、`mcp__moka-go__interview_availability_list`、`mcp__moka-go__interview_search`、
`mcp__moka-go__mail_application_list`、`mcp__moka-go__sourcing_record_search`、`mcp__moka-go__sourcing_resume_search` 支持可选 `cursor`
（上一页返回的 `nextCursor`），返回：

```
{ items: [...], nextCursor: string | null, hasNext: boolean }
```

- `nextCursor` 为 `null` / `hasNext` 为 `false` = 末页。
- **没有 `count` 字段**，`items.length` 只是本页条数，不是全量匹配数。
- 无 `limit` 参数；页大小由服务端决定，agent 不能指定（`mcp__moka-go__candidate_search` / `mcp__moka-go__interview_search`
  例外，可传 `limit` 1–20，默认 10）。
- `mcp__moka-go__user_list` 是不分页的 `{ items }`；`mcp__moka-go__pipeline_get_default.stages` 是完整数组。
- `mcp__moka-go__candidate_get` 的 `experiences` / `applications.transitions` 等分段是**裸数组**（按候选人整取的
  子集合，天然全量，不套分页封套）；`mcp__moka-go__candidate_get` 自身返回 `{ summary, data, meta }` 外壳。

### 成功返回

`structuredContent` 与 `content` 里的 JSON 文本同源：能拿到 `structuredContent` 就读它，拿不到（有的宿主只把文本交给模型）就解析文本。带卡片的工具在 agent-server 里可能只给模型一段摘要（例如「需要人工确认：……确认由页面完成」），这时按摘要行事：请用户在卡片上确认，不要重复调用。实体详情直接在载荷根部，
不自动包装为 `{ candidate }` 或 `{ application }`。
MCP 投影递归剥掉 `orgId`；不能照抄 REST 读模型。`createdByName`、`operatorName` 等姓名可为 `null`。

### 错误：`isError` + `structuredContent`，不是文本 JSON

业务错误一律 `isError: true` 返回（不 throw）。机读载体是：

```
structuredContent: { code, retryable, nextAction, retryAfterSeconds?, details? }
content: [{ type: "text", text: <中文 message> }]
```

- 按 `nextAction` 决定恢复方式，`code` 判断具体原因，`details` 可能带冲突字段等补充。
- `retryable: true` 不表示可以直接重放；限流等待秒数在顶层 `retryAfterSeconds`。
- `content[].text` 是中文错误信息；面向 HR 按业务含义转述。
- SDK 入参校验失败可能只有 `isError` 和文本，没有 `structuredContent`；按实际 schema 修正参数。

| nextAction | 处理 |
| --- | --- |
| `retry_same_request` | 按 `retryAfterSeconds` 等待后原样重试 |
| `check_state_then_decide` | 先查是否已生效；查不清就报告结果未知，不重放外呼、通知等副作用 |
| `fix_request` | 修正参数后再调用 |
| `reauthenticate` / `request_access` | 重新认证 / 由有权限者处理 |
| `resolve_conflict` | 读取冲突对象，确定目标后再决定 |
| `escalate` / `none` | 交由排查 / 不自动恢复 |

### 时间：墙钟字符串（北京时间），不是 epoch 数字

**绝对时间点使用 `"YYYY-MM-DD HH:mm"` 格式的北京时间（UTC+8，分钟粒度）**，
例如 `"2026-09-18 14:00"`。包括 `scheduledAt`、`interview.candidateOptionTime[]` /
`interviewerOptionTime[]`、`availability.startTime` / `endTime`、`mcp__moka-go__call_create.slots[]` /
`availabilityQuery.from|to`，以及所有 `createdAt` / `archivedAt` / `callbackedAt` /
`processedAt` / `expiresAt`。

- 输入已经是北京时间时直接传入；其他时区先换算并复述，不传 epoch、时区后缀或秒。
- 时间段为 `{ startTime: "2026-09-18 14:00", endTime: "2026-09-18 15:00" }`，不是单个字符串。
- 出生日期仍为 `YYYY-MM-DD`，经历年月为 `YYYY-MM`；它们不是绝对时间点。
- 系统不存租户时区、也没有时区工具：中国业务单时区，北京时间即业务时间。
- 例外：`mcp__moka-go__candidate_get` 的 `engagements[].conversation[].timestamp` 是**通话内相对毫秒**
  （如 `8200` = 通话 8.2 秒），不是时刻，原样保留；`duration` 是秒数。

### id：字符串化的 BIGINT

不是 UUID，形如 `"12"`。只能来自某次 `*_list` / `*_get` / 创建类工具返回，猜不出来。

### 幂等与恢复

见文末「幂等性」。相同字段值不等于无副作用；改期会重发通知，解析重放也不能当作刷新经历。

### 无 Org / 时区工具

系统**没有** `get_org`、没有租户时区字段。中国业务单时区：时间字段就是北京时间墙钟串，
直接展示即可，不要向用户声称"系统时区"。

---

## 工具清单

### 职位（job）

| 工具 | 入参 | 返回 | 备注 |
|---|---|---|---|
| `mcp__moka-go__job_list` | `cursor?` | 分页 `Job[]` | **无关键词过滤**，按 title 自行匹配 |
| `mcp__moka-go__job_get` | `jobId` | `Job` | |
| `mcp__moka-go__job_upsert` | `jobId`? + `title`? / `locations`? / `description`? / `status`? + `hireMode`? / `experience`? / `education`? / `minSalaryK`? / `maxSalaryK`? / `payPeriod`? / `headcount`? / `clear`? | `{ summary, data, meta }`，data 是 `Job` | 不传 `jobId`=新建（`title` 与 `locations` 必填，**不幂等**）；传了=部分更新（未传不动，幂等）。`locations` 用名称 `[{province?, city, area?, address?}]`，城市必填、不要写进标题；用户没说城市先问。调用即执行：停招 `status: "closed"` 直接生效、可再改回 `"open"`，调用前先把后果告诉用户并取得明确同意；`description` 不能传空串清空；清空经验、学历、月薪、几薪、人数只能把字段名放进 `clear`（如 `"clear":["minSalaryK","maxSalaryK"]`），这六个字段不收 `null`，同一字段既传值又在 `clear` 里报 `VALIDATION_FAILED` |

`Job` = `{ id, title, description: string\|null, status: "open"\|"closed", createdByUserId, createdByName, locations: string[], hireMode, experience, education, minSalaryK, maxSalaryK, payPeriod, headcount, createdAt }`；地点是 `浙江省 · 杭州市 · 西湖区` 这样的可读串，不含代码。

**没有**按关键词搜岗位的入口（`mcp__moka-go__job_list` 只支持游标分页）；标题匹配要自己拉全量。

### 候选人（candidate）

| 工具 | 入参 | 返回 | 备注 |
|---|---|---|---|
| `mcp__moka-go__candidate_search` | `query`? / `jobId`?（+`stageId`?）/ `filters`?(city/skills/minYears/companies/degree/excludeArchived) 至少一个、`limit`?(1–20 默认 10)、`detail`?(`brief`默认/`full`)、`cursor?` | `{ summary, items, meta }` | **关键词字面匹配**（姓名/技能/摘要），不是语义理解；`minYears` 建在年限自由文本上（近似口径，读不出数字的不命中）；传 `jobId` 时项内另带 `applicationId` 与 `currentStageId` |
| `mcp__moka-go__candidate_get` | `candidateId`、`sections`?(默认 `["profile"]`)、`jobId`?、`detail`?(`brief`默认/`full`) | `{ summary, data, meta }` | 分段取数：profile / experiences / applications / interviews / engagements / ingestions；`jobId` 收窄到该职位；`full` 才给经历描述与通话转写（并带 `textTrust` 不可信标记）；`null` 表示确实没有，不是没取到 |
| `mcp__moka-go__candidate_create` | `name`? / `phone`? / `email`? / `source`? / `resumeFileId`? | `{ candidate, duplicateOf }` | **手工建档只落基本联系字段**；不幂等 |
| `mcp__moka-go__candidate_from_resume` | `fileId` | `{ candidate, experiences: CandidateExperience[], duplicateOf }` | 同 fileId 重放返回已有档案；不同文件仍可能另建 |
| `mcp__moka-go__candidate_ingest_status` | `fileId` | `{ fileId, ingested, candidateId, candidateName }` | 未建档时 id/name 为 null；不反映上传状态或经历完整性 |
| `mcp__moka-go__candidate_update` | `candidateId` + 档案字段、`source`?、`resumeFileId`? | `Candidate` | 未传不动；name/phone/email/resumeFileId 不接受空串，birthDate 须日期格式，其余文本按 schema 可传空串 |
| `mcp__moka-go__candidate_set_archived` | `candidateId`、`archived` | `Candidate` | 幂等；`archived: true` 归档、`false` 取消归档 |
| `mcp__moka-go__candidate_intake` | `jobId`? | `{ summary, data }`（界面操作说明 + `jobId` 回显） | 只打开候选人录入界面，不写数据；真正建档由用户在界面触发 `mcp__moka-go__candidate_from_resume` / `mcp__moka-go__candidate_create`；无界面能力的客户端会收到同一句操作说明文本 |

`Candidate` 15 个信息列：`name`(≤128)、`phone`(≤32)、`email`(≤128)、`gender`(≤32)、`birthDate`
(`YYYY-MM-DD`)、`location`(≤128)、`wechat`(≤64)、`personalUrl`(≤512)、`highestDegree`(≤32)、
`yearsOfExperienceText`(≤32，**文本非数字**)、`expectedSalary`(≤64)、`skills`、`awards`、`certificates`、
`summary`；另 `source`(`manual`/`mail_in`/`ai_sourcing`)、`resumeFileId`、`archived`、`archivedAt`、`createdAt`。

`CandidateExperience` = `{ kind: "education"|"work"|"internship"|"project", organization, title, major,
degree, location, description, startDate: "YYYY-MM", endDate: "YYYY-MM"|null }`（除 kind 外均可空）。

MCP 没有删除候选人的工具；需要其他入口时先核实其能力。手工建档（`mcp__moka-go__candidate_create`）只收 name/phone/email/
source/resumeFileId 五项，学历、年限、期望薪资等要用 `mcp__moka-go__candidate_update` 补，或直接走简历解析。
**经历仍然只能由简历解析写入**：`mcp__moka-go__candidate_update` 不含 `experiences`，没有单条经历工具。

### 投递（application）

| 工具 | 入参 | 返回 | 备注 |
|---|---|---|---|
| `mcp__moka-go__application_create` | `jobId`、`candidateId` | `Application` | 重复投递**报错** `APPLICATION_ALREADY_EXISTS`，不幂等 |
| `mcp__moka-go__application_transition` | `applicationId`、`toStageId`、`reason`?(1–256) | `Application` | 阶段是**实体**、要 id 不要枚举名；终态吸收 |

`Application` = `{ id, jobId, candidateId, currentStageId, status: "in_progress"|"hired"|"rejected", createdAt }`

`StageTransition` = `{ id, applicationId, fromStageId, toStageId, operatorId, operatorName, reason, createdAt }`。
**投递的读口只有 `mcp__moka-go__candidate_get`**（`sections: ["applications"]`，`detail: "full"` 时每个投递项带
`transitions` 裸数组）；按职位列某阶段的候选人用 `mcp__moka-go__candidate_search`（传 `jobId`，可再传 `stageId`）。

MCP 没有归档投递的工具。
`currentStageId` 是 id，要拿阶段名必须先 `mcp__moka-go__pipeline_get_default`（阶段随流程一并返回）；阶段与 id 固定不变，一次对话查一次即可复用。

### 阶段与流程（pipeline）

| 工具 | 入参 | 返回 |
|---|---|---|
| `mcp__moka-go__pipeline_get_default` | — | `{ pipeline, stages: Stage[] }`（默认流程 + 按 seq 有序的阶段） |

MVP 恒一份默认流程：`mcp__moka-go__pipeline_get_default` 同时覆盖原 `pipeline_list`（列表）与 `stage_list`
（按 pipelineId 取阶段）的能力——阶段就在返回里，不需要再多一次调用。

`Stage` = `{ id, pipelineId, name, seq, createdAt }`。默认阶段名：
**新申请 / 初筛 / 面试 / Offer / 已入职 / 已淘汰**。`已入职` → `status=hired`，`已淘汰` → `status=rejected`，
其余 → `in_progress`。

### 面试（interview）

| 工具 | 入参 | 返回 | 备注 |
|---|---|---|---|
| `mcp__moka-go__interview_create` | `applicationId`、`interviewerId`? \| `interviewerName`?（至少其一、**单个**面试官）、`scheduledAt`?（`"YYYY-MM-DD HH:mm"` 北京时间）、`candidateOptionTime`?、`interviewerOptionTime`?、`location`?、`interviewLink`?（http/https）、`overrideAvailability`? | `{ interview, availabilityConflicts: TimeSlot[] }` | 自动前向推进到面试阶段并尝试通知；`round` 服务端派生 |
| `mcp__moka-go__interview_reschedule` | `interviewId` + `scheduledAt`? / `candidateOptionTime`? / `interviewerOptionTime`? / `location`? / `interviewLink`? / `overrideAvailability`? | `{ interview, availabilityConflicts }` | 部分更新，自动尝试改期通知；相同参数也可能重发 |
| `mcp__moka-go__interview_cancel` | `interviewId` | `Interview`（`result: "cancelled"`） | 终态不可逆；尝试取消通知，不回退投递阶段 |
| `mcp__moka-go__interview_submit_result` | `interviewId`、`result: "pass"\|"fail"`、`feedback`? | `Interview` | **fail 自动把投递流转到「已淘汰」** |
| `mcp__moka-go__interview_notify` | `interviewId` | `NotifyResult[]` 裸数组 | 逐路触达；与 REST 的 `{ results }` 不同 |
| `mcp__moka-go__interview_availability_list` | `interviewerId`、`cursor?` | `{ items: AvailabilitySlot[], nextCursor, hasNext }` | 面试官不可约时段，须翻页 |

`Interview` = `{ id, applicationId, candidateId, stageId, round, interviewerId, interviewerName,
candidateOptionTime, interviewerOptionTime, scheduledAt, result: "pending"|"pass"|"fail"|"cancelled",
feedback, location, interviewLink, createdAt }`

`NotifyResult` = `{ target: "candidate"|"interviewer", channel: "sms"|"email"|"agent_hint",
outcome: "sent"|"failed"|"skipped"|"hint", messageId, content, error }`

**没有** `title` / `endsAt`（只有开始时刻与可选时段）与面试官冲突 / 同投递重复排期检测——
冲突只有 `availabilityConflicts` 软提示，可被 `overrideAvailability` 静默放行。
该提示在写入后返回；不能为确认冲突再次创建面试。
创建、改期、取消均在保存后 best-effort 发送通知，返回不含通知结果；不要自动追加通知调用。
当前改期的 `idempotentHint` 与实现不符。
`AvailabilitySlot` 含 `id`、`interviewerId`、`kind: "blocked"`、`startTime`、`endTime`、`note`、`createdAt`。

#### 待办与面试查询

| 工具 | 入参 | 返回 | 备注 |
|---|---|---|---|
| `mcp__moka-go__interview_search` | `bucket`?（`unscheduled` / `upcoming` / `pending` / `done`，多选 OR）、`scheduledFrom`? / `scheduledTo`?（`"YYYY-MM-DD HH:mm"` 北京时间，左闭右开、可只给一侧）、`interviewerId`? / `candidateId`? / `applicationId`?、`q`?（候选人姓名或职位标题）、`limit`?(1–20 默认 10)、`cursor`? | `{ summary, items, buckets, meta }` | 跨候选人查面试；item 另带 `candidateName` / `jobTitle` / `jobId`；按排期时间升序，未定时间的排最后 |
| `mcp__moka-go__todo_summary` | — | `{ summary, data, meta }` | 与网页首页「今天要做」卡同口径的五组：今日面试、待反馈、待筛选、待安排、Offer 待定；每组最多 5 条，`count` 是全组条数；范围是租户全部，不按本人过滤 |

### 成员（user）

| 工具 | 入参 | 返回 |
|---|---|---|
| `mcp__moka-go__user_list` | `keyword`?（名字/邮箱/手机号包含匹配） | `{ items: { uid, displayName, phone(脱敏), role: "ENTERPRISE_ADMIN"\|"MEMBER", createdAt }[] }` |
| `mcp__moka-go__user_create` | `name`(≤64)、`countryCode`?、`phone`、`email`?、`role`? | `OrgUser`（需管理员） |
| `mcp__moka-go__user_update` | `uid` + `name`? / `email`? / `role`?（至少一项） | `OrgUser`（需管理员，不能改手机号/区号） |
| `mcp__moka-go__auth_logout` | — | `{ revoked: boolean }`，撤销当前客户端授权；只在用户要求退出时调用 |

`mcp__moka-go__user_list` 返回的 `uid` 就是面试官的 `interviewerId`。**没有** `list_interviewers`；
`mcp__moka-go__user_list` 不返回"是否停用"标记。
`countryCode` 默认 `+86`，`role` 默认 `MEMBER`；`OrgUser` 不返回 email。

### 文件（file）

| 工具 | 入参 | 返回 |
|---|---|---|
| `mcp__moka-go__file_request_upload_token` | `fileName`(≤256)、`mimeType`、`maxBytes`(>0)、`bizType`?(简历传 `resume`) | `{ fileId, uploadUrl, expiresAt, credentials? }` |
| `mcp__moka-go__file_commit_upload` | `fileId` | `File`（`status` 转 `uploaded`） |
| `mcp__moka-go__file_get` | `fileId` | 文件实体（status、fileName、sizeBytes 等），不返回下载地址或文件内容 |

`credentials` 仅 real OSS 部署有（STS 临时凭证）；mock/local 直接向 `uploadUrl` PUT。
**未 commit 的 pending 文件不可用于简历解析。**

### AI 外呼（call）

| 工具 | 入参 | 返回 |
|---|---|---|
| `mcp__moka-go__call_create` | `applicationId`、`templateId`?、`templateVars`?、`availabilityQuery`?、`slots`? | `{ aiCallId, externalTaskId }` |

调用即执行、不可撤回：先把「真实拨号、会产生费用、通话会被录音与转写」告诉用户并取得明确同意。

外呼的读口只有 `mcp__moka-go__candidate_get`（`sections: ["engagements"]`，`detail: "full"` 时项内带
`conversation` 转写与 `textTrust` 不可信标记）。

`AiCall.status` = `initiated`（待拨）/ `success` / `fail` / `manual_stop`。
`slots` 与 `availabilityQuery` 二选一，**都缺 / 都算不出窗口 → `CALL_NO_AVAILABLE_SLOTS`（422）**。
同时传时优先 `slots`。`availabilityQuery` 是 `{ interviewerUserId, from, to }`；
`slots` 是时间段对象数组。`templateVars` 为键值对象，例如 `{ "name": "张三", "jobTitle": "后端工程师" }`。

### 招聘邮箱（mail）

邮箱账号配置与邮箱进简历。配置需要真实邮箱连接信息；`password` 写入后不回显。

| 工具 | 入参 | 返回 | 注意点 |
|---|---|---|---|
| `mcp__moka-go__mail_inbox_create` | `email`、`password`、`mailServer`、`port`?（默认 143，IMAP+TLS 常用 993）、`tls`?（默认 false）、`protocol`?（IMAP/POP3/EXCHANGE，默认 IMAP）、`username`?、`enablePermission`?、`exchangeAuthorizationType`?、`exchangeIgnoreSslError`? | 配置行数组（每 box 一行，不含 password） | 先经外部服务验连通性再落库；落库后 BM 开始按 box 抓取，非即时；自由格式简历处理恒开 |
| `mcp__moka-go__mail_inbox_update` | `id` + 连接参数（`email`? / `password`? / `mailServer`? / `box`? / `port`? / `tls`? / `protocol`? / `username`? / `enableFlag`? / `enablePermission`? / `exchangeAuthorizationType`? / `exchangeIgnoreSslError`?） | 更新后的配置行（不含 password） | 只改这一个 box 行，未传字段不动 |
| `mcp__moka-go__mail_inbox_delete` | `email` | `{ deletedEmail }` | 删该邮箱全部 box 行，BM 停止抓取；可逆（重新配置即恢复）；调用即执行，无确认码 |
| `mcp__moka-go__mail_application_list` | `cursor`? | `{ items, nextCursor, hasNext }` | 邮箱进简历记录；status 为 `received` / `processed` / `failed`；空结果先确认邮箱已配置、抓取可能还没完成 |
| `mcp__moka-go__mail_application_to_candidate` | `mailApplicationId` | `{ candidateId, duplicateOf, alreadyProcessed }` | 按记录幂等：`processed` 直接回既有候选人，`failed` 可重试；只建候选人不建投递，投递用 `mcp__moka-go__application_create`；缺简历文件报错 |

### AI 寻聘（sourcing）

寻聘只有四个对象：**渠道**（一个 HR 在 Boss / 猎聘上的插件与账号）、**任务**（一个职位在一个渠道上）、
**画像**（职位级，两个渠道共用）与**记录 / 简历**。13 个工具按「对象 + 动词」命名。先记住三条规则，
下面所有剧本都按它走：

- **设置和执行分开，设置只有一个写入口**：任务级设置（做什么、每天几个、几点结束、绑定哪个渠道职位）
  只用 `mcp__moka-go__sourcing_task_update`；发布信息（薪资 / 经验 / 学历 / 地点）是职位信息，用 `mcp__moka-go__job_upsert` 补；
  职位级画像与沟通指令只用 `mcp__moka-go__sourcing_profile_update`。
  `mcp__moka-go__sourcing_task_start` 只带 `intent`，不带任何设置，也不替用户改设置。
- **`mcp__moka-go__sourcing_task_start` 调用即执行，体检不通过就不开**：一次调用就按任务上存好的设置打开任务；
  没准备好报 `SOURCING_BOT_TASK_NOT_READY`（发布类 `SOURCING_BOT_PUBLISH_NOT_READY`），
  `details.blockers` 每条带 `code / message / fix`，**下一步照 `fix` 做**，不要在对话里另编一套。
  调用前把「每天自动触达、耗额度、收不回」等后果告诉用户并取得明确同意。
- **`accountStatus=unknown` 不等于没登录**：它表示插件还没确认过登录，或上次打开渠道时发现掉线、在等扫码；
  插件下次打开渠道才更新。别因此让用户重新登录，先看同一条里的 `pluginStatus` 与 `hold`。

#### 只找人

1. `mcp__moka-go__job_list` 拿职位 id（`jobId` 是 ATS 职位 id，不是渠道职位 id）。
2. `mcp__moka-go__sourcing_task_update{channel, jobId, actions:["greet","collect"], dailyGreet:20}` 建任务。
   返回的 `readiness.find` 告诉你能不能开，也带匹配预判（`match_auto` / `match_ambiguous` / `match_none` 等）；
   要单独看 `channelJob.match` 用 `mcp__moka-go__sourcing_task_get`。
3. 把渠道、职位、动作、每天几个、结束时间、副作用转述给用户并取得明确同意，再调
   `mcp__moka-go__sourcing_task_start{channel, jobIds:[jobId], intent:"find"}`（调用即执行）。执行结果的 `items` 里
   单个职位失败会带 `error`，把原因转述给用户，不要整次重试。

如果 `readiness.find.blockers` 不为空，先按每条 `fix` 补齐再开；`warnings` 不拦，但要把要紧的（如画像为空、
今天次数已用完明天接着跑）告诉用户。

#### 只发布 / 发布后找人

1. `mcp__moka-go__job_list` 拿职位 id。
2. `mcp__moka-go__sourcing_channel_list{channel}` 看 `mirror.syncedAt / mirror.fresh`。发布前镜像必须新鲜：
   `fresh:false`（超过 24 小时或从没同步过）先 `mcp__moka-go__sourcing_channel_sync{channel}`。
3. `mcp__moka-go__sourcing_channel_sync` 只派一轮同步，结果不随本次返回。**隔 1–3 分钟**再调 `mcp__moka-go__sourcing_channel_list`，
   看 `mirror.syncedAt` 是否更新；一直不更新就让用户看插件，别带着旧镜像硬开。
4. 先确认职位信息齐全（薪资 / 经验 / 学历 / 地点）：缺什么用 `mcp__moka-go__job_upsert{jobId, …}` 补。
   只发布就把 `actions` 设成 `[]`（用 `mcp__moka-go__sourcing_task_update{channel, jobId, actions:[]}`）；
   发布后要找人则同时带 `actions` 与 `dailyGreet`（例如 `actions:["greet","collect"], dailyGreet:20`）。
   任务开着时不能把 `actions` 清空（`SOURCING_BOT_TASK_STATE_CONFLICT`，`details.reason=actions_required_while_on`）；
   先把任务停掉再改，或改用 `publish_then_find`。
5. `mcp__moka-go__sourcing_task_start{channel, jobIds:[jobId], intent:"publish"}`（只发布）或
   `intent:"publish_then_find"`（发布、过审后找人）。发布类 `jobIds` 只能一个。预览会列发布字段；
   缺字段、Boss 档位不对、已发布、渠道有同名候选都在预览阶段报错。
6. 用户同意后带码执行。发布类会在渠道生成真实职位，下线要去渠道手动做，Boss 可能耗发布权益。

`publish_then_find` 的预览会同时列「发布字段 + 过审后每天几个」，一次确认覆盖两件事。

#### 渠道里已经有同名职位

看 `readiness.find` 的 blocker / warning（`match_ambiguous` / `match_none` / `match_unknown` / `match_auto`），
或 `mcp__moka-go__sourcing_task_get` 的 `channelJob.match`（bound / auto_match / ambiguous / no_match / unknown）：

- `bound` / `auto_match`：已经对应上，直接 `intent:"find"` 开。
- `ambiguous`：`candidates` 有多条。**把候选职位名给用户选**，再用
  `mcp__moka-go__sourcing_task_update{channel, jobId, channelJobId}` 绑定。别自己挑一个。
- `no_match` / `unknown`：按 blocker 的 `fix` 走（通常是先 `mcp__moka-go__sourcing_channel_sync` 再看，或走发布）。
- 如果误走了 `intent:"publish"`，预览会报 `bind_suggested`：渠道里已有同名职位，先绑定，不要重复发。

#### 改设置，不重启

- 每天几个、几点结束、动作、绑定渠道职位：`mcp__moka-go__sourcing_task_update{channel, jobId, …}`；
  发布信息用 `mcp__moka-go__job_upsert` 补职位。
  从下一轮生效，不打断正在跑的一轮；看返回的 `readiness` 就知道改完能不能开。
- 加画像要求、改沟通指令：`mcp__moka-go__sourcing_profile_update{jobId, must:[…]}`。默认 `mode:"append"`（追加），
  不会丢 HR 手写的内容；要整组替换才显式传 `mode:"replace"`，`[]` 清空该组。同一职位两个渠道共用一份。

#### 看进度 / 为什么停了

1. `mcp__moka-go__sourcing_task_list{channel}`：`summary` 给一句结论；每行看 `schedule.state` 与 `hold`。
2. 只看停住的：`mcp__moka-go__sourcing_task_list{channel, state:"held"}`。
3. 下钻一个任务：`mcp__moka-go__sourcing_task_get{channel, jobId}`，看 `channelJob.candidates`、`readiness`（find / publish
   各一份）与 `recentRounds`（最近 5 轮）定位原因。
4. 渠道级停住（这个渠道所有任务都跑不了）看 `mcp__moka-go__sourcing_channel_list` 的 `hold`；任务级停住看
   `task_list / task_get` 的 `hold`。两处的 `fix` 就是下一步。

#### 扫码 / 验证码处理完，接着跑

1. `mcp__moka-go__sourcing_channel_list{channel}` 看到 `hold.code` 是 `login_required`、`verify_timeout` 或 `window_closed`：
   把 `hold.detail` 转述给用户，请用户在插件弹出的渠道窗口里扫码或过验证码（MCP 代办不了）。
   是 `ai_insufficient_balance` 则请管理员充值，充完再 resume。
   是 `plugin_permission` 则是插件没开「允许运行用户脚本」（Edge 叫「允许用户脚本」）：按 `fix` 请用户在本机
   扩展管理页打开这个开关（MCP 代办不了），开好再 resume。
2. 用户处理完，调 `mcp__moka-go__sourcing_task_resume{channel}`，**只传 channel**（渠道级接着跑）。不要带 `jobId`，
   也不要用 `mcp__moka-go__sourcing_task_start`（那会重新走确认）。
3. 如果是某个任务自己停住（例如渠道职位没对上），先用 `mcp__moka-go__sourcing_task_get` 看原因，再
   `mcp__moka-go__sourcing_task_resume{channel, jobId}`；想让这个任务先跑，加 `front:true`。`front` 只能和 `jobId` 一起用。

#### 停止

- 停指定任务：`mcp__moka-go__sourcing_task_stop{channel, jobIds}`；停整个渠道：`mcp__moka-go__sourcing_task_stop{channel}`（不传 `jobIds`）。
- 渠道卡住停不下来：`mcp__moka-go__sourcing_task_stop{channel, force:true}`，渠道级、忽略 `jobIds`，清待执行指令并复位连接。
- 停住的任务要接着跑用 `mcp__moka-go__sourcing_task_resume`，不是 stop；停掉的任务要重新打开用 `mcp__moka-go__sourcing_task_start`。
  `force:false` 是异步的，返回只代表指令已下发，别轮询本工具。

**MCP 做不了、要回网页的事**：装插件与绑定（`/sourcing-bot/accounts`）、渠道扫码登录与过验证码（插件弹窗）、
渠道筛选条件（`/sourcing-bot/tasks`）；简历截图去 `/sourcing-bot/candidates`，逐步骤运行细节去
`/sourcing-bot/runs`。这些地址用 `mcp__moka-go__system_links` 的 `webUrl` 拼。

| 工具 | 入参 | 返回 | 注意点 |
|---|---|---|---|
| `mcp__moka-go__sourcing_channel_list` | `channel`? | `{ summary, items, meta }` | 入口工具。items 含 `status`、`channelUsername`、`accountStatus`、`pluginStatus`、`pluginLastSeenAt`、`lastLoginAt`、`activity{kind,jobName,startedAt}`、`hold{code,detail,since,fix}`、`quotaUsedUpToday`、`mirror{syncedAt,fresh,jobCount}`、`tasks{on,running,held}`；异常条目带 `guide`。`accountStatus=unknown` 不等于没登录 |
| `mcp__moka-go__sourcing_channel_sync` | `channel` | `{ summary, data: { requested, previousSyncedAt, checkAfterMinutes }, meta }` | 只派一轮同步，不等人；1–3 分钟后看 `mirror.syncedAt`。插件离线报 `SOURCING_BOT_PLUGIN_OFFLINE`；渠道忙 / 不在 7:00–22:00 报 `SOURCING_BOT_TASK_STATE_CONFLICT`（看 `details.reason` / `until`） |
| `mcp__moka-go__sourcing_task_list` | `channel`?、`state`?（running/queued/done_today/tomorrow/held/publishing/reviewing/collecting/published/off） | `{ summary, items, meta }` | 每行含 `id`、`jobId`、`jobName`、`schedule`、`today`、`quota`、`lastRun`、`hold`、`channelJob{name,match}`（bound/auto_match/ambiguous/no_match/unknown）；看「为什么停」用 `state:"held"` |
| `mcp__moka-go__sourcing_task_get` | `channel`、`jobId` | `{ summary, data, meta }` | 设置、排期、`channelJob`（含 `candidates`）、发布信息、画像全文、`readiness{find,publish}`、最近 5 轮；改设置前先看它 |
| `mcp__moka-go__sourcing_task_update` | `channel`、`jobId` + 至少一项 `actions`? / `dailyGreet`? / `dailyFavor`? / `endHour`? / `channelJobId`? | `{ summary, data: { settings, channelJob, publish, schedule, readiness }, meta }` | 任务级设置唯一写入口；不开始、不打断正在跑的，从下一轮生效；`actions:[]` = 只发布；`channelJobId:""`（空串）解绑，不收 `null`；同参幂等；`publish` 已下线，发布信息用 `mcp__moka-go__job_upsert`（传了会拒收并提示） |
| `mcp__moka-go__sourcing_profile_update` | `jobId` + `mode`?（append 默认 / replace）、`must`? / `bonus`? / `exclude`?（每组 ≤50 条）、`chatInstruction`? | `{ summary, data: { jobId, mode, updated, profileItems, chatInstructionChars }, meta }` | 条目是扁平对象：文本 `{"kind":"text","text":"…"}`（`kind` 缺省为 text），条件 `{"kind":"condition","condition":{"name":"学历","condition":"gte","value":["本科"]}}`；`text` / `condition` 只能出现与 `kind` 对应的那一个，缺或多报 `VALIDATION_FAILED`。职位级画像唯一写入口；默认追加，不覆盖 HR 手写内容；`replace` 整组替换；两个渠道共用；职位要先在某个渠道有任务 |
| `mcp__moka-go__sourcing_task_start` | `channel`、`jobIds`(1–20；发布类只能一个)、`intent`?(find 默认 / publish / publish_then_find) | `data.items[{jobId,ok,schedule\|error}]`；已开着直接回 `alreadyOn` | 调用即执行；只带 `intent`，不写设置；体检不通过就不开；`publish` 但任务上存着找人动作会报 `find_actions_set`；开着就每天 7:00–22:00 自动触达、耗当日额度，发出去收不回；调用即视为同意授权声明 |
| `mcp__moka-go__sourcing_task_stop` | `channel`、`jobIds`?(1–20)、`force`? | `{ summary, data: { ok, force, items }, meta }` | 不传 `jobIds` = 渠道全停；`force:true` 强停（渠道级、忽略 jobIds、清待执行指令并复位、幂等）；`force:false` 异步，返回只代表指令已下发 |
| `mcp__moka-go__sourcing_task_resume` | `channel`、`jobId`?、`front`? | `{ summary, data: { ok, channel, front, items }, meta }` | 渠道级只传 `channel`；`front` 只能配 `jobId`；不开始新任务、不改设置；停掉的任务要重开用 `mcp__moka-go__sourcing_task_start` |
| `mcp__moka-go__sourcing_record_search` | `kind`? / `channel`? / `taskId`? / `jobId`? / `name`? / `cursor`? | `{ summary, items, meta }` | 记录新的在前，每页最多 50 条；`meta.total` 是本页条数不是全量；不看会话、不给截图 |
| `mcp__moka-go__sourcing_record_get` | `recordId` | `{ summary, data, meta }` | AI 报告全文；`communicated` 记录另带 `session.messages`（`sentAt`）；他人记录按 404 |
| `mcp__moka-go__sourcing_record_feedback` | `recordId`、`type`(`like`/`dislike`)、`content`?(≤2000) | `{ summary, data: { recordId, type }, meta }` | 覆盖写（改判语义，幂等）；不改 AI 评分与结论 |
| `mcp__moka-go__sourcing_resume_search` | `q`?(≤200 字) / `jobId`? / `cursor`? | `{ summary, items, meta }` | 插件上传的渠道简历库；中文 bigram 字面匹配、不是语义检索；`name` 是渠道脱敏称呼 |

### 用户任务（user-task）

| 工具 | 入参 | 返回 |
|---|---|---|
| `mcp__moka-go__user_task_wait` | `timeoutSeconds`?（1–300，默认 60）、`ackTaskIds`?（上一批已处理完的 id） | `{ summary, data: { tasks, timedOut, acknowledged, waitAvailable }, meta }` |

`mcp__moka-go__user_task_wait` 是**等待原语**：没有待办就在服务端阻塞等新信号（客户端不用自己 sleep 轮询），
回来时把上一批处理完的 id 放进 `ackTaskIds` 一并确认。「确认上一批 + 等下一批」一次调用完成。
`timedOut: true` 是正常结果（这段时间没有新信号），继续调用继续等；`waitAvailable: false` 说明
服务端等待能力不可用，本次只做了一次查询，别把它读成「确实没有任务」。

`UserTask` = `{ id, taskType, channel, status, refs: {type,id}[]\|null, payloadJson, ... }`。
外呼完成后 `refs` 里有 `{type:"ai_call", id: aiCallId}`（带类型的引用，不必猜下标）。

### 平台（platform）

| 工具 | 入参 | 返回 |
|---|---|---|
| `mcp__moka-go__system_links` | — | `{ webUrl, mcpUrl }` |

`mcp__moka-go__system_links` 返回网页端入口与 MCP 端点（由部署配置 `PUBLIC_URL` 派生，同部署所有租户一致）。
要给用户一个浏览器可打开的网址（登录、看职位/候选人/面试，或寻聘的网页操作页）时调用它，
不要凭记忆拼域名；它只给站点级入口，不给具体页面深链。

---

## 常见错误（具体恢复方式以 nextAction 为准）

| code | 触发场景 | 正确反应 |
|---|---|---|
| `VALIDATION_FAILED` | 业务输入校验失败；SDK 校验可能仅返回文本 | 修正参数，不原样重试 |
| `NOT_FOUND` | id 不存在**或跨租户**（语义就是"不存在"，不是 403） | 重新 search/list 定位，不要重试 |
| `AUTH_REQUIRED` | 未认证 / 凭证失效 | 停下，让用户重新登录 |
| `ACCESS_DENIED` | 已认证但无该资源权限（如非管理员建成员） | 停下，说明需要管理员操作 |
| `CURSOR_INVALID` | 游标非法 | 从首页重新开始 |
| `RATE_LIMITED` | 工具级限流（租户 × 工具，按分钟） | 按 retryAfterSeconds 等待后重试 |
| `APPLICATION_ALREADY_EXISTS` | 同 `(jobId, candidateId)` 已有投递 | 用 `mcp__moka-go__candidate_search({ jobId })` 拿已有那条，别重试 |
| `APPLICATION_INVALID_TRANSITION` | 终态投递再流转，或目标阶段非法 | 读现状，别重试 |
| `INTERVIEW_APPLICATION_TERMINAL` | 对已 hired/rejected 的投递排面试 | 停下说明投递已终态 |
| `INTERVIEW_RESULT_FINALIZED` | 面试结果已定案后再提交 | 读现状，别重试 |
| `RESUME_UNPARSEABLE` | 简历读不出内容 / 格式不支持 / 损坏 | 提示换文件或用 mcp__moka-go__candidate_create 手工建档 |
| `CALL_CANDIDATE_PROFILE_INCOMPLETE` | 候选人缺手机号或姓名，无法外呼 | 按用户提供的信息 mcp__moka-go__candidate_update 补档案 |
| `CALL_NO_AVAILABLE_SLOTS` | 算不出非空可约时段 | 改传时段或先登记可用时间 |
| `SOURCING_BOT_TASK_NOT_READY` | 开任务找人前体检不过（没设动作、匹配不上、配额为 0 等） | 读 `details.blockers` 每条的 `fix` 补齐，再重新预览；不要原样重试 |
| `SOURCING_BOT_PUBLISH_NOT_READY` | 发布体检不过（缺字段、Boss 档位不对、已发布、有同名候选、镜像过期） | 同上按 `fix`；镜像过期先 `mcp__moka-go__sourcing_channel_sync`，别硬开 |
| `SOURCING_BOT_PLUGIN_OFFLINE` | 插件不在线，同步 / 核对没人执行 | 让用户到「账号与连接」检查插件并开着 Chrome；Agent 修不了 |
| `SOURCING_BOT_TASK_STATE_CONFLICT` | 渠道在跑别的、不在运行时段，或任务开着时要清空动作 | 看 `details.reason`（`channel_busy` / `outside_window` / `actions_required_while_on`）后再决定，不原样重试 |
| `SPI_TIMEOUT` | 外部服务超时 | 先查状态再决定，不能直接重放写操作 |
| `SPI_UPSTREAM_FAILED` | 外部服务业务失败 | 不可重试 |
| `PHONE_ALREADY_EXISTS` / `EMAIL_ALREADY_EXISTS` | 建成员时唯一性冲突 | 换值或告知用户已存在 |
| `INTERNAL_ERROR` | 未归类异常（不泄漏内部细节） | 停下告知，不要重试 |

---

## 幂等性

| 工具 | 重复调用行为 |
|---|---|
| `mcp__moka-go__candidate_set_archived` | 幂等，两个方向都返回同一候选人（不刷新 `archivedAt`） |
| `mcp__moka-go__user_task_wait`（`ackTaskIds`） | 幂等：已 done 的任务再确认不报错，仍计入 `acknowledged` |
| `mcp__moka-go__file_commit_upload` | 幂等（重复 commit 返回同一文件） |
| `mcp__moka-go__job_upsert`（更新路径） | 幂等（含 `status` 停招 / 重开；目标已是该状态再调仍返回该职位） |
| `mcp__moka-go__candidate_update` / `mcp__moka-go__user_update` | 到同一字段值结果一致（未传字段保持原值） |
| `mcp__moka-go__interview_reschedule` | 字段值可相同，但每次会尝试发送通知，不能自动重放 |
| `mcp__moka-go__candidate_from_resume` | 同 fileId 顺序重放返回既有档案；同实例并发合并，跨实例及部分失败限制见下文；duplicateOf 只提示不同文件命中同一人 |
| `mcp__moka-go__candidate_create` | **不幂等**：同邮箱/手机号会再建一条，靠 `duplicateOf` 提示 |
| `mcp__moka-go__job_upsert`（新建路径） | **不幂等**：无唯一约束，重复产生同名岗位 |
| `mcp__moka-go__application_create` | **不幂等**：重复报 `APPLICATION_ALREADY_EXISTS` |
| `mcp__moka-go__interview_create` | **不幂等**：重复排产生两条面试记录（无重复排期检测） |
| `mcp__moka-go__application_transition` | 到同一 `toStageId` 结果一致，但会**追加一条流转历史** |
| `mcp__moka-go__interview_submit_result` / `mcp__moka-go__interview_cancel` | 已定案后再提交 / 取消报 `INTERVIEW_RESULT_FINALIZED` |

网络 / 未知错误先查状态，按 nextAction 决定。fileId 重放目前只保证顺序调用与同实例并发，
没有数据库唯一约束保障跨实例竞争；候选人与经历也未在同一事务写入。
`mcp__moka-go__candidate_ingest_status.ingested: true` 不代表经历完整，不靠重复上传修复。

---

## 校验缺口（服务端没兜，agent 自己兜）

| 缺口 | 后果 | 兜法 |
|---|---|---|
| 无面试官冲突 / 重复排期检测 | 同一时段可排出两场，只有 `availabilityConflicts` 软提示 | 排期前 `mcp__moka-go__candidate_get` 的 `interviews` 段 + `mcp__moka-go__interview_availability_list` 自查，冲突时先问用户 |
| `mcp__moka-go__job_list` 无关键词过滤 | "按名字找岗位"要自己拉全量匹配 | 翻页到底再匹配，别只匹配首页；`hasNext` 未翻页就下"没有"的结论是错的 |
| `mcp__moka-go__candidate_search` 是关键词匹配，不是语义理解 | 整句自然语言（"杭州的 Java 后端，5 年以上"）不会命中 | 拆成 `query` 关键词 + `filters`（city/skills/minYears）；`minYears` 是近似口径，读不出数字的年限一律不命中 |
| 不同文件可能属于同一个人 | 不同 fileId 仍可能新建候选人 | 按联系方式查重，duplicateOf 非空时说明未自动合并 |
| 终态不可回退 | `rejected`/`hired` 投递再也流转不了 | 别计划"恢复"；只能新建投递（同 job+candidate 会被 uk 拦住，实际做不到 → 停下说明） |
| `mcp__moka-go__interview_create` 自动推进阶段 | 阶段变化不体现在返回里 | 排完面试后 `mcp__moka-go__candidate_get` 的 `applications` 段回读 `currentStageId` 确认 |
| `mcp__moka-go__candidate_update` 不接受 `experiences` | 经历无法经 MCP 手工修改 | 同文件重放不会更新经历，说明限制并核实其他入口能力 |
| 面试排期冲突只是软提示 | 冲突不阻断创建 / 改期 | 告知已保存与冲突，用户要调整时修改原场次，不重复创建 |
| `description` / 多数文本字段最小长度 1 | 传空串会被 schema 拒绝，不是“清空” | 不传即不动；清空职位的经验 / 学历 / 薪资 / 几薪 / 人数用 `mcp__moka-go__job_upsert` 的 `clear`，解绑渠道职位传 `channelJobId:""`；其余清空只使用 schema 明确支持的字段 |
