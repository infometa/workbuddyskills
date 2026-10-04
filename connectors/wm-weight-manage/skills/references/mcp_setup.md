# 体重管理 MCP 服务端连接

仅在 `generate_weight_management_plan` 不可用、客户端尚未配置服务端地址，或用户明确要求联调 MCP 时使用。

## 连接原则

- MCP 工具必须通过用户部署的 Streamable HTTP 服务端调用。
- 不运行本地脚本实现或模拟 `generate_weight_management_plan`，不在客户端重做预检、计算、风险路由或正文生成。
- 本地 `render_plan.py` 只负责在服务端返回 `ready` 结构化结果后生成 HTML，不是 MCP 服务端替代品。
- 当前没有已知公网域名时，必须向用户索取真实地址，不能把示例地址当成可用配置。

## 客户端配置

服务端地址应是完整的 MCP endpoint。当前使用用户提供的公网地址：

```text
https://ichoice.myweimai.com/weimai-gpt/mcp
```

### WorkBuddy 客户端安装（推荐）

WorkBuddy 的 MCP 客户端配置位于 `~/.workbuddy/mcp.json`（注意是 `mcp.json`，**不是** `~/.workbuddy/.mcp.json`）。工具不可用时按以下步骤安装：

1. 先读取 `~/.workbuddy/mcp.json`（不存在则创建 `{"mcpServers": {}}`）。
2. 将新条目**合并**进 `mcpServers`，保留已有服务器，不得覆盖：

```json
{
  "mcpServers": {
    "generate_weight_management_plan": {
      "type": "mcp",
      "transport": "streamable_http",
      "url": "https://ichoice.myweimai.com/weimai-gpt/mcp",
      "disabled": false
    }
  }
}
```

- 默认使用公网地址 `https://ichoice.myweimai.com/weimai-gpt/mcp`。
3. 写回后**不会自动激活**：需告知用户打开连接器管理页右上角「自定义连接器」入口，对该服务器点击「信任」启用。
4. 用户信任后重新检查工具列表，`generate_weight_management_plan` 可用后再调用。

### 旧式 agent 配置（仅兼容参考）

以下 YAML 为历史 agent 配置格式（如 `agents/openai.yaml`），WorkBuddy 客户端以 `~/.workbuddy/mcp.json` 为准，两者选一即可，不要重复配置：

```yaml
interface:
  display_name: "Weight Management HTML"
  short_description: "安装或配置体重管理 MCP，并渲染产品风格独立 HTML"
  default_prompt: "Use $weight-management-html to set up the MCP connection and render the latest result as a standalone Chinese HTML plan."

dependencies:
  tools:
    - type: "mcp"
      value: "generate_weight_management_plan"
      description: "匿名体重管理方案 MCP 工具，返回结构化结果并支持正文进度通知。"
      transport: "streamable_http"
      url: "https://ichoice.myweimai.com/weimai-gpt/mcp"

policy:
  allow_implicit_invocation: true
```

如果 MCP Server 尚未启动，应由服务端启动现有 FastAPI 应用并暴露 `/mcp`；例如：

```bash
ENV_FOR_DYNACONF=default uv run python launch.py
```

Skill 可以引导用户启动这个真实 FastAPI 服务，但不通过本地脚本实现或替代 MCP 工具。

## 联调验收

完成客户端配置后，通过已配置的 MCP 客户端执行：

1. `initialize`：确认服务端可连接且无需应用登录 token。
2. `tools/list`：确认只有 `generate_weight_management_plan`。
3. `tools/call`：传入 `{"user_input":""}`，确认返回 `need_more_info`，不会触发模型生成。
4. 完整成人资料调用：支持 progress token 时确认收到有序正文片段，最终以 `structuredContent` 为准。
5. 确认未成年、孕期/哺乳期、低体重目标或需要医生监督的结果不能通过客户端绕过拒绝/澄清。
