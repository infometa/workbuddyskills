# MCP 插件调用与接入

平台上 `pluginKind = 2` 的插件（例如「可灵视频生成」）通过统一的 Streamable HTTP MCP 网关对外提供工具列表与直接调用能力。

> **相关索引**：MCP 网关鉴权使用的是 **ADP API Key（工具密钥，`adp plugin key`）**，而非 CAM `SecretId`/`SecretKey` 或连接器出站凭证。工具密钥的创建、查看、启停、删除与 2 把配额上限处理，详见 [credentials.md](credentials.md#工具密钥adp-api-key)；插件调用第三方服务所需的出站凭证与 OAuth 授权，见 [credentials.md](credentials.md#连接器与插件出站凭证adp-credential)。

---

## 1. 平台 MCP 网关地址与协议

- **固定地址格式**：`https://adp.cloud.tencent.com/plugin/mcp/<pluginId>/mcp`
- **传输协议**：MCP JSON-RPC 2.0（Streamable HTTP），依次执行 `initialize`、`notifications/initialized`，再执行 `tools/list` 或 `tools/call`。
- **鉴权方式**：请求头 `Authorization: Bearer <ADP API Key>`。CLI 仅向该网关白名单前缀发送 Bearer Token，且拒绝重定向。
- **密钥读取顺序**：`--api-key-env <变量名>` → 环境变量 `ADP_API_KEY` → 本地文件 `~/.adp/tool-key`（由 `adp plugin key create` 默认以 `0600` 权限写入，见 [credentials.md](credentials.md#工具密钥adp-api-key)）。若显式传了 `--api-key-env` 但对应变量为空，CLI 会直接报错而不会回退到其他密钥。

---

## 2. 直接调用 MCP 插件（如可灵）

1. **查找 MCP 插件 ID**：先用 `adp space list --format json` 获取空间 ID，再执行 `adp plugin list --space-id <id> --query "可灵" --format json`，确认目标插件的 `pluginKind` 为 `2`（例如可灵视频生成插件 ID 形如 `651c15de-2756-40f5-9c91-442a48767065`，以实际查询结果为准，不要凭记忆硬编码）。
2. **查看工具与入参 Schema**：
   - 从平台目录读取：`adp plugin get --space-id <id> --plugin-id <id> --format json` 查看 `tools[]` 的 `toolId` 与 `name`，再用 `adp plugin tool get --plugin-id <id> --tool-id <toolId> --format json` 查看单个工具的入参/出参定义。
   - 从 MCP 网关实时读取：`adp plugin tool list --plugin-id <id> --format json` 直接向 MCP Server 发送 `tools/list`，返回所有实时工具的 `name`、`description` 与 `inputSchema`。
3. **准备工具密钥**：若本机尚无 `~/.adp/tool-key` 且未设置 `ADP_API_KEY`，先运行 `adp plugin key create --format json` 生成并保存工具密钥（或在调用时加 `--auto-create-key`）。如遇密钥数量上限（`ToolKeyLimitReached` / `4509400`），按 [credentials.md](credentials.md#工具密钥adp-api-key) 先禁用并删除闲置密钥后再创建。
4. **发起工具调用**：

```bash
# 按工具名直接调用（无需额外请求 Cloud API 反查名称）
adp plugin tool call --plugin-id <id> --tool-name SubmitKlingTextToVideoJob --input '<json>' --format json

# 按工具 ID 调用（CLI 自动通过 DescribeTool 反查工具名后再调 MCP）
adp plugin tool call --plugin-id <id> --tool-id <toolId> --input '<json>' --dry-run --format json

# 实时列出 MCP 服务端工具及 JSON Schema
adp plugin tool list --plugin-id <id> --format json
```

### 调用参数与注意事项

- `--tool-name` 与 `--tool-id` 二选一即可；同时传入但名称不一致时报 `UsageError`。
- `--input`（别名 `--args`）接收 JSON 对象字符串，默认为 `{}`。
- `--dry-run`：仅预览将要请求的 MCP URL、工具名与解析后的参数，不发送 HTTP 请求。即使本机尚未配置工具密钥且未传 `--auto-create-key`，`--dry-run` 仍会成功返回预览（`hasKey: false`），并提示在真实调用前执行 `adp plugin key create` 或加 `--auto-create-key`。
- `--auto-create-key`：当本机没有可用工具密钥时，自动创建一把写入 `~/.adp/tool-key` 并完成调用，全程不在输出中打印明文；与 `--dry-run` 同用时仅标记 `wouldCreateKey: true`，不会真正创建密钥。
- `--timeout-ms`：默认 `60000`（60 秒），提交视频生成等耗时任务时可适当调大（上限 `600000`）。
- **异步任务两步走**：视频生成等长耗时工具通常拆分为 `Submit*`（如 `SubmitKlingTextToVideoJob`）与 `Query*`（如 `QueryKlingTextToVideoJob`）。先调 `Submit*` 从返回结果中取出任务 ID（如 `data.id`），再将其作为 `{"task_id": "<id>"}` 传给对应的 `Query*` 工具轮询状态。

---

## 3. 将导出的 MCP 插件无缝装入任意 Coding Agent（CLI + Skill 方式）

无需在各个 Coding Agent 的 `mcp.json` 中硬编码明文 Bearer Token，通过 `adp` CLI + Skill 即可在 `claude`、`cursor`、`codex`、`agents`、`codebuddy`、`workbuddy` 中安全、无缝地调用任何 ADP MCP 插件：

1. **方式一：安装通用 `adp` 伴生 Skill（推荐，一次安装即可按需调用全部 MCP 插件）**
   - 预览安装目录：`adp skills install --dry-run --format json`（支持 `--scope global|project` 与 `--agent cursor,claude,codex,agents,codebuddy,workbuddy`）。
   - 执行安装：`adp skills install --yes --format json`（WorkBuddy 连接器环境已内置，无需执行）。
   - 确保本机已通过 `adp plugin key create --format json` 生成并缓存 `~/.adp/tool-key`（权限 `0600`，详见 [credentials.md](credentials.md#工具密钥adp-api-key)）。此后任何安装了该 Skill 的 Coding Agent 均可按本页第 2 节自动发现并调用目标插件。
2. **方式二：为特定 MCP 插件派生独立专属 Skill（适合高频使用的单一插件，如“可灵”）**
   - 先执行 `adp plugin get --space-id <id> --plugin-id <pluginId> --format json` 与 `adp plugin tool list --plugin-id <pluginId> --format json`，获取该插件全部工具的 `name`、`description` 和 `inputSchema`。
   - 确认本机工具密钥已就绪（`adp plugin tool list` 返回 `hasKey: true`）。
   - 在目标 Coding Agent 的 skills 目录（全局如 `~/.cursor/skills/<skill-name>/SKILL.md`、`~/.claude/skills/<skill-name>/SKILL.md`，或项目级 `.cursor/skills/`、`.claude/skills/` 等）创建专属 `SKILL.md`：
     - Frontmatter 的 `description` 写明该插件的能力与触发词。
     - 正文写明固定的 `--plugin-id <pluginId>`、各工具的 `name` 与入参 JSON Schema，以及标准调用模板：
       `adp plugin tool call --plugin-id <pluginId> --tool-name <ToolName> --input '<json>' --format json`
     - **严禁**将 `ADP_API_KEY` 明文写入 `SKILL.md` 或 `mcp.json`；调用时由 `adp plugin tool call` 自动从 `~/.adp/tool-key` 或环境变量读取（安全规则见 [credentials.md](credentials.md#安全规则)）。

---

## 4. 在空间目录中注册自定义外部 MCP Server

若要将外部自建的 MCP Server 注册为 ADP 空间中的插件（供应用内 Agent 绑定使用）：

```bash
adp plugin create --space-id <id> --name <name> --mcp-url https://your-mcp-server.example/mcp --mcp-transport 1 --icon-url https://cdn.xiaowei.qq.com/static/adp/app-default-avatar.png --format json
adp plugin update --space-id <id> --plugin-id <id> --mcp-url https://your-mcp-server.example/mcp --mcp-transport 1 --format json
```

- `--mcp-transport`：`0` 表示 SSE + HTTP，`1` 表示 Streamable HTTP。
- 平台在创建和更新时会立即连接 `--mcp-url` 校验连通性，因此地址必须是真实可达的线上地址（占位域名会报 `460030`）。
