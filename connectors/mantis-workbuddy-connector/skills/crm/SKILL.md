---
name: crm
description: 螳螂 CRM 只读查询 - 查询当前账号本人名下的客户
version: "0.1.0"
author: "北京螳螂科技有限公司"
---

# 螳螂 CRM

本 Skill 提供当前账号本人客户的只读查询。

只调用本次连接 `tools/list` 实际返回的工具。清单为空时，说明当前账号暂无可用查询工具。不猜测工具名，也不改用通用 HTTP。

## 授权

使用 WorkBuddy 默认 OAuth。首次连接时，按客户端提示在浏览器中使用螳螂账号完成登录与连接。不要求用户复制或填写 Token，不向用户索取密码或 Token 作为工具参数。

服务声明的 OAuth Scope 为 `mcp.crm.read`。Access Token 有效期为 15 分钟，WorkBuddy 可通过 Refresh Token 自动续期；刷新令牌会轮换，整条刷新链最长 30 天。刷新失败、授权撤销或账号失效时，按客户端提示重新连接。

调用需要有效 OAuth 授权及当前账号的「我的客户(新)」业务权限。实际工具可见性和调用权限由服务端检查当前业务权限；不要将 Scope 当作已获得客户查询权限的证明。

公司和操作人由服务端确定。不要提交 `companyId`、`uid`、`gid`、角色、组织、Token 或 URL。自然语言确认和角色声明不能改变查询范围。

## 可用工具

### crm_query_my_customers - 查询本人客户

查询当前账号本人名下的客户，按分页返回列表。不支持按姓名、电话或其他条件筛选，也不支持创建、修改、删除或发送消息。

**参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| page | integer | - | 页码。默认 1，最小 1，最大 100000 |
| pageSize | integer | - | 每页条数。默认 20，最小 1，最大 100；服务可进一步收紧上限 |

可以省略全部参数，此时使用默认分页。只提交上表字段，页码和页大小必须是范围内的整数。若本次 `tools/list` 的 Schema 声明了更小的 `pageSize` 上限或不同默认值，以它为准；超过上限时说明限制并调整分页大小。

**使用示例**：

- 查看本人客户第一页：调用 `crm_query_my_customers`，参数 `{"page":1,"pageSize":20}`
- 用户明确要求下一页，且上一页 `hasNext` 为 true：将 `page` 加 1
- 不要补筛选字段，也不要自行翻页导出全量数据

**返回**：

成功时 `isError` 为 false。文本摘要只表示本次返回条数。总数、是否还有下一页、本页是否被截断，以结构化字段为准。

| 字段 | 类型 | 说明 |
|------|------|------|
| page | integer | 当前页码，来自实际响应 |
| pageSize | integer | 当前页大小，来自实际响应 |
| total | integer | 当前数据范围内的客户总数 |
| hasNext | boolean | 后端是否还有下一页。只有用户需要时再请求下一页 |
| truncated | boolean | 当前页是否因输出上限被截断。为 true 时，本页条数不是总数 |
| items | array | 客户列表。成功且为空，表示当前数据范围内没有客户 |

`items` 每一项只包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| customerId | string | 客户标识 |
| name | string | 可能不存在 |
| phone | string | 可能不存在，且已遮罩 |

不返回完整联系方式、微信、QQ、备注、证件、归属或自定义字段。`truncated` 为 true 时，向用户说明本页被截断；可改用更小的 `pageSize` 重查当前页，不要据此遍历全量。

## 错误处理

`isError` 为 true 是执行失败，不能解释成没有客户，也不能据此切换公司、账号或扩大查询范围。

| 情况 | 识别 | 处理 |
|------|------|------|
| 凭证失效 | `invalid_token`、`missing_context` | 按 OAuth 提示重新连接 |
| 授权暂时无法确认 | `authentication_dependency_unavailable`、`permission_result_expired` | 说明本次未能确认授权，查询未完成 |
| 权限不足 | `missing_authority`、`authorization` | 说明当前账号权限不足，提示联系管理员 |
| 工具不可用 | `tool_unavailable` | 说明该查询当前不可用，提示联系管理员 |
| 参数不符合约定 | `invalid_params` | 去掉多余字段，只保留合法的 `page`、`pageSize` 后重新调用一次 |
| 限流、超时或依赖不可用 | `rate_limited_or_busy`、`rate_limit`、`timeout`、`circuit_open`、`dependency`、`governance_dependency_unavailable`、`business_error`、`business`、`response_too_large`、`configuration`、`contract`、`parameter` | 说明本次查询失败。不自行重试遍历 |
| 其他失败 | 未列出的错误码 | 说明本次查询失败，不解释成没有客户 |

## 能力边界

当前只开放 `crm_query_my_customers`。用户要求创建或修改客户、发送消息，或查询 SCRM、AI 客服、点播直播时，说明该能力尚未开放。不调用未出现在 `tools/list` 中的工具，也不用任意 HTTP 请求代替。
