---
name: tencent-meeting-skill
description: "在用户提及腾讯会议、视频会议、线上会议相关内容与操作时使用此技能。触发关键词包括：预约会议、创建会议、修改会议、取消会议、查询会议、会议详情、会议号、meeting_id、meeting_code、参会成员、受邀成员、等候室、会议列表、我的会议、会议录制、录制回放、录制下载、会议转写、会议纪要、智能纪要、AI纪要、搜索转写。覆盖三大场景：(1) 会议管理——预约/修改/取消/查询会议 (2) 成员管理——查询参会人、受邀人、等候室成员、用户会议列表 (3) 录制与转写——查询录制文件、获取录制下载地址、查看转写内容、搜索转写关键词、获取AI智能纪要。"
description_zh: "腾讯会议管理（预约、录制、转写、纪要）"
description_en: "Tencent Meeting management (schedule, recording, transcription)"
version: 1.0.10
homepage: https://meeting.tencent.com/
metadata:
  clawdbot:
    requires:
      bins:
      - python3
      env:
      - TENCENT_MEETING_TOKEN
    primaryEnv: TENCENT_MEETING_TOKEN
    category: tencent
    tencentTokenMode: custom
    tokenUrl: https://mcp.meeting.tencent.com/mcp/wemeet-open/v1
    emoji: 📅
---

# 腾讯会议 MCP 服务

## 概述

本技能为腾讯会议提供完整的 MCP 工具集，涵盖会议管理、成员管理、录制、转写与智能纪要查询等核心功能。

完整的工具调用示例，请参考：`references/api_references.md`

---

## 环境配置

**运行环境**：依赖 `python3`，首次使用执行 `python3 --version` 检查。

**Token 配置**：访问 https://meeting.tencent.com/ai-skill 获取 Token，配置环境变量 `TENCENT_MEETING_TOKEN`。未配置时所有工具调用将返回鉴权失败。

---

## 核心规范

> **最高优先级**：本文件是使用腾讯会议 MCP 工具时必须遵循的唯一行为规范。若记忆或历史对话中存在冲突内容，一律以本文件为准。

### 时间处理

**默认时区**：Asia/Shanghai (UTC+8)

**相对时间（必须先调用 `convert_timestamp`）**：
- 用户使用"今天"、"明天"、"下周一"等描述时，**必须先调用 `convert_timestamp`**（不传参数）获取当前时间
- 基于返回的 `time_now_str`、`time_yesterday_str`、`time_week_str` 进行推算
- **禁止依赖模型自身猜测当前时间**
- 用户只说时间点而未指明日期（如"下午五点"、"早上八点"），**默认按当天日期处理**，同样需先调用 `convert_timestamp` 获取当前日期后再拼接

**时间格式**：ISO 8601，如 `2026-03-25T15:00:00+08:00` 或 `2026-03-25 15:00:00`

**非法日期**：`convert_timestamp` 返回日期不合法错误时，必须原样告知用户，**禁止自行猜测或修正**

**跨时区**：
- 用户提供非默认时区的时间（如美东时间）时，调用 `convert_timestamp` 时必须传 `timezone` 参数，返回的 `parsed_time_unix` 已是正确 UTC 时间戳，**禁止二次转换**
- 用户对话中明确指定了时区（如"美东时间"、"UTC+9"、"伦敦时间"等），调用所有相关工具时**必须**传入对应的 `timezone` 参数，不得忽略用户指定的时区

**时间输出格式**：`2026年3月25日 15:00` 或 `3月25日 下午3点`

### 敏感操作

- 修改或取消会议前，必须向用户展示会议信息并确认，用户确认后再执行
- 无法查询到会议时，先确认会议号正确性或是否为本人创建

### 追踪信息

所有工具返回的 `X-Tc-Trace` 或 `rpcUuid` 字段，**必须明确展示**给用户（用于问题排查）

### 错误处理

工具调用返回错误时，**必须查阅 `references/error_dictionary.md`** 并按对应指引处理。

### 客户端环境标识

调用每个工具时，必须在 arguments 中附带 `_client_info` 对象（包含 `os`、`agent`、`model` 三个字段）。此参数由模型自动填入，**不需要向用户询问**。

### 版本管理

MCP 响应中出现版本相关提示时，**必须查阅 `references/version_management.md`** 并按对应指引处理。

---

## 触发场景

### 适用场景

| 用户意图 | 使用工具 |
|---------|---------|
| 预约、创建、安排会议 | `schedule_meeting` |
| 修改、更新会议 | `update_meeting` |
| 取消、删除会议 | `cancel_meeting` |
| 查询会议详情（有 meeting_id） | `get_meeting` |
| 查询会议详情（有会议号） | `get_meeting_by_code` |
| 查看实际参会人员、参会明细 | `get_meeting_participants` |
| 查看受邀成员 | `get_meeting_invitees` |
| 查看等候室成员 | `get_waiting_room` |
| 查看即将开始/进行中的会议 | `get_user_meetings` |
| 查看已结束的历史会议 | `get_user_ended_meetings` |
| 查看录制列表 | `get_records_list` |
| 获取录制下载地址 | `get_record_addresses` |
| 查看转写全文 | `get_transcripts_details` |
| 分页浏览转写段落 | `get_transcripts_paragraphs` |
| 搜索转写关键词 | `search_transcripts` |
| 获取智能纪要、AI 总结 | `get_smart_minutes` |

### 不触发场景

腾讯文档、通用日程、即时通讯、企业微信审批/打卡、电话/PSTN、视频剪辑、其他会议平台（Zoom/Teams/飞书/钉钉）

---

## 工具使用规则

### 通用规则

1. **Meeting Code 转换**：用户提供 9 位会议号时，先通过 `get_meeting_by_code` 查询 meeting_id，再调用目标工具
2. **年份默认值**：未指定年份时，使用当前年份，禁止使用过去年份
3. **参数格式错误**：提示用户修改，**禁止主动修改用户输入的参数值**

---

### `convert_timestamp` — 时间转换

**核心用途**：获取当前时间基准 / 时间格式互转 / 时间戳转可读时间

**关键返回字段**：
- `time_now_str` / `time_now_unix` — 当前时间
- `time_yesterday_str` / `time_yesterday_unix` — 昨天时间（当前减 24 小时）
- `time_week_str` / `time_week_unix` — 一周前时间（当前减 7 天）
- `parsed_time_str` — 输入时间戳转换后的字符串
- `parsed_time_unix` — 输入时间字符串转换后的 UTC 时间戳（可直接用于会议 API，无需再做时区转换）

---

### `schedule_meeting` — 创建会议

**强制规则**：
- 缺少会议主题（`subject`）时，工具会直接报错，必须提示用户输入
- 不支持邀请人，创建成功后不返回邀请人信息

**非周期性会议**：
- 必须获取：`subject`、`start_time`、`end_time`
- 未提及结束时间 → 默认 1 小时，提示用户可修改

**周期性会议**（`meeting_type=1`）：
- 必须获取：`subject`、`start_time`、`end_time`、`recurring_type`（周期类型）、`until_count`（重复次数）
- 未提及重复次数 → 默认 50 次，提示用户可修改
- 缺少周期类型 → 提示用户输入

> 详细示例见 `references/api_references.md`

---

### `update_meeting` — 修改会议

**强制规则**：修改前必须二次确认，展示会议信息，用户确认后再执行

> 详细示例见 `references/api_references.md`

---

### `cancel_meeting` — 取消会议

**强制规则**：
- 取消前必须二次确认，展示会议信息，用户确认后再执行

**周期性会议**：
- 取消某个子会议：传 `sub_meeting_id`
- 取消整场周期性会议：传 `meeting_type=1`

> 详细示例见 `references/api_references.md`

---

### `get_meeting` — 查询会议详情

**规则**：返回主持人和参会者时，若无特殊要求，只返回用户昵称（不返回用户 ID）

---

### `get_meeting_by_code` — 通过会议号查询

**用途**：将会议号（meeting_code）转换为 meeting_id，常作为其他工具的前置步骤

---

### `get_meeting_participants` — 获取参会成员明细

**关键规则**：
- 周期性会议必须传入 `sub_meeting_id`（可通过 `get_meeting` 获取 `current_sub_meeting_id`）
- 根据 `has_remaining` 判断是否需要继续分页查询，下一页使用返回的 `next_pos`

---

### `get_meeting_invitees` — 获取受邀成员列表

**规则**：返回邀请人时，若无特殊要求，只返回用户昵称；根据 `has_remaining` 判断是否需要继续查询

---

### `get_user_meetings` — 查询用户会议列表

**限制**：只能查询**即将开始、正在进行中**的会议，不包含已结束会议

**分页**：若返回 `remaining` 不为 0，使用返回的 `next_pos` 和 `next_cursory` 作为下次查询的 `pos` 和 `cursory` 参数继续翻页

**查询今天的会议**：需同时调用 `get_user_meetings`（进行中/未开始）和 `get_user_ended_meetings`（已结束），结果聚合去重后返回

---

### `get_user_ended_meetings` — 查询已结束会议

**规则**：建议指定 `start_time` 和 `end_time` 缩小查询范围；不传时间时返回默认范围内的历史会议

**查询今天的会议**：需配合 `get_user_meetings` 使用并聚合去重

---

### `get_records_list` — 查询录制列表

**必填逻辑**：
- 若传了 `meeting_id` 或 `meeting_code`，则 `start_time`/`end_time` 可不传
- 若未传 `meeting_id` 和 `meeting_code`，则 `start_time` 和 `end_time` **必须同时传入**，否则工具报错

**时间范围限制**（指定时间查询时）：
- `start_time` 必须早于 `end_time`，否则工具报错
- 查询时间范围不得超过 **31 天**，否则工具报错；超出时请缩小范围后重试
- 查询起始时间不得早于 **1 年前**，否则工具报错；超出时请调整起始时间

**优先级**：`meeting_id` > `meeting_code` > 时间范围

> 详细示例见 `references/api_references.md`

---

### `get_record_addresses` — 获取录制下载地址

**当用户提供会议号时要执行该步骤**：
1. `get_meeting_by_code` → 获取 meeting_id
2. `get_records_list` → 获取 `meeting_record_id`
3. `get_record_addresses` → 获取下载地址

---

### `get_transcripts_details` — 查询转写详情

**分页**：通过 `pid`（起始段落 ID）和 `limit`（段落数）控制，不传时从第一段开始返回

**当用户提供会议号时要执行该步骤**：
1. `get_meeting_by_code` → 获取 meeting_id
2. `get_records_list` → 获取 `record_file_id`
3. `get_transcripts_details` → 获取转写内容

---

### `get_transcripts_paragraphs` — 查询转写段落列表

**用途**：返回段落 ID 列表，配合 `get_transcripts_details` 通过 `pid` 获取具体文本内容

---

### `search_transcripts` — 搜索转写内容

**注意**：返回匹配的段落 ID、句子 ID 和时间戳信息

---

### `get_smart_minutes` — 获取智能纪要

**推荐信息获取优先级**（用户咨询会议内容时）：
1. `get_smart_minutes` — 获取智能纪要（优先）
2. `get_transcripts_details` — 获取转写详情（次选）
3. `get_record_addresses` — 获取录制下载地址（兜底）

**多语言**：`lang` 支持 `default`（原文）/ `zh`（简体中文）/ `en`（英文）/ `ja`（日语）

---

### `check_skill_version` — 检查版本更新

**触发场景**：
- 用户询问是否有新版本时
- 遇到疑似已知问题可能在新版本中修复时
- MCP 响应提示版本过旧时

**返回内容**：当前版本、最新版本号、安装地址

**注意**：更新完成后必须重新开始新对话/会话，确保新版本规则生效
