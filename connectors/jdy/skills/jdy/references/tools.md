# 金斗云 MCP 工具参考

## `get_context`

用途：读取当前 OAuth 授权员工的实时身份和权限上下文。每个新任务必须首先调用。认证令牌由连接器管理，不作为业务工具参数传入。

参数：无。

主要返回字段：

- `staff`：员工 ID、用户名和昵称。
- `identity`：身份数值与名称。
- `role`：实时角色 ID、名称和描述。
- `stores`、`headquarters`、`warehouses`：按业务类型分开的授权节点，每项包含 `id`、`name`、`alias`、`region_id`、`node_type`。
- `regions`：授权区域。
- `all_stores`、`all_headquarters`、`all_warehouses`、`all_regions`：对应范围是否为全部。
- `openapi_resource_uri`：可选 MCP Resource 入口。普通任务无需依赖 Resources。

## `search_api`

用途：从当前角色有权调用的 Gin API 中搜索匹配 operation，并返回完整 OpenAPI 3.1 参数和 Schema。

参数：

- `query`，string，必填，1 到 200 个字符。可以是接口中文名称、用途、HTTP method、path 或 API ID。
- `limit`，integer，可选，默认 5，范围 1 到 10。

返回：

- `query`：实际搜索词。
- `match_count`：全部匹配数。
- `returned_count`：本次返回数。
- `openapi`：匹配 operation 的完整 OpenAPI 文档。调用 `call_api` 时使用 operation 的 `x-jdy-api-id`。

当 `match_count` 大于 `returned_count`，或结果含多个不同业务类型时，使用更具体的业务词缩小搜索范围。

## `call_api`

用途：以当前员工身份调用 `search_api` 找到的授权接口。

参数：

- `api_id`，string，必填。必须原样使用 operation 的 `x-jdy-api-id`。
- `query`，object，可选。每个查询参数的值都是字符串数组，例如 `{"page":["1"],"keyword":["戒指"]}`。
- `body`，任意 JSON，可选。用于 JSON 请求体。
- `form`，object，可选。每个表单字段的值都是字符串数组；不能与 `body` 同时使用。
- `files`，array，可选。每项包含必填的 `field`、`filename`、`data_base64`，以及可选的 `content_type`。文件内容使用标准 Base64。

返回：

- `status_code`：原 API HTTP 状态码。
- `body`：原 API 返回的 JSON 或文本。
- `truncated`：响应是否因大小限制被截断。

文件上传只能与 `form` 一起使用。调用前必须完全遵循 `search_api` 返回 operation 的 content type、参数位置、必填字段、枚举、长度和格式约束。

## `get_monthly_report`

用途：为当前用户可管理的全部门店读取经营月报聚合数据。只允许实时 Role 有效且身份为区域经理及以上的员工调用。

参数：

- `year`，integer，可选，报告年份。
- `month`，integer，可选，范围 1 到 12。

`year` 和 `month` 必须同时提供或同时省略；同时省略时使用最近完成月份。

本工具没有门店筛选参数。用户限定单店/部分门店时不得调用全部门店月报再过滤，改为发现支持服务端门店筛选的授权接口，找不到则停止。受三个月权限限制的员工还需核对整个月份是否全部位于允许范围内，不能用月报访问边界之前的数据。

返回包含 Boss 净收入、目标、门店、品牌/大类/品类及交叉分析、黄金/JW 商品结构、换金克重、黄金手镯/钻戒专项和员工表现，不包含会员或订单明细。月报范围只包括 `node_type=store` 的门店。

## `submit_feedback`

用途：把程序/逻辑错误或具体改进建议发送到配置的反馈接收渠道。调用前必须获得用户确认。

参数：

- `feedback_type`，string，必填：`error` 或 `suggestion`。
- `user_question`，string，必填，1 到 2000 个字符，保留用户原始问题但移除凭证。
- `summary`，string，必填，1 到 2000 个字符，概括根因、影响和可行改进。
- `errors`，string array，`error` 类必填，按顺序包含初始错误和每次重试错误，最多 4 条。
- `retry_count`，integer，范围 0 到 3，必须等于 `errors.length - 1`。

`suggestion` 类不传 `errors` 和 `retry_count`。返回 `sent: true` 表示提交成功。反馈中不得包含 API Key、Token、密码、机器人 key 或完整请求头。
