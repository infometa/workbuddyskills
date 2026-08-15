# 认证授权流程详解

> 本文档是 beisen-shared 的子参考，由 SKILL.md 引用。

## 首次认证流程

```bash
# 1. 安装 CLI（全局仅一次）
npm install -g beisen-cli

# 2. 检查版本
beisen-cli version

# 3. 检查认证状态
beisen-cli auth status

# 4. 完成登录（首次或 token 过期时，优先 SSO 浏览器授权）
beisen-cli auth login

# 5. 若 auth login 等待授权超时失败，改用 API Key 绑定登录（回退方案）
beisen-cli auth bind --api-key <你的APIKey>
```

## 登录方式

`beisen-cli auth login` 为首选登录方式：会输出授权链接，用户在浏览器中完成北森 SSO 授权，授权完成后 CLI 自动获取 token。Agent 拿到授权链接后：**若 Agent 平台提供浏览器工具**（如 WorkBuddy、千问办公、豆包、Codex、Hermes 等），直接调用浏览器工具打开授权链接并告知用户；**若无浏览器工具**，将链接发给用户自行打开。等待用户完成授权后验证登录状态——若用户此前有未完成任务则继续，否则结束并等待下一条指令。**若 `auth login` 等待授权超时失败**（如进程被 kill、exit 137，或浏览器未在窗口期内完成授权），改用 `beisen-cli auth bind --api-key <你的APIKey>`：将已有 API Key 绑定到当前设备并保存设备凭据，作为 SSO 不可用时的回退登录方式。

## Token 管理

| Token | 有效期 | 说明 |
|-------|--------|------|
| Access Token | 2 小时 | 调用 API 的凭证 |
| Refresh Token | 30 天 | 换新 Access Token |

## 首次认证后的权限授权

首次登录仅解决"我是谁"。部分操作（如查询他人数据、管理员范围的数据）需要后台对该账号开通对应访问权限。

Agent 应在权限错误发生时（业务信封 `code != "200"` 且 `message` 提示无权限）：
1. 从 `message` 提取权限不足的原因
2. 向用户说明当前账号缺少哪类访问权限
3. 引导用户联系企业管理员在后台开通权限
4. 不要对权限错误反复重试业务命令
