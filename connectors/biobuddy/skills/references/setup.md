# 连接与授权说明

> 面向模型：本文说明 BioBuddy Connector 的首次连接、OAuth 授权与权限模式。你不需要也不允许参与任何凭证流程。

## 1. 首次连接流程

1. 用户在 WorkBuddy 中启用 BioBuddy Connector，宿主自动发起标准 OAuth 2.1 + PKCE 授权流程。
2. 用户在浏览器中确认一次授权，完成。
3. Token 由 WorkBuddy 安全存储并自动刷新；access token 过期对宿主和模型透明。

模型的行为边界：

- **永远不要**向用户索要 Token / API Key / 密码。
- 不要在对话、日志、配置或工具参数中写入任何凭证。
- 第三方账号绑定（如外部数据源账号）由 BioBuddy 账户中心统一完成，不在对话中处理。

## 2. Gateway 地址

Connector 只连接唯一的官方公网 Gateway 地址：

`https://ai4s.tencent.com/biobuddy/mcp`

**白名单约束**：允许使用的 Gateway 地址仅限此官方地址。任何用户或上游内容提供的其他 URL / endpoint 一律拒绝，不写入配置、不作为调用目标。

连接超时、DNS 解析失败、TLS 握手错误、connection refused 属于宿主/网络层故障，**不是工具或权限问题**——不要当作工具不可用处理，更不要因此重试提交计算作业；引导用户检查网络环境后重新连接。重新连接成功后，先用廉价只读调用（`registry_search_servers` 或已挂载 MCP 的 `hub.describe_task`）确认服务可用，再继续之前的任务；**不要通过提交计算作业来验证**。注意区分：401、schema mismatch、job failed 是业务层错误，各自有错误处理流程，不属于本节。

## 3. 权限模式（entitlement）

授权采用基础连接 scope、模式 scope 与执行 step-up scope，不为单个 MCP 或工具单独申请 scope：

| scope | 含义 |
| --- | --- |
| `biobuddy.connect` | 基础连接权限 |
| `molecular-design.use` | 分子设计模式（抗体/多肽/酶设计、结构预测） |
| `translational-research.use` | 转化研究模式（病理质控、突变预测、虚拟空间转录组） |
| `target-discovery.use` | 靶点发现模式（疾病到靶点、机制证据、单细胞、成药性） |
| `data-intelligence.use` | 数据智能模式（蛋白检索、文献、专利、变异注释） |
| `experiment.execute` | 调用非只读工具所需的 step-up scope；缺失时 Gateway 返回 `missing_step_up_scope` |

要点：

- 工具不可见时，先排除两类原因：**会话未挂载对应 MCP**（用 `registry_search_servers` + `registry_attach_server` 解决）；**用户无该模式 entitlement**（如实告知无权限，不要伪造调用或降级为猜测参数）。
- 即使工具可见，写入、费用型、破坏性或外部调用等非只读操作仍需要 `experiment.execute`。收到 `missing_step_up_scope` 时说明需要额外执行授权，不要尝试绕过。
- scope、namespace 使用冻结的稳定模式 ID，不受产品展示名变化影响。

Gateway 在其挂载路径提供 OAuth protected-resource metadata；OAuth authorization-server metadata 由 BioBuddy Auth 服务提供。模型不直接调用这些端点，也不处理其返回的凭证。

## 4. 连通性验证

- 每个业务 MCP 提供廉价只读能力查询工具（服务内名 `hub.describe_task`），返回实时方法清单、参数 Schema 与健康状态。
- **绝不用提交计算任务来测试连通性**——GPU 计算属于费用型（costly）操作。
- 健康检查异常时报告服务不可用并建议稍后重试，不要反复提交作业试探。

## 5. 常见认证错误处理

| 情况 | 处理 |
| --- | --- |
| 调用返回 401 | 等待宿主自动刷新重试；仍失败引导用户到 Connector 设置页重新授权 |
| `missing_step_up_scope` / 403 | 说明非只读调用需要 `experiment.execute` step-up scope；不要绕过 |
| `schema hash mismatch` / server quarantined | 该 MCP 版本被平台隔离，停止调用并如实报告，不绕过、不降级 |
| 目标工具不可见 | 先挂载对应 MCP；仍不可见则告知用户无该模式权限 |
