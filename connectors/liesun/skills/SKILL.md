---
name: liesun-recruiting
description: 猎隼招聘查询与受控写入——查岗位、候选人、面试、录音分析摘要和招聘分析；创建岗位或上传简历必须先预览再确认
version: "1.2.2"
author: "猎隼 AI 智聘"
---

# 猎隼招聘 Skill

用猎隼 MCP 查询已有招聘事实。写入只有创建岗位和上传单份简历，必须先预览。

## 使用前

- 用户在 WorkBuddy 点连接后，会打开猎隼授权页：登录或注册、确认组织、勾选能力后点允许。不要让用户去设置里复制密钥。
- WorkBuddy 用授权码换票；过期后先走 refresh。refresh 失败、提示未授权或 401 时，让用户在 WorkBuddy 里对「猎隼AI智聘」重新点连接，再走一遍授权页。不要改去设置页复制密钥，也不要让用户自己填 Bearer。
- 用户要撤回时，到猎隼「设置 → 招聘设置 → 开放接入」停用或删除。停用后不要重试同一把旧票。
- 返回范围不超过该成员当前组织、角色和数据范围。邮箱在 MCP 里会打码。不要把分数当成录用结论。
- 招聘数据属敏感个人信息。禁止将候选人姓名、联系方式、简历原文写入本地文件、在线文档或群消息；输出只保留岗位匹配判断所需的最小信息。
- 不要承诺候选人状态流转、换岗、自动联系、录音原文下载、完整转写或批量导出。这些工具不存在。
- 不要传 `organization_id` / `created_by`，服务端会丢弃并改用当前成员身份。

## 列表约定

`search_jobs`、`search_candidates` 共用：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| page | number | - | 页码，从 1 开始 |
| page_size | number | - | 默认 10，超过服务端上限按上限返回 |
| include_total | boolean | - | 默认 false；需要「共 N 条」时再开 |

## 先查后写

1. 先用只读工具确认对象（岗位 ID、候选人 ID、时间范围）。
2. 创建岗位或上传简历时，第一次必须 `confirm=false`，把预览给用户看。
3. 用户明确同意后，用相同参数再调一次并设 `confirm=true`。
4. 用户没点头，不要提交。

## 只读工具

### search_jobs

按名称或状态列出岗位。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| keyword | string | - | 岗位名称关键词 |
| status | string | - | `online` 上架 / `offline` 下架 / `draft` 草稿 |
| hr_user_id | number | - | 按岗位创建人筛选；personal 范围下只看本人 |

### get_job_detail

岗位详情：薪资、学历、年限、JD、招聘人数、候选人数。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| job_id | number | ✅ | 岗位 ID |
| include_jd | boolean | - | 默认 true；只要结构化字段可设 false |

### search_candidates

按姓名、岗位、状态搜索候选人。问「这个人怎么样」不要停在本工具，继续 `get_candidate_journey`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| name | string | - | 姓名模糊搜索 |
| job_id | number | - | 岗位 ID |
| status | string | - | 状态码，逗号分隔。0 待处理 / 1 候选人 / 2 面试通过 / 3 淘汰 / 4 已邀约 / 5 面试中 / 6 已入职 / 7 已发 offer / 8 放弃 |
| order_by | string | - | `created_at`（默认）/ `updated_at` / `match_score`。`match_score` 必须同时传 `job_id` |
| created_from | string | - | 新增起点，YYYY-MM-DD |
| created_to | string | - | 新增终点，YYYY-MM-DD |
| hr_user_id | number | - | 按招聘负责人筛选；personal 范围下只看本人 |

### get_candidate_detail

候选人基础信息、状态、岗位、Offer。不含面试轮次与匹配度。问「这个人怎么样」改用 `get_candidate_journey`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| candidate_id | number | ✅ | 候选人 ID |

### get_candidate_journey

候选人全流程：基本信息、简历要点、岗位、匹配分、轮次、结论。已有 `candidate_id` 时首选，不要再拆成 detail + matching + rounds。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| candidate_id | number | ✅ | 候选人 ID |
| include_matching | boolean | - | 默认 true |
| include_rounds | boolean | - | 默认 true |

### get_resume_quickview

简历速览：教育、经历、技能摘要。不是原文。只有 `resume_id`、没有 `candidate_id` 时才用。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| resume_id | number | ✅ | 简历 ID |

### get_matching_result

已有匹配分析结果（总分与各维度）。缺证据时按返回的 unknown/partial 转述，不要补造。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| candidate_id | number | ✅ | 候选人 ID |

### get_interview_schedule

查面试日程。`scheduled_date` 与 `month` 必须二选一。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| scheduled_date | string | - | 单日，YYYY-MM-DD |
| month | string | - | 月历，YYYY-MM；只回有面试的日期和当天条数 |
| job_id | number | - | 按岗位筛选 |
| include_cancelled | boolean | - | 默认 false |

### list_candidate_rounds

某候选人的面试轮次。某一轮的录音分析摘要用 `get_interview_round_analysis`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| candidate_id | number | ✅ | 候选人 ID |
| include_cancelled | boolean | - | 默认 false |

### get_interview_round_analysis

某轮已有结论、录音分析摘要、风险与建议。只读已有结果，不触发重分析，不返回录音原文或完整转写。没有分析记录时如实说缺证据。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| round_id | number | ✅ | 面试轮次 ID，先从 `list_candidate_rounds` 或日程取得 |

### get_recruitment_overview

招聘概览指标卡（简历/筛选/Offer/入职）。谈单个岗位必须传 `job_id` 或 `job_ids`。未传时间默认近 30 天。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| time_from | string | - | YYYY-MM-DD 或 ISO8601 |
| time_to | string | - | YYYY-MM-DD 或 ISO8601；仅日期时按当天闭区间 |
| job_id | number | - | 单个岗位 |
| job_ids | number[] | - | 多个岗位，最多 50；与 `job_id` 同时传时以本字段为准 |
| hr_user_id | number | - | 按招聘负责人；personal 范围下只统计本人 |
| channel_ids | number[] | - | 渠道 ID，最多 50 |
| base_locations | string[] | - | 工作地点，最多 50 |
| time_basis | string | - | `created`（默认，可看转化率）/ `occurred`（期间活动，转化率为空） |

### get_recruitment_funnel

招聘漏斗阶段人数与转化率。参数与 `get_recruitment_overview` 相同。口径以返回 `meta` 为准，不要改公式。

### get_recruitment_summary

按负责人/岗位/渠道/地点分组的汇总表，最多 50 行。筛选参数同上，另加：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| group_by | string[] | - | `organization` / `created_by` / `job_id` / `channel_id` / `work_location`。不传默认按招聘负责人；按岗位出报告传 `["job_id"]` |
| metrics | string[] | - | `screening` / `interview_rounds` / `offer` / `onboarding`；不传返回全部 |

### get_interview_rounds_stats

1–4 轮面试量与通过率。通过率 = 通过 /（通过 + 未通过），待定不进分母。筛选参数与 `get_recruitment_overview` 相同。

### get_user_help

产品帮助文档。不能代替业务数据查询，也不要编造套餐或界面承诺。`doc_id` 与 `query` 至少填一个。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| doc_id | string | - | 已知文档 id |
| query | string | - | 关键词检索 |
| prefer_context | string | - | 页面上下文，如 `settings`、`resume_management`、`job_management` |

## 受控写入（默认关闭）

授权未授予 `job_write` / `resume_write` 时，这些工具不会出现。出现了也必须预览。

### create_job

默认草稿，不自动上架。不支持更新、删除、批量。创建后用 `search_jobs(keyword=岗位名)` 回读。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| job_name | string | ✅ | 岗位名称 |
| confirm | boolean | - | 默认 false 只预览；true 才创建 |
| work_location | string | - | 工作地点；草稿可省略 |
| department | string | - | 所属部门 |
| salary_range | string | - | 如 15K-25K |
| education_requirement | string | - | 学历要求 |
| work_years | string | - | 如 3-5年 |
| job_description | string | - | 职责与任职要求 |
| department_job_description | string | - | 用人部门提供的描述 |
| status | string | - | `draft`（默认）/ `offline` / `online` |
| recruitment_period_days | number | - | 招聘周期（天） |
| headcount | number | - | 招聘人数 |
| visibility_scope | string | - | `organization`（默认）/ `owner_only` |

### upload_resume

单文件，≤10MB，pdf/docx/doc/txt/jpg/jpeg/png，不支持 zip。解析异步，提交后返回 `task_id`；完成态用 `search_candidates(name=文件名或姓名)` 回读。

- 只上传用户在当前对话中明确指定的那一个文件；禁止自行遍历、搜索或猜测本地目录寻找简历。
- 上传前向用户回显文件名，确认后再编码提交；非简历类文件一律拒绝。
- 禁止把候选人姓名、联系方式、简历原文写入本地文件、在线文档或群消息；输出只保留岗位匹配判断所需的最小信息。

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| filename | string | ✅ | 带扩展名，如 zhangsan.pdf |
| file_base64 | string | ✅ | 文件 Base64，可带 data URL 前缀 |
| job_id | number | - | 关联岗位 |
| confirm | boolean | - | 默认 false 只预览查重；true 才提交解析 |

## 默认不开放

列表里没有 `compare_candidates_for_job`、`generate_interview_questions` 就不要调用，也不要编造结果。未出现对比工具时，用每人的 `get_matching_result` + `get_candidate_journey` 做横向对照，缺证据标 unknown。

## 常见错误

- `401` / 未授权 / token 无效：重新点连接，不要编造密钥。
- `permission_denied` / 不存在：当前成员看不见这条数据，换有权限的人或改问本人范围内的对象。
- `invalid_params`：按该工具参数表补齐，缺 `job_id`、`candidate_id`、`round_id` 或日期时先查再调。
- 匹配、录音分析返回空或 unknown：如实说还没有分析结果，不要补造分数、名次或面试结论。
- 写入预览成功：只代表还没落库，必须用户确认后再 `confirm=true`。

## 不要做

- 不要调用不存在的 `set_status`、自动联系、删除、扣费、重跑录音分析。
- 不要把 AI 匹配分说成录用结论。
- 不要把「已接收 / 预览成功」说成已经创建或已经上传。
- 不要把录音分析摘要说成录音原文或完整转写。
- 不要自行翻盘找文件，也不要把姓名、联系方式、简历原文写到本地文件、在线文档或群消息。

## 示例

- 「这个人跟岗位匹配吗，还要不要往下推」→ `search_candidates` 再 `get_matching_result` / `get_candidate_journey`
- 「这几位横向对比」→ 每人 `get_matching_result` + `get_candidate_journey`；列表里有 `compare_candidates_for_job` 才用它
- 「这场面试的录音分析」→ `list_candidate_rounds` 再 `get_interview_round_analysis`
- 「今天有哪些面试」→ `get_interview_schedule(scheduled_date=今天)`
- 「近 30 天漏斗卡在哪」→ `get_recruitment_funnel`
- 「帮我建一个上海运营岗」→ `create_job` 且 `confirm=false`，用户确认后再 `confirm=true`
