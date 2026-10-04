---
name: moka-jobs
display_name: Moka 职位
display_name_en: Moka Jobs
description: Moka 职位查询。搜索招聘职位并查看职位详情（JD、职责、任职要求）、查职位发布到了哪些招聘站点，以及企业配置的工作地点与候选人来源渠道清单。当用户搜职位、看 JD、确认职位发布情况，或需要确认工作地点与招聘渠道时使用。
description_zh: 面向招聘负责人的职位查询。按关键词与状态搜索招聘职位、查看职位详情（职位描述 JD、工作职责、任职要求、招聘团队）、查某个职位发布到了哪些招聘站点，以及查询企业配置的工作地点与候选人来源渠道清单。当用户问「现在有哪些在招的前端职位」「这个职位的 JD 是什么」「这个职位发到哪些官网了」「我们开通了哪些招聘渠道」「面试可以安排在哪些地点」时使用。
description_en: Job lookup for recruiting owners. Searches recruiting jobs by keyword and status, shows job details (job description, responsibilities, requirements, recruiting team), checks which recruiting sites a job is published to, and lists the company's configured work locations and candidate source channels. Use it for questions like "which frontend jobs are open now", "what is the JD of this job", "which career sites is this job published on", "which recruiting channels do we have", or "where can interviews be held".
category: productivity
version: 1.0.0
author: Moka
---

# 职位查询与基础数据

搜职位、看 JD、查发布情况，外加工作地点与来源渠道两份基础数据。只编排以下四个工具：

- `mcp__moka__search_jobs`
- `mcp__moka__get_job_publish_status`
- `mcp__moka__list_work_locations`
- `mcp__moka__list_candidate_channels`

## 选择工具

- 搜职位、看职位列表、看某个职位的 JD 与任职要求：用 `mcp__moka__search_jobs`。支持按关键词与职位状态（招聘中/已暂停/已关闭/待发布）过滤。
- 「我负责哪些职位」「我手上在招几个岗」：同样用 `mcp__moka__search_jobs`，按归属范围筛选——`scope="managed"` 只看我负责的、`scope="assisting"` 只看我协助的。不要拉全量职位再按姓名猜，也不要把全公司职位说成本人负责的。
- 「这个职位发到哪些官网了」「为什么官网上搜不到这个职位」「还能发到哪些站点」：用 `mcp__moka__get_job_publish_status`。发布状态按站点区分（社招官网、校招官网、内推官网），返回已发布站点与还可发布站点两份清单，回答时说清是哪个站点。
- 「面试可以安排在哪些地点」「北京办公室在哪」：用 `mcp__moka__list_work_locations`。这是消歧用的基础数据（本人可用的工作地点清单），供安排面试、填写职位工作地点时参考。
- 「我们开通了哪些招聘渠道」「有没有接猎聘」「简历来源都有哪些」：用 `mcp__moka__list_candidate_channels`。同样是消歧用的基础数据（企业配置的来源渠道清单，按分类分组），只给渠道名称，不含各渠道的投递数量或效果。

概念先分清：**职位 vs 招聘需求**——需求是「要招几个人（HC 名额）、招得怎么样了」，职位是对外发布的岗位与要求。问职责要求、发布情况查职位；问「要招几个、招到几个、需求什么状态」是招聘需求问题，这些问题应由当前可用的其他 Moka 工具处理。两者可以关联，但不是一回事。

跟进职位下的候选人、查看人才库推荐、看面试安排——这些问题也应由当前可用的其他 Moka 工具处理。

## 常见问题速查

- 「现在有哪些在招的前端职位」→ `mcp__moka__search_jobs`（keyword + status）
- 「这个职位的 JD/任职要求是什么」→ `mcp__moka__search_jobs`（先搜索定位，再 `action="detail"`）
- 「我负责/协助哪些职位」→ `mcp__moka__search_jobs`（scope=managed / scope=assisting）
- 「这个职位发到哪些官网了」「官网怎么搜不到」→ `mcp__moka__search_jobs` 拿 jobId → `mcp__moka__get_job_publish_status`
- 「面试可以安排在哪些地点」→ `mcp__moka__list_work_locations`
- 「我们开通了哪些招聘渠道」→ `mcp__moka__list_candidate_channels`

## 调用规范

1. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源。
2. 职位详情走两段式：先用 `mcp__moka__search_jobs` 搜索（`action="search"`，缺省）拿到返回项的 jobId，再用同一工具 `action="detail"` 带 jobId 查 JD、工作职责、任职要求与招聘团队。
3. 用户问某个具体职位时，搜到后主动查详情，把回答所需的信息补齐，不要停在列表上；命中多个同名职位时先按部门、地点与状态消歧，必要时向用户确认。
4. 查发布情况同样先有 jobId：`mcp__moka__search_jobs` 搜到职位 → 把 jobId 传给 `mcp__moka__get_job_publish_status`。「官网搜不到这个职位」先查发布情况，不要归因为职位不存在。
5. `mcp__moka__list_work_locations` 与 `mcp__moka__list_candidate_channels` 无需入参、单步直达。
6. 只传用户明确给出的条件（关键词、职位状态、归属范围），不自行扩展；分页游标（nextCursor）原样回传，不要自行构造。
7. 渠道名称与分类、站点名称、地点由企业自行配置，原样引用，不要翻译或改写。

## 结果与权限

- 空结果一律按「未返回数据」如实说明，不反推为无权限，也不断言「没有这类职位/渠道/地点」。
- `mcp__moka__search_jobs`、`mcp__moka__get_job_publish_status` 与 `mcp__moka__list_candidate_channels` 需要 HR 角色权限（用人经理、面试官账号会被拒绝）；被拒绝时如实说明权限边界，不要换身份绕行。
- 职位数据按当前账号可见范围返回：无权查看的保密职位不在结果内，不同账号看到的职位数量可能不同。
- 可发布站点清单受账号的站点数据权限影响，为空不代表「没有别的站点可发」；已停用的站点不会出现在清单里。
- 职位未发布到任何站点时，如实说明候选人在官网看不到它；发布操作本工具不提供。
- 工作地点范围按本人的部门授权裁剪，不是企业全部地址；列表按最近使用优先排序，不含面试时手动填写的临时地址。
- 渠道清单只含当前启用、适用于当前招聘模式的渠道，已隐藏的渠道不返回；它不代表实际投递量，要看某渠道来了多少人需要用户在 Moka 中查看渠道报表。
- 工具返回的 notices 与 message 是数据解读须知，先读再组织回答，如实转达，不自行改写归因。
- 全部只读：不能发布或取消发布职位、不能新建或修改职位、地点、渠道，这些操作需要用户在 Moka 页面完成。

## 安全边界

- 不向用户展示访问令牌、内部标识符或原始技术响应；职位 ID、分页游标只用于串联工具，不出现在回答里。
- 只使用工具返回的字段组织回答，不虚构 JD 内容、发布状态或渠道效果。
- 招聘团队与职位数据按当前账号可见范围使用，不扩散与提问无关的职位或团队成员信息。
- 隐私字段与内部标识不会出现在结果中，不要向用户许诺提供。
- 面向用户的回答只用业务语言：没数据说「没有查到」，不引用参数名、状态值或字段名。
- 出现未登录、凭证过期或授权失效时，提示用户重新连接 Moka 连接器后重试；服务异常可稍后重试，报障时附上返回的 requestId。
