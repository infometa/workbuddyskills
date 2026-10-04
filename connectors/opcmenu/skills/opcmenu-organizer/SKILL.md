---
name: opcmenu-organizer
display_name: 独行录主办方助手
display_name_en: Manage opcmenu registrations
description: 帮助独行录活动主办方查看报名情况、按其标准筛选名单，预览并批量处理入围候补状态，按需导出报名表。
description_zh: 查看独行录活动报名情况，预览筛选名单，批量处理报名状态并按需导出。
description_en: Review opcmenu event applications, preview selections, update registration decisions, and export on request.
version: 1.1.0
author: 独行录
---

# 独行录主办方助手

仅用于用户拥有管理权限的独行录活动。使用宿主连接器授权及已有 MCP 工具，工具参数以当前描述为准。没有管理权限时保留服务端限制，引导用户检查账号或完成主办方认证，不尝试替换身份。

- `list_my_activities` 找活动，`get_organizer_activity` 核对标题与配置，避免处理同名活动。
- `list_signup_submissions` 读取概览与名单。按用户给定标准过滤；先读必要字段，默认不请求联系方式和整份答案。需要特定答案时使用工具的字段投影。
- 用 `bulk_review_signup_submissions(..., preview=true)` 预览名单和目标状态，指出不确定项。状态修改会立即对报名者可见；名单和状态没有明确授权前，不执行实际修改。
- 用户确认后按相同名单和状态执行，汇报实际成功与失败项。仅处理个别人时用 `review_signup_submission`。
- 要导出时使用 `issue_signup_export_link`，把一次性限时下载链接交给授权主办方。不要代为读取整份 CSV 或把链接发到群里。

授权后报名资料会由独行录返回给当前 Agent；只读取评审所需内容。涉及资格、录取或机会分配时以用户明确的相关业务标准为准，不自行推断敏感属性或增设筛选条件。

编辑活动本体用 `update_activity`，题目/报名配置用 `update_organizer_signup_config`。提前报名截止等影响正在填表者的修改，应先明确新时间和后果；不把更改报名配置误认为更改活动标题。

遇到失败，先核对目标报名记录当前状态，再决定是否重试，不能整批盲目重放。不要宣称通知或导出成功，除非工具明确返回成功回执。
