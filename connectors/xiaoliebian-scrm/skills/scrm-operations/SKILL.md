---
name: scrm-operations
description: |
  Perform confirmed Xiaoliebian SCRM write operations.
description_zh: |
  小裂变 SCRM 的受控写操作技能。用户要创建、编辑、删除、发送、停发、发布、提醒，或切换活动、抽奖、红包工具状态时使用。
  仅处理明确的写操作；普通查询和分析使用 `scrm`。所有写操作必须先复述目标与影响并取得用户明确确认，再通过 MCP 执行。
description_en: |
  Perform explicit Xiaoliebian SCRM write operations after user confirmation. Use `scrm` for queries and analysis.
version: 1.2.0
author: Xiaoliebian
---

# 小裂变 SCRM 受控运营操作

本 Skill 只处理有副作用的 SCRM 操作。普通列表、报表、分析和详情查询使用 `scrm`。

## 执行约束

- 调用前通过 MCP `tools/list` 核对完整工具名、参数 Schema 和必填字段；不得猜测工具或参数。
- 所有写工具都必须在用户明确确认后传入 `confirmed: true`。Skill 中的确认不能替代服务端校验。
- 用户未明确确认时不得调用写工具。删除、停发、撤销和关闭等不可逆或高影响操作，需要再次说明影响。
- 编辑前先查询详情，基于完整对象合并用户确认过的差异，避免清空未修改字段。
- 发送、发布和提醒前确认任务范围以及目标成员、客户群或账号。
- 写工具返回成功后只根据实际返回字段说明结果；必要时使用对应只读工具回查一次。
- 工具失败或返回空结果时如实反馈，不自动重复提交，也不改用其他方式绕过权限或确认限制。
- 图片上传使用 `imageBase64`，不传 MCP 服务端本地文件路径。图片内容必须有效且不超过 5 MB。
- 不向用户展示原始 JSON、Token、Cookie、密码或私钥。遇到 `401` 时让 WorkBuddy 自动续期；仍失败则提示用户重新连接。遇到 `403` 时说明当前账号或租户权限不足。

## 支持的写操作

| 场景 | 工具范围 | 前置流程 |
|---|---|---|
| 企微活动 | `scrm_event_update_state` | 确认活动类型、目标活动和目标状态 |
| 抽奖活动 | `scrm_lottery_update_state` | 确认目标活动和目标状态 |
| 红包工具 | `scrm_red_packet_tool_state` | 确认目标工具和目标状态 |
| 群发任务 | `scrm_custom_send_create`、`scrm_custom_send_update`、`scrm_custom_send_upload_image`、`scrm_custom_send_delete`、`scrm_custom_send_send`、`scrm_custom_send_stop_send` | 创建前查真实选项；编辑、删除、发送前定位任务 |
| 朋友圈任务 | `scrm_moment_create`、`scrm_moment_upload_image`、`scrm_moment_update`、`scrm_moment_delete`、`scrm_moment_publish`、`scrm_moment_stop_send`、`scrm_moment_cancel`、`scrm_moment_remind` | 创建时收集必要参数；编辑前查详情；提醒前查执行情况 |

实际工具名和参数以当前 `tools/list` 为准。

## 群发流程

1. 从用户表述识别客户群发 `single` 或客户群群发 `group`；不明确时询问，不猜测类型。
2. 创建前查询真实的人群包、标签、客户阶段、客户群和员工选项，收集必要参数后统一展示并确认。
3. 编辑前查询详情并合并完整任务对象，向用户展示差异后确认。
4. 用户要求附加图片时，先调用 `scrm_custom_send_upload_image` 获取返回的 `data.path`，再把图片项写入 `additionalMsgList` 并按工具 Schema 启用素材；不能只提交新增图片项。
5. 删除、立即发送、停止发送分别确认任务标识、影响范围和不可逆影响。

## 朋友圈流程

- 创建时先收集标题、文案、发送成员和发送方式；立即发送不传 `sendTime`，定时发送才传发送时间。
- 用户要求图片时，先调用 `scrm_moment_upload_image` 获取 `data.path`，按工具 Schema 设置媒体类型并写入图片列表。
- 编辑前读取完整详情和成员列表，只修改用户确认的内容；不得用局部对象覆盖原任务。
- 撤销定时发布前确认任务处于定时状态；提醒前查询员工执行情况并确认提醒范围。

## 时间与回复规则

- 询问时间时使用具体年月日、时分秒。用户只提供日期时，开始补 00:00:00，结束补 23:59:59；只到分钟时秒数补 00。
- 工具调用前用自然语言说明正在准备或确认什么，不向用户展示 `scrm_*` 工具名。
- 调用后用中文表格、列表或短摘要展示实际结果；不编造成功状态、进度或接口未返回的字段。

