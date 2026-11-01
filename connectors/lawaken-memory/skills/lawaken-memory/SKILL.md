---
name: lawaken-memory
description: 查询用户本人的李未可记忆、原文片段和记忆包；当用户要求查找、查看或筛选自己的记忆内容时使用。
description_zh: 查询用户本人的李未可记忆、原文片段和记忆包。
description_en: Read the user's own LAWK memories, transcript passages, and memory packages.
version: 1.1.0
author: LAWK
---

# 李未可记忆

仅查询当前 OAuth 授权账号的数据。连接未授权或授权失效时，引导用户重新连接“李未可记忆”；不要索取、展示或保存访问令牌、短信验证码或旧密钥。

## 工具选择

| 工具 | 用途 | 参数 | scope |
| --- | --- | --- | --- |
| `memory_list` | 分页查询记忆 | 可选：`start_time`、`end_time`、`keyword`、`memory_type`、`cursor`、`limit` | `memory.read` |
| `memory_get` | 按编号读取一条记忆 | 必填：`memory_id`，整数 | `memory.read` |
| `memory_transcript_search` | 分页查询原文片段 | 可选：`memory_id`、`start_time`、`end_time`、`keyword`、`memory_type`、`cursor`、`limit` | `memory.read` |
| `memory_package_list` | 分页查询记忆包 | 可选：`keyword`、`status`、`cursor`、`limit` | `memory.package.read` |
| `memory_package_get` | 读取记忆包及聚合总结 | 必填：`package_id`，字符串 | `memory.package.read` |
| `memory_package_list_memories` | 分页查询包内记忆 | 必填：`package_id`；可选：`cursor`、`limit` | `memory.package.read` |

## 参数规则

- `start_time`、`end_time` 格式为 `yyyy-MM-dd HH:mm:ss`。
- `memory_transcript_search` 使用 `memory_id` 时，不要同时传 `start_time` 或 `end_time`。
- `status` 仅可为 `ready`、`processing`、`failed`。
- `limit` 为正整数，必须服从服务端返回的最大分页限制。
- `cursor` 是服务端返回的不透明分页值，后续页原样回传，不自行解析或构造。
- 没有必填参数的列表工具可用空对象调用；筛选条件不明确时先采用最少条件，不扩大查询范围。

## 使用原则

1. 查多条记忆先用 `memory_list`；已有 `memory_id` 时用 `memory_get`。
2. 用户明确要原话、片段或逐字内容时用 `memory_transcript_search`。
3. 用户明确提到记忆包时，使用三个 `memory_package_*` 工具。
4. 结果为空时如实说明没有匹配项，不改用其他账号、扩大时间范围或绕过权限。
5. 本连接器只提供查询工具，不代表允许新增、修改或删除用户数据。
