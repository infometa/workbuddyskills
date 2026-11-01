# 环境配置与认证

## 登录操作（唯一入口）

用户要求登录时，执行原子化工具，不要手动拆分步骤：

```javascript
const { provision } = require("references/yidea-provision.js");
await provision(userName, password);
```

> `<yidea-api-dir>` 为本文件所在目录

**完成判定**：命令返回 `{"status":"success"}` 即为成功。

**关键步骤：将工具列表注入上下文**

脚本返回的 `details.tools` 数组中包含了所有 Yidea MCP 工具的 name、description 和 inputSchema。拿到该数组后，**必须**将其写入当前会话的内存/上下文，以便后续所有业务操作（增删改查）都能直接使用这些工具定义。

建议在 agent 脚本/工作流中做如下处理：

```javascript
const { provision } = require("references/yidea-provision.js");
const result = await provision(userName, password);

if (result.status === "success") {
  // 将 tools 列表注入上下文供后续 MCP 调用使用
  context.yidea_tools = result.details.tools;
  memory.set("yidea_tools", result.details.tools); // 持久化到 memory
}

## 关键约束

1. 即使已有有效 Token，用户明确说"登录"，也必须重新执行完整原子化流程。
2. 若用户未提供用户名/密码，先询问再执行。
3. 配置 MCP 时禁止使用被截断的 Token（含 `…`），必须用完整原始字符串。

## 调试参考

底层 API：`POST /api/v1.2/Credential/YideaLogin`，body `{ "userName", "password" }`，返回 `{ "success", "accessToken" }`。
```
