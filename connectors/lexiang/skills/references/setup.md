# 乐享 MCP 配置向导

> **触发场景**：
> - 用户说 "配置乐享"、"setup lexiang"、"连接乐享"
> - 用户首次安装乐享 skill 后
> - MCP 连接失败或返回 401 错误时
> - 用户需要切换企业/租户时

---

## 🖥️ 第一步：判断客户端平台

**配置前必须先判断平台类型，不同平台走完全不同的路径：**

| 平台类型 | 示例客户端 | 认证方式 |
|---------|-----------|---------|
| **内置连接器平台** | WorkBuddy、QClaw 等 | OAuth 连接器，**无需手动配置** |
| **其他平台** | OpenClaw、Claude、Cursor 等 | Bearer Token 手动配置 mcp.json |

> **如何判断？** 若用户提到的客户端名称在「内置连接器平台」列表中，或用户描述了「集成/连接器/授权」等入口，则视为内置连接器平台。

---

## ⚡ 内置连接器平台（WorkBuddy / QClaw 等）

### ⛔ 连接器优先原则

> **重要**：当客户端内置乐享连接器时，**无论用户是否额外手动安装了乐享 MCP**，均以连接器为准，手动安装的 MCP 配置会被忽略。
>
> 如果检测到用户同时存在手动安装的乐享 MCP（mcp.json 中有 lexiang 条目），需主动提示用户移除：
>
> ```
> ℹ️ 您的客户端已内置乐享连接器，手动配置的乐享 MCP 会被忽略。
> 建议在 mcp.json 中删除手动添加的 lexiang 条目，避免混淆。
> ```

### 首次连接

1. 在客户端的「集成」/「连接器」入口中找到「**乐享**」
2. 点击「**授权**」，跳转到乐享授权页面完成 OAuth 登录
3. 授权成功后连接器自动激活，调用 `whoami()` 验证

> ⚠️ 整个过程**不需要** LEXIANG_TOKEN，也**不需要**编辑任何配置文件。

### 连接断开 / 401 错误

内置连接器平台出现连接断开或 401 时：

1. **不要引导用户手动配置 mcp.json**
2. 引导用户在客户端「集成」页面找到乐享连接器
3. 点击「**重新授权**」完成 OAuth 重连
4. 授权完成后继续之前的任务

---

## 🚀 其他平台：手动配置 mcp.json

> 本节仅适用于**不内置乐享连接器**的平台。WorkBuddy / QClaw 等内置连接器平台请见上方。

### 获取配置参数

访问：https://lexiangla.com/mcp

登录后获取：
- **COMPANY_FROM**：你的企业标识
- **LEXIANG_TOKEN**：访问令牌（格式 `lxmcp_xxx`）

**校验规则**：两个参数都不能为空。

### 配置 mcp.json

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

> ⚠️ 如果配置文件已存在且包含其他 mcpServers 条目，应**合并**而非覆盖整个文件。

### 配置文件路径

| 客户端/平台 | 路径 |
|-------------|------|
| 通用（mcporter） | `~/.mcporter/mcporter.json` |
| Windows | `%USERPROFILE%\.mcporter\mcporter.json` |
| WSL | `~/.mcporter/mcporter.json`（Linux 侧路径） |

### 配置完成后验证

配置完成后，**立即调用** `whoami()` 获取当前用户信息。

**成功时**展示欢迎消息：

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

> ⚠️ 不要在输出中回显 LEXIANG_TOKEN 的完整值（安全考虑）

---

## 🔑 AccessToken 生命周期管理（其他平台）

> ⚠️ 内置连接器平台（WorkBuddy / QClaw 等）不适用本节，连接问题请见上方「连接断开 / 401 错误」。

### 阶段 1：未配置 Token

当调用 MCP 连接失败或无认证信息时：

1. 告知用户需要获取乐享 MCP 的 `LEXIANG_TOKEN`
2. 引导用户打开 `https://lexiangla.com/mcp` 获取配置信息
3. 用户获取后，帮助完成 mcp.json 配置

### 阶段 2：Token 即将过期

当 MCP 返回正常结果但附带过期预警信息时：

1. **先正常返回本次结果**
2. 读取 mcp.json 中 `url` 字段里的 `company_from` 参数值
3. 在结果末尾附加提醒：

```
⚠️ 您的乐享访问令牌即将过期。请打开以下链接，点击「续期」按钮即可延长有效期（需已登录）：
https://lexiangla.com/mcp?company_from=<从mcp.json读取的company_from值>
```

### 阶段 3：Token 已过期（401 响应）

1. **不要反复重试**
2. 读取 mcp.json 中 `url` 字段里的 `company_from` 参数值
3. 引导用户续期，原 token 即可恢复，**无需重新获取新 token**：

```
🔒 您的乐享访问令牌已过期。请打开以下链接，点击「续期」按钮即可恢复（无需重新配置）：
https://lexiangla.com/mcp?company_from=<从mcp.json读取的company_from值>
```

> `company_from` 从 mcp.json `url` 字段提取（如 `?company_from=csig` 中的 `csig`），**不能省略**。

### 租户隔离规则

- `COMPANY_FROM` 和 `LEXIANG_TOKEN` **必须属于同一租户**，不同租户的 token 不能混用
- 如果用户切换了企业/租户，必须重新获取对应租户的 token 并更新 mcp.json

---

## ❓ 故障排查

| 问题 | 平台 | 解决方案 |
|------|------|---------|
| 连接器未连接 | 内置连接器平台 | 在客户端「集成」页面重新授权 |
| 连接无响应 | 其他平台 | 确认 mcp.json 中 URL 包含 `company_from` 且格式正确 |
| 401 未授权 | 其他平台 | token 过期或租户不匹配，参见上方「AccessToken 生命周期管理」 |
| 参数报错 | 所有平台 | 执行 `get_tool_schema(tool_name="xxx")` 获取最新参数定义 |
| 手动 MCP 与连接器冲突 | 内置连接器平台 | 从 mcp.json 删除 lexiang 手动条目，仅保留连接器 |

---

## 🔄 MCP 连接中断处理

> 当任务执行中途出现 MCP disconnected / 连接超时时，按以下流程处理，**不要立即打断用户要求重新配置**。

### 内置连接器平台

1. 直接引导用户在「集成」页面点击乐享连接器的「**重新授权**」
2. 授权完成后继续任务，无需额外配置

### 其他平台

1. **先自动重连一次**：使用 mcp.json 中已有的配置静默重连，无需用户操作
2. **重连成功**：继续执行未完成的任务，告知用户「连接已自动恢复，正在继续...」
3. **重连失败**：
   - 展示已有配置（脱敏显示 token），让用户确认是否正确，**不重复询问已填写过的信息**
   - 提示检查网络或访问 `https://lexiangla.com/mcp` 确认 token 是否有效

### 连接超时（非 401）

1. 等待 3 秒后重试一次
2. 重试成功则继续；重试失败则告知用户：
   ```
   ⚠️ 乐享 MCP 连接超时，请检查网络状态后重试。
   如多次超时，可尝试重新启动客户端。
   ```

---

## 相关链接

- 获取配置：https://lexiangla.com/mcp
- 乐享平台：https://lexiangla.com
- MCP 协议：https://modelcontextprotocol.io
