---
name: fbs-connector
description: "福帮手人机协同连接器：身份、场景包、乐包、首值记录和超级合伙人交接。"
description_zh: "福帮手人机协同连接器：身份、场景包、乐包、首值记录和超级合伙人交接。"
description_en: "FBSir MCP connector for identity, scene packs, lebao status, first-value recording, and super-partner handoff."
version: "26.7.2"
connectorContractVersion: "1.2.9"
author: "FBSir"
---

# 福帮手人机协同连接器

这份技能说明用于指导 WorkBuddy 通过公开连接器地址使用 `fbs-connector` MCP 服务。默认口径以中文为主；英文仅保留在规范要求的字段中，不作为主说明语气。

## 使用边界

- 公开 MCP 地址：`https://api2.u3w.com/fbs-mcp/mcp`
- 当前连接器包版本：`26.7.2`
- 当前公开 MCP 兼容合约版本：`1.2.9`
- 不要把已发布的 WorkBuddy 客户端改到 `/api/fbss/mcp`；那个地址属于 API2 sidecar / direct integration 面，不是正式连接器入口。
- 服务健康、`tools/list`、只读 scene-pack 检查，只能证明能力面可用，不能直接证明自然业务闭环已经完成。

## 推荐调用顺序

1. 先调用 `skill_whoami`，读取身份、权益、scene-pack 和 next-action 状态。
2. 如果 `skill_whoami.actionEnvelope.tool` 或 `nextAction.tool` 返回 `fbs_scene_pack_query`，就在同一个 binding 上用返回参数继续调用。
3. 如果 scene-pack 响应要求 `skill_consume`，就在同一个 binding 上精确记录一次 `first_value_completed` 或 `continued_use_completed`。
4. 当凭证或奖励状态不明确时，先调用 `lebao_status`，再判断是否需要 claim / redeem。

## 安全边界

- 把 `sessionRef`、`sessionToken`、凭证签名、本机绝对路径视为敏感信息。
- 没有对应工具结果确认时，不得声称乐包、权益解锁、首值完成或继续使用已经完成。
- 专家包 UI 证明与连接器证明必须分开。超级合伙人专家团的正式展示面可以来自远端 COS UI，而本地 `my-experts` 只属于等效调试路径。
- 不要把 probe、synthetic、monitor、host-proxy fallback 样本当成自然业务闭环证据。
