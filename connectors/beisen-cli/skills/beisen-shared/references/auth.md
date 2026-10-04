# 认证授权流程详解

> 本文档是 beisen-shared 的子参考，由 SKILL.md 引用。

## 认证模型：响应式校验

beisen-cli 在每次业务命令执行时**内部自动校验认证状态**，Agent 无需主动调用 `beisen-cli auth status` 检查登录状态。

- 凭据有效 → CLI 正常返回业务数据
- 凭据失效 → CLI 返回 `HTTP 401` + `error_code: "CLI_AUTH_005"`，Agent 据此触发登录流程

## 触发登录的条件

当 CLI 返回信息中**同时包含**以下两个信号时，触发登录：

| 信号 | 值 |
|------|------|
| HTTP 状态码 | `401` |
| error_code | `CLI_AUTH_005` |

返回示例：

```
HTTP 401: {"error_code":"CLI_AUTH_005","error_message":"xxxxx"}
```

## 登录流程

### 首选：SSO 浏览器授权

```bash
beisen-cli auth login
```

该命令输出授权链接，Agent 将链接输出给用户，提示用户在浏览器中完成北森 SSO 授权。授权链接有效期 10 分钟。

用户完成授权后，重新执行此前因认证失败的业务命令。

### 回退：API Key 绑定

若 `auth login` 等待授权超时失败（进程被 kill、exit 137，或浏览器未在窗口期内完成授权），改用：

```bash
beisen-cli auth bind --api-key <你的APIKey>
```

API Key 获取路径：web 端 → 个人设置 → API Key → 生成新 Key。

## 首次安装

```bash
# 安装 CLI
npm install -g beisen-cli

# 验证版本
beisen-cli version
```

## Token 管理

| Token | 有效期 | 说明 |
|-------|--------|------|
| Access Token | 2 小时 | 调用 API 的凭证 |
| Refresh Token | 30 天 | 换新 Access Token |

## 手动排查

如需手动排查认证问题（非日常流程），可使用：

```bash
beisen-cli auth status
```

## 首次认证后的权限授权

首次登录仅解决"我是谁"。部分操作（如查询他人数据、管理员范围的数据）需要后台对该账号开通对应访问权限。

Agent 应在权限错误发生时（业务信封 `code != "200"` 且 `message` 提示无权限）：
1. 从 `message` 提取权限不足的原因
2. 向用户说明当前账号缺少哪类访问权限
3. 引导用户联系租户管理员授权及购买安装相关的产品
4. 不要对权限错误反复重试业务命令
