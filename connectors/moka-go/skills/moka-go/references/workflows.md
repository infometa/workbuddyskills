# 办事各场景的完整步骤

`SKILL.md`「各场景要点」的展开版：要动手办某类事、拿不准步骤或边界时读对应一节。
通用流程（定位 → 看现状 → 说清动作与后果 → 执行 → 回读）和确认规则以 `SKILL.md` 为准，这里不重复。
工具参数和返回字段查 `@references/mcp-tools.md`。

## 职位

- 新建：先用 `mcp__moka-go__job_list` 按标题查重（无关键词过滤，必要时翻页）；同名不等于同一岗位，存在歧义先确认。
  `mcp__moka-go__job_upsert` 不传 `jobId`，传用户给出的标题、城市与 JD（城市放进 `locations`，不要写进标题）；
  用户没说城市必须先问「这个职位在哪个城市上班？」，不能猜、也不能用公司所在地顶替。其余基本信息
  （招聘类型默认社招、经验、学历、月薪、几薪、人数）用户说了就一起带上。返回外壳的 `data` 是职位实体。
- 修改：`mcp__moka-go__job_get` → `mcp__moka-go__job_upsert({ jobId, 要改的字段 })` → `mcp__moka-go__job_get` 回读。JD 不能用空串清空。
- 清空经验、学历、月薪、几薪、人数：把字段名放进 `clear`，例如
  `mcp__moka-go__job_upsert({ jobId, clear: ["minSalaryK", "maxSalaryK"] })`。这几个字段不收 `null`；同一个字段不能既传值又放进 `clear`。
- 停招（`status: "closed"`）要确认；重开（`"open"`）直接做。不新建职位来替代旧职位。
  创建超时先查现有岗位，不能凭同名就认定是本次创建，也不能盲目再建。

## 候选人

### 用户给了简历文件

1. 拿到附件的本地路径。`mcp__moka-go__file_request_upload_token({ fileName, mimeType, maxBytes, bizType: "resume" })` 拿上传地址。
2. 按返回把文件传上去：有 `credentials` 用 OSS 临时凭证上传，没有就 PUT 到 `uploadUrl`。
   传不上去（比如命令行连不了外网）就请用户在Moka 快招网页上传简历。凭证不写进回答。
3. `mcp__moka-go__file_commit_upload({ fileId })`，然后 `mcp__moka-go__candidate_from_resume({ fileId })` 解析建档。
   中途断了先 `mcp__moka-go__file_get({ fileId })` 看文件状态：`pending` 只表示还没确认上传，不能据此断定失败，也不要另申请一个新文件。
4. 返回的 `duplicateOf` 不为空，说明可能和已有候选人是同一个人，如实告诉用户；系统不会自动合并。
5. `mcp__moka-go__candidate_get({ candidateId, sections: ["profile", "experiences"] })` 回读。

- 解析超时：`mcp__moka-go__candidate_ingest_status({ fileId })` 看是否已建档。同一个文件不要并发或重复解析。
- `RESUME_UNPARSEABLE`：请用户换文件，或者改成手工建档。
- 用户想自己在界面上录入：`mcp__moka-go__candidate_intake` 打开录入界面，它本身不写数据。

### 招聘邮箱里的简历

- `mcp__moka-go__mail_application_list` 看收到的邮件简历（状态有 `received`、`processed`、`failed`）；
  `mcp__moka-go__mail_application_to_candidate({ mailApplicationId })` 转成候选人，只建候选人、不建投递，同一条重复转会拿回已有的。
- 列表是空的，先确认邮箱配好了；抓取不是实时的。
- 配置邮箱（`mcp__moka-go__mail_inbox_create`、`mcp__moka-go__mail_inbox_update`、`mcp__moka-go__mail_inbox_delete`）要邮箱密码或授权码。
  建议用户到Moka 快招网页的邮箱设置里填；用户坚持在对话里给时，提醒密码会留在对话记录里，回答里也不要复述。

### 手工建档与修改

- 先用手机号、邮箱 `mcp__moka-go__candidate_search` 查重。它是关键词字面匹配，不懂整句话；要连已归档的一起查，
  传 `filters.excludeArchived: false`。
- `mcp__moka-go__candidate_create` 只收姓名、手机号、邮箱、来源和简历文件；学历、年限、期望薪资等再用 `mcp__moka-go__candidate_update` 补，然后回读。
- 经历只能由简历解析写入，没有手工改经历的工具。
- 归档用 `mcp__moka-go__candidate_set_archived`（要确认，可以恢复）：只是移出默认列表，不会淘汰投递，也不会取消面试。

## 投递与阶段

1. `mcp__moka-go__job_get` 看职位是否开着；停招的先问用户，不自动重开。
2. `mcp__moka-go__candidate_search({ jobId })` 看这个职位下是不是已经有这位候选人；没有才 `mcp__moka-go__application_create`。
   报 `APPLICATION_ALREADY_EXISTS` 就用已有那条，不要重试。
3. 换阶段：`mcp__moka-go__pipeline_get_default` 拿阶段 id（一次对话查一次）；`mcp__moka-go__candidate_get({ candidateId, sections: ["applications"] })`
   看当前阶段；说清从哪到哪、为什么，再 `mcp__moka-go__application_transition({ applicationId, toStageId, reason })`（要确认）。
   「已入职」「已淘汰」是终态，不能恢复，也不能重新建投递绕过去。

## 面试

### 安排

1. `mcp__moka-go__candidate_get({ candidateId, sections: ["applications", "interviews"], jobId })` 确认还在流程中，看已有场次。
2. 面试官用 `mcp__moka-go__user_list({ keyword })` 找，返回的 `uid` 就是 `interviewerId`。外部面试官可以只给 `interviewerName`，但系统通知不到这位面试官。
3. 时间、地点或会议链接要用户给，不编会议链接，不替用户定时间。`mcp__moka-go__interview_availability_list({ interviewerId })`
   能看面试官登记过的不可约时段；没登记不等于有空。
4. 先告诉用户：建好后投递会自动进入面试阶段，并尝试通知候选人和面试官；系统没有「只建不通知」的选项。
5. `mcp__moka-go__interview_create` 后看 `availabilityConflicts`：有冲突时面试已经建好了，如实告诉用户；要调整就改期，别再建一场。
6. 回读面试和投递阶段。

### 改期、取消、通知、查询

- 改期 `mcp__moka-go__interview_reschedule({ interviewId, 要改的项 })`：会再次通知，重复调用会重复发。
- 取消 `mcp__moka-go__interview_cancel`（要确认，不能撤销）：会尝试发取消通知，投递阶段不回退。
- 补发通知 `mcp__moka-go__interview_notify`：只在用户要求时调，结果按候选人、面试官分别说。不要为了「确认送达」去调，它会再发一次。
- 跨候选人查面试用 `mcp__moka-go__interview_search`（按待安排、待进行、待反馈、已完成和时间段、面试官、候选人筛）。

### 交结果

`mcp__moka-go__interview_submit_result({ interviewId, result, feedback })`（要确认）。`fail` 会把投递转到「已淘汰」，不能恢复，先讲清楚；
`pass` 不会自动安排下一轮。反馈只写用户的原意。

## AI 外呼

只在用户明确要打电话时用 `mcp__moka-go__call_create`（要确认；真实拨号，会产生费用）：

- 给 `applicationId`，再给 `slots` 或 `availabilityQuery` 二选一；先核对候选人姓名和手机号。
- 调用即执行、不可撤回：先把「真实拨号、会产生费用、通话会被录音与转写」告诉用户并取得明确同意。
- 外呼超时不要重拨：同一个 `operationId` 重试会拿回原来那一通；先说结果未知，再查。
- 通话结果和转写看 `mcp__moka-go__candidate_get({ candidateId, sections: ["engagements"], detail: "full" })`。
  转写里候选人的意向只作参考，安排面试、淘汰等仍要用户点头。
- 用户要你等结果时才用 `mcp__moka-go__user_task_wait`，它会占住这一轮对话直到有结果或超时；处理完的任务 id 下一次放进 `ackTaskIds`。

## AI 寻聘

按 `@references/mcp-tools.md`「AI 寻聘」一节的剧本办。三条要先记住：

- 任务设置只用 `mcp__moka-go__sourcing_task_update`，画像只用 `mcp__moka-go__sourcing_profile_update`，`mcp__moka-go__sourcing_task_start` 只带 `intent`。
- 开任务要确认：开着就每天用公司渠道账号自动触达候选人、消耗当天额度，发出去的消息收不回。
- 画像条目两种写法：文本 `{ "kind": "text", "text": "3 年以上 Java" }`（`kind` 可省略）；条件
  `{ "kind": "condition", "condition": { "name": "学历", "condition": "gte", "value": ["本科"] } }`；
  `text` 和 `condition` 只能出现一个，和 `kind` 对应。
  解绑渠道职位传 `channelJobId: ""`。

## 成员与其他

- 成员：`mcp__moka-go__user_list` 查；`mcp__moka-go__user_create`、`mcp__moka-go__user_update` 只有管理员能做，报无权限就说明要管理员处理。
- 今天要做什么：`mcp__moka-go__todo_summary` 给出与首页「今天要做」同口径的五组（今日面试、待反馈、待筛选、待安排、Offer 待定）。
- 网页地址用 `mcp__moka-go__system_links` 拿，不凭记忆拼域名。
- `mcp__moka-go__auth_logout` 只在用户要断开这个连接时用。

## 做不到的事（展开）

没有删除候选人、归档投递、手工改经历、维护面试官日历的工具；没有系统打分或自动匹配。用户要评估候选人时，
读 JD 和经历给出有依据的判断，并说明这是基于材料的判断。需要走别的入口时，先确认那个入口真的支持，不替网页打包票。
