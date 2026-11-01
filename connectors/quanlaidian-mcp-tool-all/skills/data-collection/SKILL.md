---
name: data-collection
description: Collect authorized Quanlaidian business data through the configured quanlaidian-mcp-tool-all MCP server. Use when a user asks to query, summarize, compare, or explain permitted business data.
metadata:
  ai.workbuddy.description_zh: "通过已授权的 quanlaidian-mcp-tool-all MCP Server 查询全来店业务数据。只读、不接触凭据，输出事实与证据。"
  ai.workbuddy.description_en: "Collect authorized Quanlaidian business data through the quanlaidian-mcp-tool-all MCP server. Read-only, no credential handling, facts and evidence only."
---

# 全来店数据采集

本 Skill 只使用名为 `quanlaidian-mcp-tool-all` 的 MCP Server，固定请求头为
`X-Mcp-Biz-Scene-Code: MCP_TOOL_ALL`。`MCP_TOOL_ALL` 只标识 Gateway 的授权场景，
不表示可以绕过 Tool ACL、主体范围或写操作确认。

## 连接与授权

1. 由 WorkBuddy 宿主按标准 MCP OAuth（OAuth 2.1 + PKCE）完成发现、动态注册与
   浏览器授权。不要修改 Server URL、场景 Header 或启用状态，也不要手工添加认证
   Header 或构造授权参数。
2. 授权的 Client 绑定固定 BizScene；本连接器固定使用 `MCP_TOOL_ALL`。访问令牌按
   Gateway 策略过期后，宿主会收到 `401` 并重新引导授权；不要自行处理或传递令牌。
3. 永远不索取、不复述、不回显账号、密码、验证码、授权码或访问令牌；
   用户主动提供这类信息时，提示其在宿主授权窗口中完成，并建议轮换已泄露的凭据。
4. 每次业务查询前先读取当前 MCP 会话的 `tools/list`。只使用当前目录实际返回、名称、
   描述、输入 schema 与只读语义均明确的 Tool；不得猜测 Tool 名、参数、默认范围或返回字段。
5. 若任一 MCP 请求返回 `401` 且服务端提供 OAuth 挑战信息，立即停止业务调用，让
   WorkBuddy 宿主按标准 MCP OAuth 重新连接。重新授权后从新的 MCP 会话和 `tools/list`
   重新开始；仅当原请求明确为只读时最多重试一次。
6. `403` 是授权、主体、场景或 Tool ACL 问题；重新读取目录或请管理员处理。`429` 最多按
   `Retry-After` 重试一次；`503` 最多按服务端 `hint` 重试一次。以上结果都不要求用户
   手动配置凭据。
7. 单次请求超时（连接配置默认 60 秒）时不要并发堆叠重试；仅当原请求明确为只读时最多
   重试一次，仍超时则停止并报告未完成，附 `traceId` 与服务端 `hint`（若有）。
8. 参数被拒绝（`invalid_params`、schema 校验失败或必填字段缺失）时，按 `tools/list`
   返回的 schema 修正一次；不得猜测字段、枚举或默认值，仍失败则停下并指出缺失的输入。

## 查询流程

1. 确认时间范围、主体、门店/组织、业务对象和统计口径。任何会改变数据边界的条件缺失时先追问，
   不以“全部数据”替代。
2. 从 `tools/list` 中选择最小的只读 Tool。参数必须来自用户输入、当前授权上下文或上一步 Tool 返回；
   只发送 schema 要求且已确认的参数。
3. 先核验响应中的时间、主体、组织和口径。只有在第一步结果不足以回答且仍为只读时，才补充一次最小查询。
4. 合法空结果表示查询成功但无匹配记录；错误响应不是零值、空结果或业务结论。

## 输出

按以下顺序输出：

1. `查询范围`：时间、主体、门店/组织和统计口径。
2. `事实`：直接引用 Tool 返回的数量、金额、状态或标识。
3. `判断`：只解释由当前事实支持的关系，不把相关性写成原因。
4. `未验证`：缺失字段、空结果、范围不一致或下游失败。
5. `证据`：Tool 名、关键返回字段和 Gateway `traceId`（若有）。
6. `下一步`：补充范围、缩小查询或人工核验建议。

## 安全边界

- 只读：仅调用明确为查询、统计、获取或查看且不改变服务端状态的 Tool。
- 不得执行写操作、创建、更新、删除、提交、发布、保存、审批、退款、库存变更或批量导出。
- 不得导出全量敏感明细，不跨场景，不更换主体，也不构造或转述认证凭证。
- 对高风险或语义不明确的 Tool，停止并请求用户明确目标；不要把 `MCP_TOOL_ALL` 解释为自动授权。

## 维护验证

在 Gateway 仓库根目录运行 `bash mcp-collector/scripts/validate-connector.sh`。
该检查会读取本文件并断言授权、只读、错误处理和凭据边界；它是本地静态契约验证，不代表远端 MCP 运行时验收。
