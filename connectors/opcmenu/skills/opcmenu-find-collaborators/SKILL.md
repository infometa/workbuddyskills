---
name: opcmenu-find-collaborators
display_name: 独行录找合作
display_name_en: Find collaborators on opcmenu
description: 在独行录按用户能提供的服务和正在寻找的资源发现合作对象、需求与产业链伙伴，解释匹配理由并起草联系内容。
description_zh: 在独行录找合作对象和需求，查看产业链伙伴，起草联系内容并跟进私信。
description_en: Find collaborators and relevant needs on opcmenu, explore supply-chain partners, and draft outreach.
version: 1.1.0
author: 独行录
---

# 独行录找合作

用于用户要求在独行录找人、找需求、找服务商或处理已有合作私信。泛泛讨论创业或一人公司概念不需要连接服务。

通过此连接器已经提供的 MCP 工具执行；工具名可能带宿主前缀，参数与能力以当前工具描述为准。公开搜索不需要登录。读取我的资料或代我操作时使用宿主连接器的授权流程；凭证不进入聊天内容。

- 找人：从用户已说明的能力、需求、城市等条件开始，按意图选择 `search_people`、`search_needs` 或 `list_needs_feed`。需要我的资料且已授权时读 `get_my_card`，不在公开搜索前强制登录。
- 核实：用 `get_creator`、`get_need` 查看候选依据，通常精选 3 位，说明能合作的具体部分和仍需核实的条件。不要把匹配分写成合作成功率。
- 产业链：用 `get_chain_anchor` 查看上游下游，`list_chain_group_members` 翻页；游标原样回传。
- 接洽：先展示联系内容；用户已明确授权收件人与内容时可以执行。`contact_need` / `start_conversation` 可能立即自动发送开场语，不要把它们当纯查询。拿到 conversationId 后才用 `send_message` 继续谈。
- 跟进：用 `get_my_brief` 看需要处理的信号，再按需读取会话和消息、起草回复。没有宿主定时任务时，不承诺持续监控。

独行录是外部网络服务：查询条件会发送到 opcmenu.com；授权后工具会按账号权限返回对应资料和消息。只读取完成任务所需内容。不得将私人联系方式、消息或整份数据卡自动发给候选人或其他平台。交换联系方式、花积分等额外动作需处于用户明确授权范围。

结果不明确时先读状态，不重复发送。工具返回 `exits` 时按其说明恢复；授权失效走宿主重新连接。只使用工具实际返回的事实和链接。
