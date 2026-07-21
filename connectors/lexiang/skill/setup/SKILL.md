---
name: lexiang-setup
description: "乐享知识库 MCP 连接配置与故障排查。WorkBuddy 用户通过内置连接器 OAuth 授权；其他平台用户手动配置 Bearer Token。当用户提到「乐享」「知识库」「lexiang」并包含配置/连接/setup 意图，或遇到 MCP 连接失败、401 未授权错误时使用。典型触发：「配置乐享」「连接乐享」「乐享连不上」「token 过期了」「401 错误怎么办」「切换企业/租户」「重新授权」。"
---

# 乐享 MCP 配置向导

> **触发场景**：
> - 用户说 "配置乐享"、"setup lexiang"、"连接乐享"
> - 用户首次安装乐享 skill 后
> - MCP 连接失败或返回 401 错误时
> - 用户需要切换企业/租户时

---

## 🖥️ 平台识别 — 优先判断

**在引导配置前，先判断用户所在的客户端平台：**

| 平台 | 认证方式 | 操作 |
|------|---------|------|
| **WorkBuddy** | 内置乐享连接器（OAuth） | 见下方「WorkBuddy 连接说明」 |
| 其他平台（OpenClaw、Claude 等） | Bearer Token 手动配置 | 见下方「手动配置 mcp.json」 |

---

## ⚡ WorkBuddy 连接说明

WorkBuddy 已内置乐享连接器，**无需手动获取 Token 或编辑 mcp.json**。

### 首次连接

1. 在 WorkBuddy 的「集成」入口中找到「**乐享**」连接器
2. 点击「**授权**」，跳转到乐享授权页面完成 OAuth 登录
3. 授权成功后连接器自动激活

### 连接断开 / 401 错误

如果 WorkBuddy 中乐享连接器断开或收到 401 错误：

1. **不要手动配置 mcp.json**
2. 在 WorkBuddy「集成」页面找到乐享连接器
3. 点击「**重新授权**」完成 OAuth 重连

> ⚠️ WorkBuddy 的乐享连接完全通过 OAuth 管理，任何情况下都**不需要** LEXIANG_TOKEN，也**不需要**手动编辑配置文件。

---

## 🚀 手动配置 mcp.json（其他平台）

### 获取配置参数

访问：https://lexiangla.com/mcp

登录后获取：
- **COMPANY_FROM**：你的企业标识
- **LEXIANG_TOKEN**：访问令牌（格式 `lxmcp_xxx`）

**校验规则**：两个参数都不能为空。

### 认证方式

> ⚠️ **平台说明**：
> - **WorkBuddy**：通过内置连接器 OAuth 授权，无需手动配置，见上方「WorkBuddy 连接说明」
> - **其他平台**：使用 Bearer Token 静态鉴权，按本节步骤手动配置

Token 直接写入 mcp.json 配置文件中（硬编码方式）。

#### 配置 mcp.json

将用户提供的 `COMPANY_FROM` 和 `LEXIANG_TOKEN` **直接填入** mcp.json：

```json
{
    "mcpServers": {
        "lexiang": {
            "enabled": true,
            "url": "https://mcp.lexiang-app.com/mcp?company_from=用户的COMPANY_FROM值",
            "transportType": "streamable-http",
            "headers": {
                "Authorization": "Bearer 用户的LEXIANG_TOKEN值"
            }
        }
    }
}
```

> ⚠️ 将上面的 `用户的COMPANY_FROM值` 和 `用户的LEXIANG_TOKEN值` 替换为用户提供的实际值。

---

## 🤖 自动配置步骤

> 本节描述 AI Agent 自动帮用户完成配置的流程。
> 将用户提供的 COMPANY_FROM 和 LEXIANG_TOKEN **直接写入 mcp.json**。

### Step 1: 获取用户参数

向用户询问 `COMPANY_FROM` 和 `LEXIANG_TOKEN`。如果用户不清楚，引导其访问：

```
https://lexiangla.com/mcp
```

登录后即可看到配置信息。

**校验规则**：两个参数都不能为空。

### Step 2: 确定 mcp.json 路径

| 客户端/平台 | 路径 |
|-------------|------|
| 通用（mcporter） | `~/.mcporter/mcporter.json` |
| Windows | `%USERPROFILE%\.mcporter\mcporter.json` |
| WSL | `~/.mcporter/mcporter.json`（Linux 侧路径） |

### Step 3: 写入 mcp.json

如果配置文件已存在且包含其他 mcpServers 条目，应 **合并** 而非覆盖整个文件。

将用户提供的 `COMPANY_FROM` 和 `LEXIANG_TOKEN` 实际值直接填入：

```json
{
  "mcpServers": {
    "lexiang": {
      "url": "https://mcp.lexiang-app.com/mcp?company_from=用户提供的COMPANY_FROM",
      "transportType": "streamable-http",
      "headers": {
        "Authorization": "Bearer 用户提供的LEXIANG_TOKEN"
      }
    }
  }
}
```

**编码要求**：文件必须以 UTF-8 无 BOM 编码保存。

### Step 4: 身份验证与欢迎引导

配置完成后，**立即调用** MCP 工具 `whoami()` 获取当前用户信息。

**成功时**（返回用户信息），向用户展示欢迎消息，格式参考：

```
✅ 乐享 MCP 连接成功！

👤 当前用户：{用户姓名}
🏢 绑定乐享：{企业/租户名称}

🎉 配置已就绪，你现在可以这样使用乐享知识库：

💡 试试这样提问：
• "看看我最近访问的知识库有什么更新"
• "我要记录今天的工作内容，为我创建一个乐享文档并拟写一个模版"
• "搜索关于 XXX 的知识文档"
• "帮我总结一下这个知识库的内容：{知识库链接}"
```

> 根据 `whoami` 返回的实际字段灵活调整展示内容。如果返回了额外有用的信息（如用户角色、头像等），可酌情展示。

**401 错误** → token 无效或已过期，引导用户打开 `/mcp` 页面点击续期（参见下方 Token 管理）

**连接超时/其他错误** → 检查 mcp.json 配置是否正确

> ⚠️ 不要在输出中回显 LEXIANG_TOKEN 的完整值（安全考虑）

---

## 🔑 AccessToken 生命周期管理

### 阶段 1：未配置 Token（非 WorkBuddy 平台）

> ⚠️ WorkBuddy 用户遇到连接问题，请见上方「WorkBuddy 连接说明」，**不适用本节**。

当调用 MCP 连接失败或无认证信息时：

1. 告知用户需要获取乐享 MCP 的 `LEXIANG_TOKEN`
2. 引导用户打开 `https://lexiangla.com/mcp` 获取配置信息
3. 用户获取后，帮助完成 mcp.json 配置（参见上方「自动配置步骤」，将 token 直接写入 mcp.json）

### 阶段 2：Token 即将过期

当 MCP 返回正常结果但附带过期预警信息时：

1. **先正常返回本次结果**
2. 读取 mcp.json 中 `url` 字段里的 `company_from` 参数值
3. 在结果末尾附加提醒，引导用户续期：

```
⚠️ 您的乐享访问令牌即将过期。请打开以下链接，点击「续期」按钮即可延长有效期（需已登录）：
https://lexiangla.com/mcp?company_from=<从mcp.json读取的company_from值>
```

### 阶段 3：Token 已过期（401 响应）

当 MCP 返回 401 未授权时：

1. **不要反复重试**
2. 读取 mcp.json 中 `url` 字段里的 `company_from` 参数值
3. 引导用户打开 `/mcp` 页面点击续期，原 token 即可恢复使用，**无需重新获取新 token**：

```
🔒 您的乐享访问令牌已过期。请打开以下链接，点击「续期」按钮即可恢复（无需重新配置）：
https://lexiangla.com/mcp?company_from=<从mcp.json读取的company_from值>
```

> `company_from` 值从当前 mcp.json 的 `url` 字段中提取，例如 `url` 为 `https://mcp.lexiang-app.com/mcp?company_from=csig`，则填入 `csig`。**不能省略此参数**，否则续期页面无法定位到正确的企业租户。

### 租户隔离规则

- `COMPANY_FROM` 和 `LEXIANG_TOKEN` **必须属于同一租户**，不同租户的 token 不能混用
- 续期 token 时，URL 中的 `company_from` 必须与当前 mcp.json 中配置的一致
- 如果用户切换了企业/租户，必须重新获取对应租户的 token 并更新 mcp.json

---

## ❓ 故障排查

| 问题 | 解决方案 |
|------|----------|
| 连接无响应 | 确认 mcp.json 中 URL 包含 `company_from` 且格式正确 |
| 401 未授权 | token 过期或租户不匹配，参见上方「AccessToken 生命周期管理」 |
| 参数报错 | 执行 `get_tool_schema(tool_name="xxx")` 获取最新参数定义 |

---

## 相关链接

- 获取配置：https://lexiangla.com/mcp
- 乐享平台：https://lexiangla.com
- MCP 协议：https://modelcontextprotocol.io
