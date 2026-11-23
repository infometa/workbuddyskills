---
name: weiling-crm-usage
description: Use when the user asks to query or maintain WeiLing CRM data — clues/contacts, companies, businesses (商机), follow-up records (跟进记录), schedules (日程), or files. Covers tool selection, write-confirmation rules, operator identity, and error recovery.
description_zh: 当用户需要查询或维护卫瓴 CRM 的联系人、企业、商机、跟进记录、日程或文件时使用，指导 AI 正确选择工具、写操作确认、操作人身份与错误恢复。
description_en: Use when the user needs to query or maintain WeiLing CRM data such as clues, companies, businesses, follow-up records, schedules, or files.
version: 1.0.0
author: 卫瓴·协同 CRM 团队
---

# 卫瓴 CRM 连接器使用说明

在 WorkBuddy 里用自然语言查询、维护卫瓴 CRM 的**联系人、企业、商机、跟进记录、日程与文件**。

## 前置条件（重要）

- **无需用户填写任何凭证**。鉴权走 MCP 自带的 OAuth 扫码授权：首次连接时用户扫码确认，
  WorkBuddy 自动完成换 token 与续期。**不要向用户索要 AppId / AppSecret / access_token**。
- 唯一需要用户做的动作是「连接器管理里点一次扫码授权」。若提示未授权/授权过期，
  就说「请重新点一次卫瓴 CRM 的授权，扫码确认一下就好」。

## 工具总览（按业务线）

**联系人**（仅查）：`list_clues`、`get_clue_detail`、`get_clue_portrait`（画像/客户旅程）、`check_mobile`（手机号查重）。
> 创建/编辑联系人**不提供**（见铁律第 12 条）。

**企业**：`list_my_companies`、`get_company_info`、`get_company_by_name`、`get_company_history`（企业动态/画像）（查）；
> 企业的新增 / 编辑 / 删除**均不提供**（见铁律第 12 条）。

**商机**：`list_businesses`、`get_business_detail`、`get_business_history`（商机旅程/动态）、
`list_customer_businesses`（客户/企业相关商机）（查）。
> 商机的创建 / 编辑 / 删除**均不提供**（见铁律第 12 条）。

**跟进记录**：`get_progress_detail`、`list_progress_templates`、
`get_progress_template_detail`、`list_progress_replies`（查评论）；`add_progress`、`edit_progress`、
`record_to_progress`、`delete_progress`、`add_progress_reply`（写）。

**文件**：`upload_file`（上传）、`to_cos_url`（网络文件转存）。

**日程**：`get_schedule_detail`（查，查不到会返回预填草稿）；`save_schedule`（新建/更新，写）、
`delete_schedule`（删除，写）。

**系统配置**：`get_property_config`（对象**完整字段配置**：英文名/中文名/类型/枚举名）、
`get_custom_table_column`（某场景下列表/详情展示哪些列）、
`get_tenant_config`（字典/枚举选项：把枚举值翻译成中文）、
`list_clue_channels`（联系人来源渠道树：把来源值翻译成中文 / 列出可选来源）。

**组织架构**：`list_dept_users`（部门 + 员工列表：查同事、选参与人、了解组织架构）。

## 铁律（务必遵守）

1. **写操作先确认**：所有带「写」的工具，调用前必须把关键字段（对象、内容、附件等）
   复述给用户并得到明确确认，再执行。
   **但有合理默认值的非关键字段不要单独追问**（如 `add_progress` 的 `open_to_square` 默认 0）。
   ⚠️ **删除 / 编辑跟进记录：必须单独确认一次，不能「用户说了就直接删/改」**：
   - 先回查目标记录，把「**时间 + 内容摘要 + 归属对象**」复述给用户，得到确认后再调用；
   - 即使用户说的是「删掉刚才那条」这种明确指令，也要先复述**具体是哪一条**（防指错，且删除不可逆）。
2. **操作人身份自动取**：写跟进、建商机时，记录人/归属人由连接器服务端从授权会话自动取
   当前扫码人，**不要向用户索要 `create_user_id` / `owner_id` / `userid`**。
3. **id 不展示**：结果里的 `id` / `*_id` 是系统内部标识，向用户转述时**不要念出这些 id 数字**，
   但后续查详情/编辑时要原样回传。
4. **分页是页码不是游标**：联系人/企业/商机列表用 `page_count`（页码，从 1 起）+ `limit`（条数），
   不是 cursor。
5. **跟进编辑/删除限时**：跟进记录**创建后 10 分钟内**才可编辑或删除。超时后 `edit_progress` /
   `delete_progress` 会被工具直接拒绝（分别返回 `edit_window_expired` / `delete_window_expired`）；
   如需补充或更正内容，请**新建一条跟进**说明。
6. **术语统一（重要）**：`clue` 这个对象对用户统一称「**联系人**」，回复里**不要出现「线索」二字**
   （工具名 `list_clues`、参数 `clue_id`、scene 值 `clue_manage` 等只在调用时用，不要念给用户）。
7. **重名校验（重要）**：按名称定位联系人/企业时，先确认能否**唯一确定**对象。
   - **完整名称能唯一确定**（如"巨量彭强"精确命中一条）→ 直接执行，**不要**在完成后补报
     「系统里还有 N 条同名的」之类的模糊匹配信息。
   - **仍无法唯一确定**（多条同名、信息不足）→ **写入前**把候选列给用户选（带手机号/企业/归属人
     等区分信息），不要自行猜测后写入再让用户来纠正。
8. **不暴露内部机制（重要）**：不要向用户解释接口名、错误码、降级路径、层级差异。
   - ❌ 错误示例：「客户级接口会返回「跟进对象不存在」，所以记在了联系人这一层」「code 7004 表示…」
     「只能走 X 层创建」
   - ✅ 正确做法：只讲**做了什么、结果如何、需要用户决定什么**。失败就说一句人话
     （如「这条没写进去，因为这个对象当前不可写」），不要贴 code / 接口名 / 技术术语。
   - 内部排查信息（错误码、降级原因）留给自己判断，不进最终回复。
   - 规则句中的**内部解释**（为什么不支持、为什么这样限制、系统内部如何实现等）属于内部判断，
     **不要解释给用户**；用户追问「为什么」时，只回该条的标准话术，或一句人话结论
     （如「这项暂时不支持」），不要展开理由。
   - ⚠️ **边界**：对象当前的真实状态、以及用户必须知情的操作后果（如「本人不在参与人里」
     「超过 10 分钟无法编辑，需要新建一条」）属于**行为事实**，该说仍然要说，不要因为上一条而省略。
   - 汇报执行进展的措辞（该讲什么、不该讲什么）另见下文「**对外表达口径**」。
9. **群 / 访客写跟进（重要）**：用户要给「某个群」或「某个访客」写跟进时：
   1. 先按名称正常查**联系人 / 企业 / 商机**（`list_clues` / `list_my_companies` / `list_businesses`），
      有匹配的可以提出来确认「是不是这个」；
   2. 三类都查不到 → **直接回复**：「暂不支持在 WorkBuddy 中给群聊/访客写跟进记录，请在卫瓴协同CRM中填写。」
   3. ⚠️ **不要向用户索要群 id / 访客 id**。**只回上面那一句**，不要解释为什么、不要补充任何说明。
10. **文案语言（重要）**：面向用户的文案一律用**简体中文**。
    - 确认弹窗的选项标签里，"推荐"写「**（推荐）**」，**不要用英文 `(Recommended)`**。
    - 技术词（接口名、错误码、progress_type 等）不直接展示给用户。
11. **日程不能凭空声称（重要）**：只有 `save_schedule` 调用成功、且回查到 `data.id` 非空，才能说
    「日程已创建」。
    - `get_schedule_detail` 返回 `has_schedule: false` / `is_draft: true` → 表示该跟进**根本没有日程**，
      `data` 只是「新建」时的预填草稿，`start_time` 是系统建议时间。
    - **不要**在回复里说「已有日程」「系统自动带出了一个待办/提醒」。
    - 如果确实想建日程，先跟用户确认时间，再调 `save_schedule`，成功后回查确认。
12. **不支持创建/编辑/删除联系人、企业、商机（重要）**：当前**不提供**这些操作。
    用户提出时**只回这一句**（不解释为什么不提供，不描述这些操作的复杂程度）：
    > 暂不支持在 WorkBuddy 中创建/编辑/删除联系人（企业/商机），请在卫瓴协同CRM中操作。
    - **不要**尝试用其他工具变相实现，也**不要**向用户索要必填字段清单；
    - 跟进记录（`add_progress` / `edit_progress` / `delete_progress`）与日程功能**仍然可用**。

## 对外表达口径

向用户说明进展时，只讲「**用户在等什么**」，不讲「**我在怎么执行**」。

- **可以讲**：进度与范围 —— 「已核对 12 个商机的本周动态」「覆盖 10/20–10/22」
- **必须讲**：需要用户决策或授权的岔路口
- **不讲**：批次与页码（「第 1 页」「下一页」「还剩 3 页」）、处理方式与脚本（「结果较大，用脚本提取关键信息」
  「我写个脚本跑一下」）、接口与工具名、错误码与重试次数、字段与数据结构名（「只取名称和 id」）

判定标准：把这句话换成用户视角重讲一遍，还有信息量吗？

- **有** → 说（「还剩约 10 个没核对」）
- **只是复述了执行动作** → 不说（「正在翻第 2 页」）

失败按用户语言报告：「这条暂时没取到，我换个方式再试」；原始错误码保留给排查模式，
不进用户可见的话术。

## 常见调用链

- 给某联系人加跟进：`list_clues`（按姓名 keyword）→ 拿联系人 id → `add_progress`（`progress_type=0`）
- 给企业加跟进：`list_my_companies`（按 keyword）→ 拿 `company_id` → `add_progress`（`progress_type=3`）
- 给商机加跟进：`list_businesses` → 拿 `business_id` → `add_progress`（`progress_type=7`）
- 带附件跟进：先 `upload_file` 拿 `cos_url` → 再 `add_progress` 带 `image_files` / `attachment_files`
- 给跟进记录建日程：先 `get_schedule_detail`（`progress_id` + `progress_type`）拿草稿字段 →
  再 `save_schedule`（`summary`/`description`/`start_time`/`end_time`/`attendees`）
- 分析联系人画像：`list_clues`（手机号/姓名找到人）→ 拿联系人 id → `get_clue_detail`（基础信息）
  + `get_clue_portrait`（动态，可带 `history_type=3` 只看跟进）→ 综合出客户分析与跟进建议

## 联系人画像（客户旅程）特别注意

- **用途**：`get_clue_portrait` 拉取某联系人（联系人）的画像时间轴，用于**分析客户意向与跟进情况**——
  客户动态（资料浏览、停留时长、分享、网页访问、表单提交等）+ 跟进动态（跟进记录）。
- **游标分页（不是页码）**：首页不传 `cursor`；下一页把上次响应里的 `data.cursor` **原样回传**
  （它是 AES 密文，不可改写）；`data.cursor` 为空或 `count=0` 表示没有更多。
- **`history_type`**：`1` 全部历史（默认）/ `2` 客户动态 / `3` 跟进动态。切换类型要重新从首页开始。
- **`keyword`** 仅对跟进历史生效。
- **联系人不存在不报错**：返回 `count=0`，不要当成失败。
- **做画像分析时**：先 `get_clue_detail` 拿基础信息（姓名/公司/职位/标签），再 `get_clue_portrait`
  拉动态，综合给出「客户意向、关注点、风险、下一步跟进建议」。`history` 是多态卡片列表，
  按 `history_type` + `event_type` + `card_type` 解读；展示时隐藏 `id` / `history_id` / `event_id` 等内部标识。

## 日程（schedule）特别注意

- **查详情会返回草稿**：`get_schedule_detail` 按 `progress_id` 查不到日程时**不报错**，而是返回
  预填草稿（`data` 里没有 `id`/`wx_schedule_id`）。**用 `has_schedule` 字段判断**：
  `false` / `is_draft: true` = 该跟进**没有日程**，`start_time` 只是建议时间，不要说「已有日程」。
- **新建/更新用同一个 `save_schedule`**：不传 `schedule_id` 是新建；传了是更新（更新必须同时传
  `wx_schedule_id`）。`start_time`/`end_time` 是**毫秒时间戳数字**，`attendees` 元素只需 `userid_third`。
  ⚠️ **新建必须传 `progress_id` + `progress_type`**：卫瓴日程必须挂在一条跟进记录下，不传会 500；
  同一跟进只能有一个日程，重复创建返回 `1001`（要先查 `get_schedule_detail` 确认有没有）。
  ⚠️ **参与人必须包含本人**：工具会自动把当前登录人补进去（放第一位），所以不要向用户索要自己的 id；
  用户只说「和某某开会」时，attendees 传对方即可。
- **删除是 `delete_schedule`**，参数是内部 `schedule_id`（不是 `wx_schedule_id`），不可逆，需二次确认。
- **5 秒防重复锁**：`save_schedule` 对同一跟进记录 5 秒内重复提交会被拦，失败重试要隔 5 秒以上。
- **5010 日历未授权**：企业未完成企微日历授权时新建日程会返回 5010，引导用户去卫瓴后台完成日历授权。

## 读懂列表 / 详情数据（推荐先做）

列表/详情里的很多字段是**存 key、不存文案**的（枚举、区域多级、商机阶段等），直接看原始数据会是一堆数字。正确顺序：

1. **先取字段配置**：优先用 `get_property_config(object_name)` —— 一次拿到该对象**全部字段**的
   英文名（`property_name`）→ **中文展示名（`view_name`）** → 字段类型（`property_type`）→ **枚举名（`enum_name`）**。
   对象名：`clue`（联系人）/ `external_user`（企微好友）/ `company`（企业）/ `business`（商机）。
   只想知道某个列表/详情页"展示了哪些列、什么顺序"时，用 `get_custom_table_column(scene)`。
2. **再翻译枚举**：字段若带 `enum_name`，调 `get_tenant_config(name=enum_name)` 拿 `key → value` 映射，
   把数据里的 key 翻成中文。通用枚举：`last_call_status`（上次呼叫状态）、`source`（来源）、
   `business_stage`（商机阶段/区域，多级，带 `level`/`parent_key`）。
3. **然后才解读/分析**：拿到带中文的完整数据后再做总结、对比、判断。

- `get_tenant_config()` **不传 name** 会一次返回全部枚举（并附带商机流程 `process_id`）。
- **联系人来源**（联系人的 `from_channel_id`）不在 `get_tenant_config` 里，用 `list_clue_channels` 取渠道树来翻译
  （返回层级树，节点带 `source_name` / `full_source_name`；广告渠道节点还带 `platform_id`）。
- `get_property_config()` **不传 object_name** 会返回全部对象的字段（含未启用字段，看 `is_enabled` 判断）。
- `get_custom_table_column` 是 **POST**，参数 `scene` 必填；该场景无表头配置时返回 `code=1003`，属正常情况，不是报错。

## 企业视图 / 企业画像

要看一个企业的全貌，组合三个工具：

1. `get_company_info`（`company_id`）— 企业基础信息（全称/简称/状态/行业/参保人数/网址等）。
2. `list_customer_businesses`（`id`=企业 id、`type`=5）— 该企业关联的商机列表。
3. `get_company_history`（`company_id`）— 企业动态时间轴：企业信息创建/变更、相关人、企业关系网、商机变更、标签、群等 + 跟进动态。

- **`get_company_history` 是加密游标分页**：首页**不要传 `cursor`**（工具会自动补空串；不传会 500）；
  下一页把上次响应里的 `data.cursor` 原样回传；响应不再出现 `cursor` 即末页。
  `history_type`：`1` 全部（默认）/ `2` 客户动态 / `3` 跟进动态。首次查询还会返回 `start_cursor`（时间轴起点）。
- **企业不存在会直接报错**（与联系人画像不同，联系人不存在是返回 `count=0`）。
- **`list_customer_businesses` 不分页**，一次全量返回；**只含「已立项」商机**（审批中/驳回看不到）；
  结果里 `company` 只有 `company_id`，要企业名需另查 `get_company_info`。`type` 决定 `id` 含义：
  `1` 企微好友 / `2` 个微人脉 / `3` 手机号联系人 / `4` 群 / `5` 企业。
- 做企业分析时：先 `get_company_info` + `list_customer_businesses` 拿事实，再用 `get_company_history` 补动态，
  综合输出「企业基本情况、商机进展、近期动态、风险与机会」。

## 商机视图 / 商机旅程

看一个商机的全貌：

1. `get_business_detail`（`business_id`）— 商机详情（名称/编号/企业/对接人/阶段/金额/归属人等）。
2. `get_business_history`（`business_id`）— 商机旅程时间轴：商机变更（创建/赢单/丢单/废弃/更新）、跟进记录，以及关联的企业动态、对接人动态。

- **商机变更事件**用 `business_opp`（新值）+ `business_opp_old`（旧值）+ `change_fields`（变更了哪些字段）表达，
  做「更新前 / 更新后」对比时按这三者呈现。
- **`get_business_history` 的 `scene`**：`1` 只看商机动态 / `2` 企业动态 / `3` 对接人动态；不传返回全部
  （对应商机详情页的三个 tab）。`history_type`：`1` 全部（默认）/ `2` 客户动态 / `3` 跟进动态。
- **游标分页**同企业动态：首页不传 `cursor`（工具会自动补空串），翻页原样回传 `data.cursor`；首次返回 `start_cursor`。
- **商机不存在返回空 `history`**（不报错）——这一点与企业动态（企业不存在直接报错）不同。
- 找商机：先 `list_businesses` 或 `list_customer_businesses` 拿到商机 id，再查详情和旅程。

## 组织架构（员工 / 部门）

`list_dept_users` 查公司的部门 + 员工（只读）。

- **不传 `pid`** 一次性拉全公司（推荐）；传 `pid`（回传响应里的部门 id）只拉该部门的直接子部门 + 直属员工。
  ⚠️ **不要传 `pid = 0`**（会被当成合成部门，结果近似为空）。
- 返回 `data.data_list` 是**扁平列表**：部门节点 `type=1`（带 `count` 人数）、员工节点 `type=2`（带 `userid_third` 企微成员 ID），
  用 `pid` 串成树；结果**顶层**另有 `user_count`（员工去重人数，**不在 `data` 里**）；`id`/`pid` 都是**字符串**。
- 常用筛选：`only_dept`（只要部门）、`only_leader`（只要部门负责人）、`only_sub`（只看自己及下级，需当前人是负责人）、
  `status`（`1` 已激活默认 / `2` 禁用 / `4` 未激活 / `5` 退出企业）。
- **默认只返回「已激活」员工**，离职员工不返回。
- 典型用途：查某部门有哪些人、找同事；建日程 / 分配任务时确认人选——参与者需要的是员工的 `userid_third`（企微成员 ID）。

## 跟进记录 @ 同事（重要）

**不要在 `remark` 里手写 `@姓名`** —— 纯文本不会被卫瓴识别成 @，也不会给对方发站内提醒
（`statistic_count` 不会增加，看起来"@ 了但没生效"）。

正确做法：用 `add_progress` / `edit_progress` 的 **`mentions`** 参数，工具会自动拼成卫瓴要求的 HTML：

```json
{
  "business_related_id": "联系人/企业/商机 id",
  "progress_type": 3,
  "remark": "这家有机会，约明天上门拜访，请及时跟进",
  "mentions": [
    { "id": "员工数字id", "userid_third": "企微成员ID", "name": "辛凯" }
  ]
}
```

- `id` 与 `userid_third` 都必填，用 `list_dept_users` 查（该响应里同时有 `id` 和 `userid_third`）。
- 支持多个（同名同事也能区分），会按顺序 @ 在文字前面。
- 若必须手写 HTML，格式为
  `<span class="at-span" contenteditable="false" userid_third="企微ID" id="员工id">@姓名</span>`，两个属性缺一不可。

## 跟进记录评论

评论挂在某条跟进记录下，分「一级评论」和「回复」。

- **查评论**：`list_progress_replies`（`progress_id` 必填）。返回 `data.data_list`，每条一级评论下面带
  `replies` 子数组；`page_count` / `limit` 只对**一级评论**分页，`data.count` 是**一级评论数**，不是总条数。
  该接口会把这些评论标记为**已读**，同一批不必反复拉取。
- **发评论**：`add_progress_reply`（`progress_id` + `content`）。【写操作】发送前把内容复述给用户确认。
  - 内容按纯文本算**最多 1000 字**。
  - **@ 同事**用 `mentions` 参数（每项 `{id, userid_third, name}`，用 `list_dept_users` 查），
    工具会自动拼成卫瓴的 @ 格式并触发提醒；不要手写纯文本「@姓名」，系统不识别。
  - 图片最多 4 张，先 `upload_file` / `to_cos_url` 拿 COS 地址；附件用 `attachment_file`（单个对象）。
  - **回复别人的评论**：从 `list_progress_replies` 结果里取 `root_id`（所在根评论的 `reply_id`）
    和 `parent_id`（要回复那条评论的 `reply_id`），两个都传，不要猜。
- **展示**：按「评论人 + 时间 + 内容」列出一级评论，回复缩进挂在对应评论下面；
  `reply_id` / `root_id` / `parent_id` 等 id 不展示。
- 没有评论就说「这条跟进还没有评论」，不要把空结果说成失败。

## 跟进记录定位（coordinate_json）

`add_progress` / `edit_progress` 都支持 `coordinate_json`，传的是 **JSON 对象**（不是字符串）：

```json
{
  "name": "上海控易电子科技有限公司",
  "address": "上海市宝山区逸仙路2816号",
  "longitude": 121.489296,
  "latitude": 31.338396,
  "coortype": "gcj02"
}
```

| 字段 | 说明 |
|------|------|
| `name` | 地点名称 |
| `address` | 地址 |
| `longitude` / `latitude` | 经度 / 纬度（Double）|
| `distance` | 距离（米，可选）|
| `coortype` | 坐标系：`gcj02`（火星坐标，高德/腾讯）/ `bd09ll`（百度坐标）|

- 系统会把定位渲染成 **`#地址#`** 追加在跟进文字后面（如 `…请及时跟进#上海市宝山区逸仙路2816号#`）。
- 不确定坐标系时默认用 `gcj02`；只知道地址时，尽量补全经纬度再传。

## 上传附件（图片 / 文件）

**统一用「上传票 + 本机 curl」直传，不管文件大小。不要用 base64**（会撑爆模型上下文，大文件必然失败）。

流程：

1. 调 `create_upload_ticket(file_name="照片.jpg")` 拿票（返回里已拼好 `upload_url`）。
2. 在**用户本机 shell** 执行：

   ```bash
   curl -s -X POST "<upload_url>" -F "file=@<文件绝对路径>"
   ```

3. 按类型放进**不同**参数：
   - **图片**（png / jpg 等）：取 `data.cos_url` → `image_files`（字符串数组，最多 9 张）
   - **文件**（pdf / docx / xlsx / zip 等）：取 `data.attachment_file`（对象 `{name, type, size, url}`）→
     放进 `attachment_files`（**对象数组**，最多 3 个）
   ⚠️ 文件**不要**塞进 `image_files`，也**不要**只往 `attachment_files` 里放一个 URL 字符串——
     这两种都会让附件在跟进记录里**显示成图片**。
   ⚠️ 对象里的 `type` 是**分类**不是扩展名（`compressed` / `word` / `excel` / `ppt` / `pdf` / `txt` /
     `image` / `video` / `audio`），填 `zip`、`xlsx` 这种会显示成图片。上传接口返回的
     `attachment_file` 已经是正确分类，**直接用，不要自己改 type**。

要点：

- 票**一次性、5 分钟有效**、默认上限 50MB；用完即失效，不要重复用同一个票。
- 字节走 shell，**不进模型上下文**，几 MB 到几十 MB 都一样。
- `upload_file`（`file_path`）只在连接器与用户同机时可用；远程会返回 `file_path_unsupported`，**不要反复换路径重试**。
- 已有网络链接的图片/文件 → `to_cos_url(url)` 转存。

| 错误码 | 含义 | 处理 |
|--------|------|------|
| `file_path_unsupported` | 连接器读不到该路径（远程部署）| 改用上传票 |
| `ticket_expired` / `ticket_used` | 票过期 / 已用过 | 重新调 `create_upload_ticket` |
| `too_large` | 超过票上限（默认 50MB）| 调大 `max_size` 重新发票 |

## progress_type 取值（add_progress / list_progress_templates 用）

`0`=联系人，`1`=客户，`3`=企业，`4`=访客，`6`=群，`7`=商机。**注意没有 2 和 5**，不确定时先问用户。

## 错误恢复

> **对内看 code，对外说人话**：下面这些 code 只用于你自己判断，**不要出现在给用户的回复里**，
> 也不要解释「为什么降级到另一层接口」。

- **401 / token 失效** → 引导用户重新扫码授权，不要反复重试。对用户只说「连接已失效，需要重新授权一下」。
- **code 7004（游客权限）** → 同 401，重新授权。
- **code 90009（重复联系人）** → 把返回的重复联系人信息交给用户决策（合并/放弃），不要自动重试。
- **跟进对象不存在** → `add_progress` 可能返回 `code=200` 但无 `data`，记录实际未创建，
  需回查确认是否真的写入，不要当成成功。
