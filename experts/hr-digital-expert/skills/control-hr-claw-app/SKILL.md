---
name: control-hr-claw-app
description: "通过 deliver-api 的 /app-mcp MCP 服务访问和控制当前用户可见的 HRClaw（hr-claw-app）应用。Use when the user asks to 查询应用、调用应用工具、通过应用执行任务、操作 HRClaw 应用、查看 HRClaw 应用能做什么，或使用 list_apps / list_app_tools / call_app_tool / app_id / toolName / args。本 skill 只调用已上线应用的业务能力，不负责生成代码、部署、开启 MCP 或维护 restful.json。"
---

# 控制 HRClaw 应用

通过 `/app-mcp` MCP 服务发现、访问和调用当前用户可见的 HRClaw 应用。所有执行都只经过
平台工具 `list_apps`、`list_app_tools`、`call_app_tool`，不直接访问应用地址，也不走部署
平台内部接口。

## 执行原则

1. 目标应用以 `list_apps` 的返回值为准，当前用户可见即视为可处理；权限由平台侧校验。
2. 应用工具契约以 `list_app_tools` 的返回值为准，每次任务对同一应用默认只读取一次，
   不猜测工具名和参数；仅 `TOOL_NOT_FOUND`、`SPEC_UNAVAILABLE` 按错误处理规则最多刷新
   一次。
3. 身份由 `/app-mcp` 网关注入，本 skill 不收集、不保存、不转发 token、staffId、staffName
   或任何用户凭据。
4. 只读查询直接执行；删除类操作必须先展示目标、参数和影响，得到用户明确确认后才调用。
5. 本 skill 不生成、不修改 `restful.json`，不部署、不发布应用，不负责把接口 MCP 化。

## MCP 连接

页面部署插件的 MCP 配置中服务名为 `hr-claw-app`，CodeBuddy 完整路径通常为
`HRIT/page-deliver/hr-claw-app`。WorkBuddy 或其他宿主可能暴露短名或转换后的名称。

调用前按以下顺序探测可用工具名，探测到哪个就使用哪个，不要把单一命名写死：

1. `HRIT/page-deliver/hr-claw-app.list_apps`
2. `hr-claw-app.list_apps`
3. 宿主实际提供的同名工具（如 `mcp__hr_claw_app__list_apps`）

访问应用只能通过 MCP 提供的三个平台工具，调用时遇到不可用、连接失败或返回 401/403 时停止执行，提示用户检查
`hr-claw-app` MCP 连接与登录状态。不要回退到 REST、shell 或平台内部接口。

## 工作流

1. **明确目标**
   - 从用户请求中确认目标应用和期望动作。
   - 如果用户只给了业务场景，先调用 `list_apps`，再按名称和描述选择候选。
   - 无法确认唯一应用时列出候选，由用户选择；不猜测 `app_id`。

2. **列出可见应用**
   - 调用 `list_apps`，每个任务对同一查询只调用一次。
   - 返回值为应用摘要：`app_id`、`name`、`description`。
   - 列表为空时停止，按平台返回的提示向用户说明当前没有可用应用能力。

3. **定位应用**
   - 优先匹配 `app_id` 或 `name` 与用户输入完全一致的结果。
   - 无精确匹配时按 `name` / `description` 做包含匹配。
   - 只有一个候选时使用该应用；多个候选时展示 `app_id`、`name`、`description`，请用户确认。
   - 零结果或用户无法确认时停止，不尝试使用列表外的应用。

4. **读取工具契约**
   - 对选定应用调用 `list_app_tools`，每次任务默认只调用一次。
   - 仅 `TOOL_NOT_FOUND`、`SPEC_UNAVAILABLE` 时按错误处理规则最多刷新一次。
   - 从返回的工具定义中选择与用户意图最匹配的工具。
   - 工具名、HTTP 方法、路径、参数名、参数位置、类型和必填性都只以该返回值为准。

5. **构造并调用工具**
   - 按 `call_app_tool` 的要求传入 `appId`、`toolName` 和 `args`。
   - `args` 必须是 JSON 字符串，解析后必须是 JSON 对象。
   - `args` 解析后的键名必须与工具契约 `parameters[].name` 完全一致；不添加未声明参数。
   - 未声明的参数不会报错，而是被平台静默丢弃（query 键直接忽略、body 缺失键跳过），
     path 占位符缺失才会报 `BAD_ARGS`。因此调用后若结果与预期不符，先核对参数名与 `in`
     位置，不要假设参数已生效。
   - `args` 总大小不得超过 32KB（UTF-8 字节），超限直接返回 `BAD_ARGS`；不要把超长列表
     作为入参传入，改用分页或过滤参数缩小入参体积。
   - `body` 参数只保留参数名这一层：例如 `parameters[].name` 为 `item` 时传 `"{\"item\":{\"name\":\"示例\"}}"`，不得扁平化成 `"{\"name\":\"示例\"}"`。
   - `callExample.good` 是外层 JSON 字符串格式的调用示例；只能作为格式参照，值仍需按用户需求构造。
   - 必填参数必须给出非空值；日期、枚举、格式等按参数描述构造。
   - 删除类工具先执行下面的「删除确认门禁」。

6. **解释结果**
   - 以 `call_app_tool` 返回的 `success`、`code`、`message`、`data` 为准。
   - 成功时向用户解释业务数据或操作结果；涉及员工、组织、绩效等敏感数据时默认只摘要展示。
   - 失败时原样区分平台拒绝和应用业务错误，不伪造成功，也不额外猜测应用内部状态。

## 删除确认门禁

同时满足任一条件即视为删除类工具：

- 工具契约的 `method` 为 `DELETE`
- 工具名或 `summary` 含 `delete`、`remove`、`clear`、`reset`、`注销`、`删除`、`清空`、
  `重置` 等删除语义

删除类工具调用前必须向用户展示：

- 目标应用：`app_id`、`name`
- 工具名与参数值
- 工具契约中的功能摘要
- 该操作可能影响的业务范围

用户明确确认后才调用。拒绝时立即停止。没有明确确认时，即使已经拿到完整参数也不得调用。

## 错误处理

`call_app_tool` 的返回结构包含 `code`。按以下规则处理：

| 返回结果 | 处理方式 |
|----------|----------|
| `success=true` | 正常解释 `data`，不额外验证 |
| `BAD_ARGS` | 不自动重试；停止并原样说明平台返回的参数错误，提示用户修正请求后可重新开始。若错误为「args 超过 32KB 硬限」，改为提示缩减参数体积或改用分页/过滤参数，不要当作参数名错误 |
| `APP_NOT_FOUND` | 停止，说明应用不存在或已下线。这与无权限（`PERMISSION_DENIED`）是不同原因，不要混为一谈；需要时可重新调用 `list_apps` 确认当前可见应用，不复用旧的 `app_id` |
| `TOOL_NOT_FOUND` | 重新读取一次 `list_app_tools`；若得到修正后的工具定义，先向用户展示并确认，再重新开始调用；仍不一致则停止，报告线上能力描述可能已变更 |
| `SPEC_UNAVAILABLE` | 先看 `message`：含「暂不可用」为应用可能已休眠，重新调用一次 `list_app_tools`，仍不可用则停止并建议稍后重试；含「与应用不匹配」为应用侧 `restful.json` 的 `appId` 写错，停止并提示联系应用 owner 修正，重试不会恢复 |
| `PERMISSION_DENIED` | 停止，按平台消息说明权限不足；不绕过权限、不换用户身份 |
| `MCP_NOT_SUPPORTED` | 停止，说明该应用未开启 MCP 能力 |
| `APP_ERROR` 且 `message` 以「应用返回」开头 | 应用已收到请求并返回非 2xx。原样报告状态码与应用返回内容；GET 最多重试一次，非 GET 不自动重试并询问用户 |
| `APP_ERROR` 且 `message` 以「转发失败」开头 | 请求未到达应用或没有拿到响应，不可能产生业务结果。按 GET/非 GET 均可最多重试一次；仍失败则停止并提示应用可能未运行或网络不通 |
| MCP 连接失败或鉴权失败 | 停止，提示检查 `hr-claw-app` MCP 连接与登录状态 |

## 目标不在列表中

如果用户明确提到的应用没有出现在 `list_apps` 中，停止处理，只提示“无权限或应用已下线”。
不暴露应用地址、平台校验逻辑或其他技术细节，也不尝试用猜测的 `app_id` 调用。

## Do Not

- 不使用 `/app-mcp` 三个平台工具之外的 REST、shell 或平台内部接口访问应用
- 不猜测或伪造 `app_id`、工具名、参数名和参数值
- 不收集、不保存 token、staffId、staffName 等身份信息
- 不把返回数据写入文件、部署状态或跨任务缓存
- 不生成、修改或部署 `restful.json`
- 不绕过权限、不自动重复删除类操作，也不在没有确认时执行删除
- 不在平台已经返回明确失败时声称操作成功

## Completion Criteria

- 目标应用确实来自当前 `list_apps` 结果，工具定义来自该应用的 `list_app_tools` 结果
- `call_app_tool` 已返回，且结果按 `success / code / message / data` 如实解释给用户
- 删除类工具已取得用户明确确认；敏感结果已按约定摘要展示
- 未写入任何项目文件、状态文件或身份凭据
