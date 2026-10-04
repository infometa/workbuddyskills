---
name: opcmenu-signup
display_name: 独行录报名机会
display_name_en: Apply to opportunities on opcmenu
description: 在独行录筛选活动、黑客松或创业赛事，合并多场报名资料缺口，按用户授权提交报名并查询结果。
description_zh: 筛选独行录报名机会，一次补齐跨场资料，提交报名并查询结果。
description_en: Find relevant events on opcmenu, consolidate missing application details, and follow registration results.
version: 1.1.0
author: 独行录
---

# 独行录报名机会

用于独行录站内活动发现、报名和结果查询。通过已连接的 MCP 工具操作，参数以当前工具描述为准。公开浏览不用登录，个人报名资料和提交操作需要宿主授权；不要要求用户在对话里粘贴密钥。

1. `list_signup_feed` 找到可报名机会，保留服务端排序；结合用户条件选择候选，核对截止时间及其时区。
2. `get_signup_activity` 查看详情、题目、个人报名状态。不是所有 `list_activities` 返回的外部活动都能站内报名。
3. 确定要报的场次后，`get_signup_gaps` 合并各场资料缺口。同一个问题只问一次，不重问资料里已有且仍有效的内容。
4. 把用户提供的通用资料通过 `update_my_signup_profile` 保存到跨场复用层；只保存用户为本次报名提供或授权复用的信息。
5. 报名前展示场次和拟提交内容；已有明确提交授权时继续执行。逐场 `submit_signup`，省略的答案不等于清空。分别报告已提交、仍缺资料、截止或外部接力的结果。
6. `list_my_signups` 查询结果。提交后遇到超时先核实状态，避免重复提交；不得把候补或投递成功说成已经入围。

附件题目前需要用户到报名页或 App 上传；外部表单可能需要浏览器接力。返回实际工具提供的链接，完成后再读取状态。不能用一个 URL 冒充已上传文件，不能只因页面打开就称报名成功。

查询条件会发送到独行录服务；报名答案按用户选择的活动提交给对应主办方。敏感答案只在必要时读取与展示，不跨活动擅自复用未授权信息。授权失效使用宿主重新连接；服务返回 `exits` 时依其恢复，不能自动绕过截止、权限或资格要求。
