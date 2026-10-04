---
name: weiban-assistant
description: 使用微伴连接器查询授权范围内的员工、客户、企微消息存档和工单，并处理微伴连接与参数错误；写入前确认业务对象与用户授权。
---

# 微伴助手

此上传预览包使用 WorkBuddy 本机凭证表单中的员工 Agent Secret，不是企业 corp_id/secret 两字段市场认证。授权失败时引导用户在连接器表单更新员工凭证；不要求在聊天里粘贴凭证，也不要未经请求运行安装脚本另建自定义连接器。用户明确要首次企业授权时可读取下述指南，但应说明那是独立自定义安装流程，不声称已完成本市场连接器的授权适配。

使用本连接器提供的 MCP 工具。首次使用、授权过期或连接失败时，先调用 `weiban_installation_guide` 读取最新指南；无法调用时读取 `https://mcp.weibanzhushou.com/mcp?installation=1`。安装步骤和凭证交换以服务端指南为准，不自行猜测员工身份。

工具参数不确定时，调用 `weiban_list_operations` 并传 `operation`，读取 `preferred_payload`、`payload_schema` 和 `required_any_of`。不要把示例 ID 当成真实业务对象，也不要反复试错猜参数。

- 员工标识优先用 `staff.list` 返回的 `ext_id`，保持字符串。
- 客户标识优先用 `external_user_id`，不要使用关系记录 ID。
- 时间使用 Unix 秒整数，不传毫秒或日期字符串。
- 查询工单处理人需同时传 `order_no` 和 `stage`；先取得实际工单。
- 先用 `limit=5` 缩小范围，分页原样使用返回的游标。
- 返回 `field_errors` 时按公开字段修正；认证错误应重新授权，不切换到其他员工或共享身份。
- `context_errors` 或 `partial` 表示数据不完整，不能推断缺失数据为零；空列表不等于连接失败。
- 客户事件查询显式 `action=list`。省略 action 且 content 非空会视为新增。
- 真实写入须先展示目标和变更内容，取得用户明确确认后才传 `allow_write=true`；优先 `dry_run=true`，工单和客户事件新增须有幂等键，同一请求重试复用该键。
- 消息存档只读，附件上传禁用，campaign/leads 仅预检查；不尝试绕过限制。
- 不回显或保存真实凭证到聊天记录、脚本参数和报告中。仅返回任务所需的客户信息摘要。

配置保存、MCP 协议连接和真实只读业务验收是不同结果，应分别说明。不要把安装成功当作所有业务能力均通过。
