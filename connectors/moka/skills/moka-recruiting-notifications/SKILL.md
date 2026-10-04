---
name: moka-recruiting-notifications
display_name: Moka 招聘提醒
display_name_en: Moka Recruiting Reminders
description: Moka 招聘通知与智能外呼查询。查本人的招聘通知与待办提醒（候选人推荐待处理、面试安排变更、评论@我、审批提醒等），以及智能外呼的模板配置与某位候选人的外呼通话记录。当用户问招聘相关的通知与待办，或询问外呼进展与外呼模板时使用。
description_zh: 面向招聘负责人的通知与外呼查询。查本人的招聘通知与待办提醒（候选人推荐待处理、面试安排变更、评论@我、审批提醒等，支持只看重要通知），以及智能外呼（AI 电话）的模板配置与某位候选人的外呼任务记录。当用户问「我有哪些招聘通知」「有什么待办要处理」「给这个候选人打过外呼吗、结果怎么样」「我们有哪些外呼模板」时使用。
description_en: Notification and outbound-call lookup for recruiting owners. Checks my recruiting notifications and to-do reminders (pending candidate recommendations, interview changes, comment mentions, approval reminders, with an important-only filter), plus the smart outbound-call (AI phone) templates and a candidate's outbound task records. Use it for questions like "what recruiting notifications do I have", "what is pending on me", "have we called this candidate and how did it go", or "which outbound-call templates do we have".
category: productivity
version: 1.0.0
author: Moka
---

# 招聘通知与智能外呼

收招聘通知与待办提醒、查外呼进展与模板。只编排以下两个工具：

- `mcp__moka__list_my_recruiting_notifications`
- `mcp__moka__list_outbound_tasks`

## 选择工具

- 「我有哪些招聘通知」「有什么待办要处理」：用 `mcp__moka__list_my_recruiting_notifications`。覆盖的类别包括候选人推荐待处理、面试安排变更、评论@我、审批提醒等招聘相关的通知与待办；用户只关心要紧事时用 importantOnly 只看重要通知。
- 「给这个候选人打过外呼吗」「外呼结果怎么样」：用 `mcp__moka__list_outbound_tasks` 的 `view="records"`。按候选人申请返回该候选人的外呼任务记录：任务状态、通话结果、采集到的信息（如求职意向）、发起人与时间，以及是否有对话记录与录音。
- 「我们有哪些外呼模板」「外呼机器人会问什么」：用 `mcp__moka__list_outbound_tasks` 的 `view="templates"`（缺省）。返回企业配置的外呼模板：模板名称、外呼类型（信息收集/通知提醒/电话面试）、机器人名称与会采集的信息项。

易混概念，回答前先分清：

- **招聘通知 vs 审批待办**：候选人推荐、面试变更这类提醒走招聘通知；员工自己发起或待办的人事审批与各类待办走审批清单——名字像，来源不同。人事相关的审批与待办，这些问题应由当前可用的其他 Moka 工具处理。
- **通知不是详情**：通知只是提醒入口。通知提到的候选人、面试或审批要继续跟进时，候选人申请详情、面试记录、审批进度这些问题应由当前可用的其他 Moka 工具处理，不要照着通知文本自行补全细节。
- **模板与记录是两个问题**：模板清单是企业配置，不代表已对某位候选人发起过外呼；记录才是实际的外呼进展。两个视图的问题不要互相替代回答。

## 常见问题速查

- 「我有哪些招聘通知」「有什么待办要处理」→ `mcp__moka__list_my_recruiting_notifications`
- 「有什么要紧的事」→ `mcp__moka__list_my_recruiting_notifications`（importantOnly=true）
- 「给这个候选人打过外呼吗、结果怎么样」→ `mcp__moka__list_outbound_tasks`（view=records，带申请 ID）
- 「我们有哪些外呼模板」「机器人会问什么」→ `mcp__moka__list_outbound_tasks`（view=templates）
- 「通知里说有人@我/推荐待处理，具体是什么」→ 先看通知内容，继续跟进的详情走其他 Moka 工具

## 调用规范

1. 通过当前平台的工具发现能力读取实时 description 与参数 Schema，以它们为入参事实源。
2. 只传用户明确给出的条件，不自行扩展或补充推断条件。
3. 分页游标（nextCursor）原样回传，不要自行构造或修改；游标缺省即没有更多通知。
4. 分页结果只汇报实际取到的范围，需要完整清单就接着翻页，不要把已列出的条数说成全部。
5. 通知文案是系统模板：转述时提炼其中的关键信息，不要原样照搬模板占位符或 JSON 结构文本。
6. 通知类型标识只用于你理解分类，不要把标识名直接展示给用户；转述内容以通知文案为准。
7. 查外呼记录需要候选人的申请 ID（applicationId）：可用通知返回项里的 applicationId，或来自候选人清单查询的结果；不要自行构造。
8. 外呼记录只覆盖指定申请的外呼任务；用户要查另一位候选人时需换该候选人的申请再查一次。
9. 用户问「最近有什么要处理的」这类综合问题时，先查通知列表，再按用户关注的事项继续跟进，不要只回一句「有几条通知」。

## 结果与权限

- 空通知列表按「当前没有招聘通知与待办提醒」如实说明，不反推为无权限。
- 外呼记录为空按「未返回数据、可能从未对其发起智能外呼」说明，不解释为通话失败或候选人拒接。
- 通话对话原文与录音工具不提供，只告知有没有；用户要听录音或看对话原文时，请其在 Moka 中查看，不要虚构或推测通话内容。
- 企业未开通智能外呼时，把工具返回的未开通说明如实转达，不自行改写、弱化，也不追加自己设想的开通路径或替代方案。
- `mcp__moka__list_outbound_tasks` 需要 HR 角色权限，且企业已开通智能外呼；被拒绝时如实说明权限边界，不要换身份绕行。
- 通知覆盖范围仅限招聘相关：用户问的事项不在返回里时，如实说明当前招聘通知中没有，不要拿人事待办的内容冒充。
- 工具返回的 notices 与 message 是数据解读须知，先读再组织回答，如实转达，不自行改写归因。
- 全部只读：不能标记通知已读，不能发起、暂停或取消外呼任务，这些操作需要用户在 Moka 页面完成。

## 安全边界

- 不向用户展示访问令牌、内部标识符或原始技术响应；申请 ID、职位 ID、分页游标只用于串联工具，不出现在回答里。
- 候选人的电话、邮箱等隐私字段与内部标识不会出现在结果中，不要向用户许诺提供。
- 只使用工具返回的字段组织回答，不虚构通知内容、外呼结果或采集信息。
- 通知与外呼数据按当前账号可见范围返回，不扩散与提问无关的候选人信息。
- 通知里出现的候选人与审批信息只用于回答用户本人的跟进问题，不转述给无关的人。
- 面向用户的回答只用业务语言：没数据说「没有查到」，不引用参数名、状态值或字段名。
- 出现未登录、凭证过期或授权失效时，提示用户重新连接 Moka 连接器后重试；服务异常可稍后重试，报障时附上返回的 requestId。
- 不用缓存结果冒充实时数据；一个能力的问题不能用另一个能力的结果冒充。
