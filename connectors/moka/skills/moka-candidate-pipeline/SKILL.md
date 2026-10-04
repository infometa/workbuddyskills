---
name: moka-candidate-pipeline
display_name: Moka 候选人
display_name_en: Moka Candidates
description: Moka 候选人跟进与流程盘点。查询分配给我的候选人及其申请详情、按招聘流程与阶段查看候选人名单、统计各流程各阶段的候选人申请数量。当用户跟进自己名下的候选人、按流程阶段拉候选人名单，或盘点招聘流程各阶段的人员分布时使用。
description_zh: 面向招聘负责人与用人经理的候选人跟进与流程盘点。查询分配给我的候选人及其申请详情（简历要点、教育与工作经历、评分与推荐理由）、按招聘流程与阶段查看候选人名单（HR 视角）、统计各流程各阶段的候选人申请数量。当用户问「我有哪些待筛选的候选人」「面试阶段现在有哪些人」「各阶段各有多少人」「这个候选人的简历怎么样」时使用。
description_en: Candidate follow-up and pipeline review for recruiting owners and hiring managers. Lists candidates assigned to me with full application details (resume highlights, education and work history, ratings and recommendation reasons), lists candidates in a given recruiting pipeline stage (HR view), and reports candidate application counts across pipeline stages. Use it for questions like "which candidates are pending my screening", "who is in the interview stage now", "how many applications are in each stage", or "how does this candidate's resume look".
category: productivity
version: 1.0.0
author: Moka
---

# 候选人跟进与流程盘点

跟进候选人、按流程阶段拉名单、盘点各阶段人数。只编排以下三个工具：

- `mcp__moka__list_my_assigned_candidates`
- `mcp__moka__list_pipeline_candidates`
- `mcp__moka__get_recruiting_stage_statistics`

## 选择工具

三个工具回答三类不同的问题，先分清再调：

- 「我名下」的候选人：用 `mcp__moka__list_my_assigned_candidates`。数据面是分配给当前用户的候选人，按待筛选/可面试/已推荐/已筛选四个处理状态查，支持按候选人姓名搜索、按职位与招聘模式过滤；它也承担申请详情查询（`action="detail"`）。
- 某条招聘流程某个阶段现在有哪些候选人：用 `mcp__moka__list_pipeline_candidates`。这是 HR 视角的流程内名单，不限定分配给谁——「面试阶段现在有哪些人」「Offer 阶段的名单拉一下」走这里。
- 各流程各阶段现在各有多少人：用 `mcp__moka__get_recruiting_stage_statistics`。只要数量分布、不要名单时用它——「各阶段积压了多少人」「面试阶段还有多少候选人在跑」。

易混概念，回答前先分清：

- **候选人 vs 申请**：候选人是人，申请是这个人投在某个职位下的流程记录。同一个人可以有多条申请，阶段、评分、推荐理由都挂在申请上，不要跨申请混用。
- **两套「阶段」不是一回事**：招聘流程阶段（初筛/面试/Offer 等，企业自行配置）是候选人在流程里的位置，`mcp__moka__list_pipeline_candidates` 与 `mcp__moka__get_recruiting_stage_statistics` 用的是这一套；「待筛选/可面试/已推荐/已筛选」是分配给某人的处理状态，只属于 `mcp__moka__list_my_assigned_candidates`。两套的数字不可互相比对或相加。
- **申请数 vs 人数**：流程阶段统计与名单的单位是候选人申请，同一个人应聘多个职位会分别计入，不要说成「多少人」。

在企业人才库中寻找尚未进入流程的新候选人、查看职位详情与 JD、查招聘需求的名额（HC）进度——这些问题应由当前可用的其他 Moka 工具处理。

## 常见问题速查

- 「我有哪些待筛选的候选人」→ `mcp__moka__list_my_assigned_candidates`（stage=pending，缺省）
- 「这个候选人的简历怎么样」→ `mcp__moka__list_my_assigned_candidates`（先列表定位，再 `action="detail"`）
- 「面试阶段现在有哪些人」→ `mcp__moka__list_pipeline_candidates`（流程名与阶段名原样传）
- 「各阶段各有多少人」「Offer 阶段积压了多少」→ `mcp__moka__get_recruiting_stage_statistics`
- 「哪些人到了可面试阶段、都什么背景」→ 名单 + 逐个详情，一次走完

## 调用规范

1. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源。
2. 只传用户明确给出的条件（阶段、候选人姓名、职位、招聘模式等），不自行扩展或补充推断条件。
3. 申请详情走两段式：先用 `mcp__moka__list_my_assigned_candidates` 的列表（`action="list"`，缺省）拿到返回项的 applicationId，再用同一工具 `action="detail"` 带 applicationId 查完整申请详情（基本信息、教育与工作经历、来源渠道、评分与推荐理由）。
4. 拿到列表就找详情：用户问「哪些候选人到了某阶段」时，列出名单后主动钻取最相关的前几位的申请详情，把可直接行动的信息补齐，并说明做了取舍；不要停在名单上。
5. 阶段名单钻取链：`mcp__moka__get_recruiting_stage_statistics` 看分布 → 把返回项的流程名与阶段名**原样**传给 `mcp__moka__list_pipeline_candidates` 拉名单 → 用名单返回项的 applicationId 调 `mcp__moka__list_my_assigned_candidates`（`action="detail"`）看详情。
6. 流程名与阶段名是企业自己配置的（可能是英文、自定义叫法甚至带拼写错误），必须原样引用与回传，不要翻译或「纠正」；名称含义不明时可借返回的阶段类型语义辅助说明，并说清「这是你们企业配置的阶段名」。
7. 流程名或阶段名匹配不到时，工具会随错误返回可选清单，从清单取原始名称重试即可，不要凭记忆造名称。
8. 企业可能配置同名的社招与校招流程：转述时带上每条流程自己的招聘模式区分，不要把两条同名流程的数字混为一谈或相加。
9. 分页游标（nextCursor）原样回传，不要自行构造或修改；`mcp__moka__list_pipeline_candidates` 的每页条数由服务端固定、不可自定义，要更少结果就用职位收窄。
10. 相对日期（「这周」「上个月」）按用户所在时区换算成绝对条件后再调用，回答里说明实际查询口径。

## 结果与权限

- 空列表、空统计一律按「未返回数据」如实说明：既可能确实没有候选人，也可能当前账号没有可查看的职位数据权限（两者返回形态相同，无法区分）。
- 不要断言「该阶段没有人」，也不要断定是权限问题；用户预期应该有数据时，可建议其找管理员确认账号的数据范围。
- 统计里未返回数据的流程既不能算 0 也不能算有数据，按「未返回数据」转述；因数量上限未统计的流程可用流程名称单独再查。
- 数据范围是当前账号有权查看的招聘职位，不等于全公司总量；无权查看的保密职位不在结果内，不同账号看到的数字可能不同。
- 三个工具的角色门槛不同：`mcp__moka__list_my_assigned_candidates` 面试官及以上可用；`mcp__moka__list_pipeline_candidates` 与 `mcp__moka__get_recruiting_stage_statistics` 需要 HR 角色，用人经理与面试官账号会被拒绝。
- 被权限拒绝时如实说明权限边界，不要换身份绕行，也不要用另一个工具的结果冒充。
- 工具返回的 notices 与 message 是数据解读须知，先读再组织回答，如实转达，不自行改写归因。
- 全部只读：不能筛选通过/淘汰候选人、不能推进流程阶段，这些操作需要用户在 Moka 页面完成。

## 安全边界

- 不向用户展示访问令牌、内部标识符或原始技术响应；申请 ID、职位 ID、分页游标只用于串联工具，不出现在回答里。
- 候选人的电话、邮箱等隐私字段与内部标识不会出现在结果中，不要向用户许诺提供。
- 只使用工具返回的字段组织回答，不虚构工具未返回的评价、背景或结论。
- 候选人数据按当前账号角色可见范围使用，不扩散与提问无关的候选人信息。
