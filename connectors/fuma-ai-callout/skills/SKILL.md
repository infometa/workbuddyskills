---
name: fuma-ai-callout-skill
description: Fuma AI phone callout task creation and lookup tools for WorkBuddy
version: "1.0.0"
author: "Fuma AI"
---

# Fuma AI Callout Skill / 福马AI外呼技能

This Skill lets WorkBuddy use Fuma AI open APIs through MCP to query phone agents, query assignable members, and create AI phone callout tasks.

本技能允许 WorkBuddy 通过 MCP 调用福马AI开放接口，用于查询手机智能体、查询可分配成员，并创建 AI 外呼任务。

## Authentication

The connector uses token-based headers injected by WorkBuddy. If a tool reports unauthorized or token expired, ask the user to verify the Fuma AI `access-token`, `orgCode`, and `loginName` values in the connector configuration.

连接器使用 WorkBuddy 注入的 Token 请求头。用户需要在连接器配置中填写福马AI的 `access-token`、`orgCode` 和 `loginName`；这些凭证通常从福马AI后台或管理员处获取，并仅存储在本机 `~/.workbuddy` 中。如果工具返回未授权或 token 过期，请让用户检查或更新连接器配置中的这三个值。

## Tools

### list_phone_agents

Query available phone intelligent agents.

查询可用的手机智能体。

| Parameter | Type | Required | Description |
| --- | --- | :---: | --- |
| pageNum | number | No | Page number, default 1. |
| pageSize | number | No | Page size, default 10, maximum 100. |

Use this before creating a task when the user has not specified `botId`.

当用户未指定 `botId` 时，先使用此工具查询可用智能体。

### list_callout_members

Query members that can receive task allocation.

查询可接收外呼任务分配的成员。

| Parameter | Type | Required | Description |
| --- | --- | :---: | --- |
| pageNum | number | No | Page number, default 1. |
| pageSize | number | No | Page size, default 10, maximum 100. |

Use this when the user wants average or ratio allocation but has not provided `memberId` values.

当用户需要平均分配或比例分配但未提供 `memberId` 时，先使用此工具查询可分配成员。

### create_callout_task

Create a Fuma AI phone callout task.

创建福马AI电话外呼任务。

| Parameter | Type | Required | Description |
| --- | --- | :---: | --- |
| name | string | Yes | Task name. |
| botId | string | Yes | Phone intelligent agent ID from `list_phone_agents`. |
| userInfoList | array | Yes | Callee list. Each item requires `phone`; `name` and `otherInfo` are optional. |
| encryptType | number | No | 1 for AES, 2 for MD5. Defaults to 1. |
| assignMode | number | No | 1 for average allocation, 2 for ratio allocation. |
| memberList | array | No | Required when `assignMode` is set. Each item has `memberId`; `ratio` is required for ratio allocation. |

Before calling `create_callout_task`, collect a clear task name, bot ID, and at least one valid phone number. If allocation is requested, collect member IDs first.

调用 `create_callout_task` 前，需要收集明确的任务名称、智能体 ID，以及至少一个有效手机号。如果用户要求任务分配，需要先收集成员 ID。

## Error Handling

If Fuma AI returns `errCode` other than `0`, surface the returned `errInfo` or full response to the user and ask for missing or corrected data. For invalid or expired authorization, ask the user to reconnect the connector.

如果福马AI返回的 `errCode` 不是 `0`，将返回的 `errInfo` 或完整响应反馈给用户，并提示用户补充或修正数据。若凭证无效或过期，请让用户重新配置连接器凭证。
