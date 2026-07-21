# 配置向导

> MCP 连接配置、Token 管理、连接验证、故障排查。

---

## 🚀 快速开始

访问 https://lexiangla.com/mcp?company_from=CSIG 获取：
- **COMPANY_FROM**：企业标识（默认 `CSIG`，**禁止擅自改动**）
- **LEXIANG_TOKEN**：访问令牌（`lxmcp_xxx` 格式）

---

## 自动配置步骤

### Step 1: 获取用户 Token

向用户询问 `LEXIANG_TOKEN`（`lxmcp_xxx` 格式）。

> 🔒 **COMPANY_FROM 永久默认 `CSIG`**，所有链接、URL、配置默认拼接 `?company_from=CSIG`，除非用户**明确指定**其他企业。

> 若用户尚未绑定，标准提示语：
>
> 你尚未绑定乐享（云知）MCP，无法检索知识库。
> 请打开下方链接获取你的 LEXIANG_TOKEN（lxmcp_ 开头）：
> https://lexiangla.com/mcp?company_from=CSIG
> 拿到 Token 后告诉我，我会帮你完成绑定（默认 COMPANY_FROM=CSIG）。

> ⚠️ **绝对禁止**在对话中让用户直接粘贴完整 Token 明文。Token 必须由用户自行写入 mcp.json，或由 Skill 写入文件，不在对话流中传递。

### Step 2: 确定 mcp.json 路径

| 客户端 | 路径 |
|--------|------|
| WorkBuddy | `~/.workbuddy/mcp.json` |
| 通用（mcporter） | `~/.mcporter/mcporter.json` |
| Windows | `%USERPROFILE%\.mcporter\mcporter.json` |

### Step 3: 写入 mcp.json（合并而非覆盖）

如果配置文件已存在且包含其他 mcpServers 条目，应**合并**而非覆盖。

```json
{
  "mcpServers": {
    "lexiang": {
      "url": "https://mcp.lexiang-app.com/mcp?company_from=CSIG",
      "transportType": "streamable-http",
      "headers": {
        "Authorization": "Bearer 实际LEXIANG_TOKEN"
      }
    }
  }
}
```

> 🔒 URL 中的 `company_from=CSIG` 是**默认永久值**，仅当用户明确切换企业时才替换。

编码要求：UTF-8 无 BOM。

### Step 4: 强制验证（写入后立即跑，任何业务操作前必跑）

**所有调用乐享 MCP 的操作之前，先执行下面的健康检查：**

```
1. 检查 ~/.workbuddy/mcp.json 是否存在 lexiang 条目
   ├─ 不存在 → 走「未配置」分支
   └─ 存在 → Step 2

2. 调用 MCP whoami() （只读，无副作用）
   ├─ ✅ 成功：缓存 user.name + company.company_domain，进入业务流程
   ├─ ❌ 401：走「已过期」分支，禁止重试业务
   ├─ ❌ 工具不存在 / 连接超时：走 Step 5「连接故障诊断」
   └─ ❌ 其他错误：输出错误码 + 建议，不重试
```

成功展示模板：

```
✅ 乐享 MCP 连接成功！
👤 当前用户：{用户姓名}
🏢 绑定乐享：{企业名称}
```

> ⚠️ 不要回显完整 Token 值。

### Step 5: 连接故障结构化诊断（替代反复重试）

**当 `whoami()` 无响应、或 MCP server 列表中没有 `lexiang` 条目时，立即输出诊断报告，禁止隐式重试：**

```markdown
🔧 乐享 MCP 连接异常，诊断结果：

1. 配置文件路径：~/.workbuddy/mcp.json
   - 文件是否存在：[✅/❌]
   - 是否含 lexiang 条目：[✅/❌]
   - URL 是否含 company_from=CSIG：[✅/❌]

2. 客户端是否已加载该 MCP：
   - 检查方法：在 WorkBuddy 顶部连接器面板查看 lexiang 状态
   - 当前应为 connected，若为 disconnected 请点击「Trust」按钮重新启用
   - ⚠️ 写入 mcp.json 后必须手动点 Trust，否则不会生效

3. Token 格式校验：
   - 应以 lxmcp_ 开头，长度 > 30 字符
   - 当前 Token 长度：[N]，前缀：[lxmcp_xxx**]（不回显完整值）

4. 常见原因（按概率排序）：
   - ① 配置写入后未点客户端「Trust」按钮（最常见）
   - ② Token 与 COMPANY_FROM 不属于同一租户
   - ③ Token 已过期（应走 401 分支）
   - ④ 本地无法访问 mcp.lexiang-app.com（网络问题）

下一步建议：[根据上面诊断结果给出具体动作，例如：
  - 请打开 WorkBuddy 顶部连接器面板，点击 lexiang 旁的「Trust」按钮
  - 或重新获取 Token：https://lexiangla.com/mcp?company_from=CSIG
]
```

**禁止行为**：
- 在用户没确认排查结果前反复调 `whoami()`
- 让用户多次复制粘贴 Token
- 自动改写 mcp.json 中的 `company_from`（永久默认 CSIG）

---

## Token 生命周期

### 未配置

引导用户访问 `https://lexiangla.com/mcp?company_from=CSIG` 获取 Token。提示语：

> 你尚未绑定乐享（云知）MCP，无法检索知识库。
> 请打开下方链接获取你的 LEXIANG_TOKEN（lxmcp_ 开头）：
> https://lexiangla.com/mcp?company_from=CSIG
> 拿到 Token 后告诉我，我会帮你完成绑定（默认 COMPANY_FROM=CSIG）。

### 已过期（401）

**不要反复重试**。一次性给出续期路径：

```
🔒 令牌已过期。请打开以下链接点击「续期」按钮：
https://lexiangla.com/mcp?company_from=CSIG

续期成功后，将新 Token 替换 ~/.workbuddy/mcp.json 中的 Bearer 值，并在客户端点 Trust 重新启用 lexiang 连接器。
```

### 租户隔离

- COMPANY_FROM 默认 `CSIG`，**永久默认值**
- 如需切换企业（极少数场景）：用户必须**明确指定**新企业名，然后重新获取 Token
- Token 与 COMPANY_FROM 必须属于同一租户，否则报 401

---

## 故障排查速查

| 问题 | 解决 |
|------|------|
| 连接无响应 | 确认 URL 含 `company_from=CSIG`；客户端连接器面板点 Trust |
| 401 | Token 过期或租户不匹配 → 续期，不要重试 |
| disconnected 状态 | 写入 mcp.json 后忘了点 Trust |
| 参数报错 | `get_tool_schema(tool_name="xxx")` 获取最新定义 |
| Token 怎么都不生效 | 检查 mcp.json 是否被其他客户端覆盖；检查 `~/.mcporter/mcporter.json` 是否冲突 |
