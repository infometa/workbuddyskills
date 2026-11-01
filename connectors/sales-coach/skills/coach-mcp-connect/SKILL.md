---
name: coach-mcp-connect
description: MCP 连接诊断与恢复。当 MCP 工具不可用时，调用此技能恢复连接。
---

# Coach MCP Connect

当 MCP 工具无法使用时，此技能帮助用户恢复 MCP 连接。

## 快速判定表

| 现象 | 结论 | 动作 |
|------|------|------|
| 401 / invalid_token | token 过期或未配置 | 运行 `auth` → 复制 token → 配置 MCP client |
| 403 | 权限不足 | 联系管理员 |
| 406 Not Acceptable | 协议头问题，与认证无关 | **不要重跑 auth**，检查脚本 Accept 头是否包含 `application/json, text/event-stream` |
| 连接超时 / DNS 失败 | 网络不通 | 检查网络/代理/VPN |
| ToolSearch 查不到工具 | 宿主未注册 MCP | 进入「MCP Client 配置」章节 |

## 核心原则：脚本负责取 token，agent 负责配置 MCP client

**标准链路**：

1. **auth**：运行 `mcp_diagnose.py auth` → 浏览器 OAuth → 输出 token
2. **configure**：复制输出的 Authorization header 值（如 `Bearer at_...`），配置你的 MCP client
3. **reconnect**：在宿主连接器页 Trust/重连（如需要）
4. **native**：宿主注册原生 MCP 工具 → 所有业务调用走原生工具

> ⚠️ **关键说明**：
> - `mcp.json` 是技能包的服务器声明文件，包含 MCP URL。脚本读取它获取 URL。
> - **Authorization 配置由 agent 自行管理**，不要修改 mcp.json。
> - 不同环境的 MCP URL 不同，始终从 `mcp.json` 读取。

## 诊断流程（按顺序执行）

### 第 1 步：检查 MCP 工具是否可用

直接尝试调用 MCP 工具（如 `training.organization.tree`）：
- ✅ **成功** → 连接正常，无需本技能
- ❌ **失败（401/403）** → 认证问题，进入第 2 步
- ❌ **失败（其他错误）** → 网络/配置问题，进入第 2 步

### 第 2 步：检测宿主原生 MCP 通道

用 ToolSearch 查 `mcp__<服务器名>__*`（如 `mcp__sales-coach__*`）：
- ✅ **查到** → 宿主通道可用，无需本技能
- ❌ **查不到** → **不等待、不换名重试**，立即进入第 3 步

> ⚠️ **硬规则**：ToolSearch 只执行一次。禁止"换个名字再搜一次"——这不是排查手段，是浪费调用。

### 第 3 步：获取 token 并配置 MCP client

#### 3.1 浏览器授权拿 token

```bash
python3 skills/coach-mcp-connect/scripts/mcp_diagnose.py auth
```

- Token 落盘路径：
  - **Windows**：`%APPDATA%\coach-mcp-connect\<host>\tokens.json`
  - **macOS/Linux**：`~/.config/coach-mcp-connect/<host>/tokens.json`
- Token 有效期约 **15 天**（过期后需重跑 auth）
- 命令会输出完整的 Authorization header 值和配置示例

#### 3.2 配置 MCP client

复制命令输出的 Authorization header 值（如 `Bearer at_...`），按你的 agent 的标准方式配置 MCP client。

配置参数：
- **URL**：从技能包的 `mcp.json` 的 `mcpServers.*.url` 字段读取
- **Authorization**：使用 `mcp_diagnose.py auth` 输出的**值部分**（不含 `Authorization:` 标签）

**配置能力说明**：
- 如果你的 agent 支持自动配置 MCP client（如 Claude Code 可编辑 settings.json），直接配置即可
- 如果你的 agent 不支持自动配置，将 URL 和 Authorization 值提供给用户，指导用户手动配置
- 配置完成后，必须在宿主连接器页完成 Trust/重连，并通过一次原生只读调用验证连接成功

#### 3.3 宿主重连（必须手动）

> **配置修改不会自动生效**——必须让用户到宿主连接器页面执行 **Trust / 重连**，宿主才会重新读取配置并注册原生工具。

重连后用 ToolSearch 验证原生工具是否已注册。

#### 3.4 连通性检查（可选诊断）

```bash
python3 skills/coach-mcp-connect/scripts/mcp_diagnose.py tools
```

如果成功列出工具，说明 MCP 连接已恢复。此步骤仅用于诊断，非必须。

## MCP Client 配置

运行 `mcp_diagnose.py auth` 后，复制输出的 Authorization header 值（如 `Bearer at_...`），按你的 agent 的标准方式配置 MCP client。

配置参数：
- **URL**：从技能包的 `mcp.json` 的 `mcpServers.*.url` 字段读取
- **Authorization**：使用 `mcp_diagnose.py auth` 输出的**值部分**（不含 `Authorization:` 标签）

**配置能力说明**：
- 如果你的 agent 支持自动配置 MCP client（如 Claude Code 可编辑 settings.json），直接配置即可
- 如果你的 agent 不支持自动配置，将 URL 和 Authorization 值提供给用户，指导用户手动配置
- 配置完成后，必须在宿主连接器页完成 Trust/重连，并通过一次原生只读调用验证连接成功

## Token 过期处理

OAuth token 有效期约 15 天。当 MCP 工具返回 401 时：

1. 运行 `mcp_diagnose.py auth`（重新完成浏览器 OAuth 授权）
2. 复制输出的 Authorization header 值（如 `Bearer at_...`）
3. 更新你的 MCP client 配置
4. 重新连接/重试

> 💡 **提示**：如果重新授权后仍然 401，检查 mcp.json 中的 URL 是否正确。

## 存量配置迁移（仅影响升级用户）

如果你之前使用过 `inject_token.py`，mcp.json 中可能包含旧的 Authorization header。

**检查**：
```bash
grep -i "Authorization" mcp.json
```

**如果有输出**，说明存在旧配置。请手动删除 `mcpServers.*.headers.Authorization` 字段，保留其他配置（如 URL）。

**为什么**：脚本现在通过 OAuth 缓存获取 token，不再依赖 mcp.json 中的 Authorization header。旧配置会覆盖新缓存，导致认证失败。

**注意**：如果你主动在 mcp.json 中配置了 API key（如 `sk_...`），可以保留。

## 临时降级规则

**默认情况下，业务调用必须走原生 MCP 工具**。以下情况允许临时降级到脚本直连（`call_tool()`）：

- **前提**：宿主未重连成功 + 当次任务紧急不可等待
- **限制**：仅完成当次业务调用，不是长期方案
- **必须声明**：向用户明确说明"当前使用的是脚本降级通道，非原生 MCP"
- **修复后禁止**：MCP client 配置完成并重连成功后，禁止继续用脚本跑业务

降级不是默认路径，是受控例外。

## 认证优先级

脚本认证时，按以下优先级获取凭据：
1. `mcp.json` 中的 `headers.Authorization`（如果已配置）
2. 已保存的 OAuth token
3. 执行 OAuth 流程

## Token 认证（可选）

**不要主动询问用户是否有 token**。只有当用户主动提供 MCP Token（sk_ 开头或 Bearer Token）时，才在 `mcp.json` 的 `mcpServers.*.headers.Authorization` 中配置。

## 架构边界

- **脚本通道**：取 token（`mcp_diagnose.py auth`）+ 诊断（`mcp_diagnose.py tools`）+ 文件上传（`upload_document.py`：本地文件 I/O + base64）+ 经声明的临时降级（`call_tool()`）
- **业务工具**（create / update / get / status / task / organization 等）：**默认且长期走宿主原生 MCP 工具**；MCP client 配置完成并重连后，禁止继续用脚本跑业务

## 命令参数说明

**mcp_diagnose.py 支持的参数**：

```bash
# Linux / macOS
python3 skills/coach-mcp-connect/scripts/mcp_diagnose.py auth
python3 skills/coach-mcp-connect/scripts/mcp_diagnose.py auth --status
python3 skills/coach-mcp-connect/scripts/mcp_diagnose.py auth --mcp-url https://mcp.test.omnimay.com/coach/mcp

# Windows（用 python，路径用反斜杠）
python skills\coach-mcp-connect\scripts\mcp_diagnose.py auth
python skills\coach-mcp-connect\scripts\mcp_diagnose.py tools --mcp-url https://mcp.test.omnimay.com/coach/mcp
```

> **路径说明**：示例使用相对路径。技能实际安装在 `~/.workbuddy/skills/`（Linux/macOS）或 `%USERPROFILE%\.workbuddy\skills\`（Windows）。如果相对路径找不到脚本，改用绝对路径。

**upload_document.py 不支持的参数**：
- `--mcp-url`（必须从 mcp.json 读取）
- `--verbose`（不存在）
- 仅接受文件路径作为参数：`python3 upload_document.py /path/to/file.pdf`
