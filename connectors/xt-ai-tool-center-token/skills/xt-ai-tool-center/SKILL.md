---
name: xt-ai-tool-center
display_name: 小题 AI 工具中心
display_name_en: XT AI Tool Center
description: 使用小题 AI 工具中心完成实时数据检索、媒体理解与内容生成。当用户的任务需要调用已连接的 xt-ai-tool-center-token MCP 工具时使用。
description_zh: 使用小题 AI 工具中心完成实时数据检索、媒体理解与内容生成。
description_en: Use XT AI Tool Center for live data retrieval, media understanding, and content generation.
version: 0.1.1
author: 小题XT
---

# 小题 AI 工具中心

通过当前已连接的 `xt-ai-tool-center-token` MCP Server 完成任务。工具能力和参数以 WorkBuddy 当前实际显示的 MCP Tool 列表及 schema 为准。

## 使用规则

- 根据用户目标选择最匹配的工具，只传入完成任务所需的参数。
- 调用前核对当前工具名称和 schema，不臆造不存在的工具、参数、返回值或完成状态。
- 用户已明确要求执行具体操作时直接调用；工具自身要求确认或提示预计费用时，先向用户说明并等待确认。
- 连续或批量调用应控制在完成当前任务所需的最小范围，不因内部重试造成无意义的重复调用。
- 对工具返回的数据注明来源和时间；结果为空、失败或不完整时如实说明，不补造事实。

## 认证与计费异常

- 如果提示 MCP Key 无效、未授权或认证失败，引导用户打开 WorkBuddy 的连接器设置，更新“小题 AI 工具中心”的 MCP Key 后重试。
- 不要求用户在对话中发送完整 MCP Key，也不在回复、日志或交付物中展示凭证。
- 如果提示余额或额度不足，引导用户前往[小题个人中心](https://xtharness.com/api-keys)检查账户并充值；在余额恢复前停止收费调用。
- 如果服务超时或暂时不可用，只进行必要的一次安全重试；仍失败时报告当前状态并停止。

## 结果边界

- 以 MCP 工具实际返回结果为准，不把推测描述为已执行结果。
- 不泄露认证信息、钱包标识、内部服务地址或工具的非公开响应。
- 涉及发布、删除、付费或其他不可逆操作时，遵守工具返回的确认要求和用户授权范围。
