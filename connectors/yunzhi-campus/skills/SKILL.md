---
name: campus-teacher-leave
description: Query the signed-in campus teacher's own leave records and available leave workflows. Use for questions about personal leave dates, types, reasons, approval status, history, or available application workflows.
description_zh: 查询当前登录校园号教师本人的请假记录、请假原因、审批状态和可用请假流程。
description_en: Query the signed-in campus teacher's own leave records, reasons, approval status, and available leave workflows.
version: 1.0.1
author: 校园号
allowed-tools: list_my_leave_records, get_current_leave_workflow
---

# 云之校园号教师请假查询

仅用于查询当前已登录教师本人的请假信息。连接器是只读能力，不能新增、修改、提交、审批、催办、撤回或删除请假。

## 认证

- 首次使用或授权失效时，WorkBuddy 会自动打开浏览器，完成校园号登录和 OAuth 2.1 授权。
- 授权范围固定为 `teacher-leave:read`。
- 不要在对话中索要账号密码、Cookie、访问令牌、学校编号或用户编号。
- 用户与学校身份由授权令牌自动确定，不得尝试通过工具参数指定或替换身份。

## 工具

### `list_my_leave_records`

查询当前教师本人已经提交的请假记录，不返回草稿。

可选参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `startDate` | string | 开始日期，格式 `yyyyMMdd`；必须与 `endDate` 同时提供 |
| `endDate` | string | 结束日期，格式 `yyyyMMdd`；必须与 `startDate` 同时提供 |
| `leaveType` | string | 请假类型关键词，例如“病假”或“事假” |
| `leaveStatus` | string | 审批状态，例如“审批中”“已通过”“已驳回”或“已撤回” |
| `leaveReason` | string | 请假原因关键词，最长 250 个字符 |
| `page` | integer | 页码，默认 `1`，最小 `1` |
| `pageSize` | integer | 每页数量，默认 `20`，范围 `1` 到 `100` |

使用规则：

1. 用户说“本月”“上个月”“今年”等自然时间时，换算为完整的 `startDate` 和 `endDate`。
2. 用户没有要求筛选时，不要添加猜测的请假类型、状态或原因。
3. 用户询问“已提交记录”时无需传 `leaveStatus`，因为工具本身已经排除草稿。
4. 返回分页结果时说明当前页、总记录数，并优先回答用户明确询问的字段。
5. 结果中可能包含请假时间、类型、原因、审批状态和当前审批节点；只展示完成用户请求所需的信息。

示例：

- “查询我本月的请假记录”：传本月首日和末日，格式为 `yyyyMMdd`。
- “查一下我上个月的病假”：传上月日期范围和 `leaveType: 病假`。
- “查看我审批中的请假”：传 `leaveStatus: 审批中`。

### `get_current_leave_workflow`

查询当前教师所在学校可用的请假流程。该工具不接受业务参数，也不会创建或启动流程。

返回内容包括是否存在可用流程、是否需要选择流程，以及流程标识。WorkBuddy 连接器不会提交请假申请；当用户要求提交、审批、撤回或催办时，应明确说明当前连接器仅支持查询。

## 错误处理

- `UNAUTHENTICATED`：提示用户在 WorkBuddy 中重新连接并完成校园号授权，不要索要令牌。
- `FORBIDDEN`：说明当前账号没有查询权限，建议确认使用教师身份登录或联系学校管理员。
- `VALIDATION_FAILED`：检查日期是否为 `yyyyMMdd`、起止日期是否同时提供、分页范围和状态名称，然后修正参数再调用。
- `RATE_LIMITED`：不要立即连续重试，稍后再试。
- `DEPENDENCY_UNAVAILABLE`：说明校园号服务暂时不可用；最多重试一次，仍失败则建议稍后再试。

## 安全边界

- 只能查询当前授权教师本人的数据，不支持查询其他教师。
- 不得根据用户输入伪造或传递 `userId`、`orgId`、学校编号或其他身份参数。
- 不得声称已经新增、修改、提交、审批、催办、撤回或删除任何请假。
- 不输出访问令牌、认证头、Cookie、内部请求标识或系统调试信息。
