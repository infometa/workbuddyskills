# 配置与授权（setup）

> ⛔ **对外口径**：本节内容（OAuth、token、端点、AppBridge、状态码、错误码）**全部仅供你内部排查使用**，
> **禁止向用户转述**。对用户只给业务结论 + 建议动作：
> - 取不到数据 → 「暂时无法获取数据，请检查授权状态。」
> - 授权失效 → 「授权已失效，请在连接器面板重新授权。」

## Token 配置

### WorkBuddy（推荐）

通过「招财多元宝」连接器 OAuth 授权，无需手动填 token：

1. 在 WorkBuddy 连接器面板找到「招财多元宝」；
2. 点击「前往绑定」，跳转授权登录页；
3. 手机验证码登录后自动回跳，连接器激活；
4. 之后 AI 调 MCP 工具时 token 自动携带、自动续期。

### MCP Apps（询价报价用）

询价报价内嵌在 WorkBuddy 里，页面点按钮通过 AppBridge 反向调 MCP 工具，token 由 WorkBuddy 自动带：

- 页面引入 `@modelcontextprotocol/ext-apps`，用 `app.callServerTool()` 调工具；
- token 全程由 WorkBuddy 托管，页面不碰 token；
- 无需用户跑任何本地脚本或填 token。

---

## 401 / token 过期处理

- 调 `queryTraderQuote` 返回 401 时，**不要重试**；
- 引导用户：WorkBuddy 点连接器的「续期/重新授权」；
- 恢复后继续执行，无需重新配置其他内容。

## 连接失败排查

| 现象 | 处理 |
|------|------|
| 工具数为 0 | 连接器未激活，点击「前往绑定」完成授权 |
| 调用 401 | token 失效，重新授权/续期 |
| 网络错误 | 确认后端 MCP 地址可达、HTTPS 正常 |

## 凭证安全

- token 由 WorkBuddy 托管，页面、URL、浏览器存储均不接触 token；不进 git、不进聊天、不进仓库。
