# 钉钉授权方案：Skill 自闭环版本

## 结论

本 Skill 的可用授权方案不是“等待 WorkBuddy Runtime 改造”，而是使用 `dws` 官方已有能力完成授权：

1. **默认：浏览器跳转登录** — 执行 `dws auth login`，由 `dws` 自动打开浏览器走 loopback OAuth，用户在浏览器/钉钉页面完成授权。
2. **兜底：设备流链接 + 授权码** — 执行 `dws auth login --device`，把授权链接和授权码展示给用户，用户打开链接完成授权。
3. **初始化基础权限授权** — 首次登录成功后说明还需要第二段 `doc:read` 业务授权；初始化可请求 permanent，以减少后续读文档时重复授权打断。
4. **可选：二维码** — 若本机已有 `qrencode` 等二维码工具，可把设备流完整链接转成二维码；不要为了二维码额外安装依赖。
5. **补充：host-owned PAT** — 仅用于已登录后的业务权限/行为授权，不作为首次登录方案。

## 授权三层模型

1. OAuth 登录：解决“当前用户是谁”。
2. 组织 CLI 访问：解决“企业/组织是否允许 CLI 访问数据”。
3. 业务 PAT scope：解决“某个具体动作是否被允许”，例如读取钉钉文档需要 `doc:read`。

不要把“已登录”误判为“所有业务权限都已授权”。

## 实测结论

- `dws` v1.0.24 已包含 `DINGTALK_DWS_AGENTCODE`、`dws pat chmod`、`dws pat browser-policy`。
- 未登录状态下执行业务命令，即使设置 `DINGTALK_DWS_AGENTCODE=workbuddy_test_agent`，当前返回 `not_authenticated`，不会返回 hostControl 授权 JSON。
- `dws auth login --device` 可以稳定输出授权页、授权码、带 `user_code` 的完整链接，并轮询授权结果。
- `dws auth login --device --format json` 当前仍输出面向终端的文本，不是纯 JSON。

## 授权触发规则

- 用户只是问“登录状态 / 是否已登录”时，只汇报状态，不主动发起登录。
- 用户明确要求“登录 / 授权 / 发起授权流程 / 继续登录 / 帮我授权 / 开始授权”时，不要停在状态汇报，也不要再询问是否继续；授权不是危险操作，必须立即执行首次授权流程。
- 业务命令返回 `not_authenticated`、`AUTH_TOKEN_EXPIRED`、`USER_TOKEN_ILLEGAL` 或 token 失效时，不要反复重试业务命令，直接执行首次授权流程。

## 首次授权流程

### 方案 A：浏览器跳转登录（默认）

```bash
dws auth login
```

执行规范：

1. 保持命令运行。
2. 等待用户在自动打开的浏览器或钉钉页面中完成授权。
3. 授权完成后执行：

```bash
dws auth status --format json
```

如果浏览器没有自动打开、loopback 失败、SSH/无头环境不可用或命令长时间无进展，切换到方案 B。

### 方案 B：设备流链接 + 授权码（兜底）

```bash
dws auth login --device
```

从输出中提取：

```text
link: https://login.dingtalk.com/oauth2/device/verify.htm
authorization code: XXXX-XXXX
https://login.dingtalk.com/oauth2/device/verify.htm?user_code=XXXX-XXXX
```

展示给用户的口径：

```text
请打开下面的钉钉授权链接并完成授权。授权码是 XXXX-XXXX。
https://login.dingtalk.com/oauth2/device/verify.htm?user_code=XXXX-XXXX

我会保持命令等待授权结果，完成后继续执行你的钉钉任务。
```

macOS 本地环境可直接打开完整链接：

```bash
open "https://login.dingtalk.com/oauth2/device/verify.htm?user_code=XXXX-XXXX"
```

授权完成后验证：

```bash
dws auth status --format json
```

## 初始化基础权限授权

首次登录成功且 `dws auth status --format json` 确认可用后，说明文档读取通常还需要第二段业务授权：

```text
钉钉初始化需要完成两步：
1. 登录钉钉账号
2. 授予 WorkBuddy 读取钉钉文档权限 doc:read
```

初始化阶段可请求长期授权，避免每次读文档都被中断；但要明确告知这可能是第二次授权确认：

```bash
export DINGTALK_DWS_AGENTCODE="workbuddy"
export DWS_CHANNEL="workbuddy"
dws pat chmod doc:read --agentCode workbuddy --grant-type permanent --format json
```

如果用户明确只想临时授权，改用一次性授权：

```bash
dws pat chmod doc:read --agentCode workbuddy --grant-type once --format json
```

执行规范：

1. 不要把 `doc:read` 说成并入同一次 OAuth；它可能触发第二次授权确认。
2. `doc:read` 属于低风险只读 PAT，初始化时可以请求 permanent，但要先说明用途：用于后续读取钉钉文档正文，减少重复授权打断。
3. 如果组织策略不允许授权或命令返回权限错误，记录失败原因，不阻断非文档类任务。
4. 执行 `doc read`、`doc search`、读取文档内容等文档读取任务前，若 `doc:read` 未授权，必须再次执行本步骤。
5. `doc:read` 只覆盖读取钉钉文档；写文档、删除块、移动/重命名等写操作仍按需单独授权，并遵守危险操作确认规则。

已验证基线：`doc:read` 可被 `dws pat chmod` 识别，`once` 与 `permanent` 在 dry-run 下均可通过；真实授权是否成功取决于组织策略和用户确认。

### 方案 C：二维码（可选）

仅在本机已有二维码工具时使用：

```bash
qrencode -o /tmp/dws-auth.png "https://login.dingtalk.com/oauth2/device/verify.htm?user_code=XXXX-XXXX"
open /tmp/dws-auth.png
```

如果没有 `qrencode`，不要安装依赖，直接用方案 B 的链接和授权码。

## 已登录后的业务权限授权

执行业务命令前可以设置：

```bash
export DINGTALK_DWS_AGENTCODE="workbuddy"
export DWS_CHANNEL="workbuddy"
```

如果业务命令返回 exit code `4`，或 stdout/stderr 出现 `PAT_MEDIUM_RISK_NO_PERMISSION`、`requiredScopes`、`grantOptions`：

1. 同时检查 stdout 和 stderr，优先解析 JSON key，不依赖可能乱码的中文 message。
2. 提取 `requiredScopes[].scope` 和 `grantOptions`。
3. 向用户说明缺少哪些权限、一次性授权和长期授权的区别。
4. 低风险只读 scope 可建议 `once`；中高风险或写权限必须先解释数据范围和风险。
5. 用户确认后执行：

```bash
dws pat chmod <scope>... --agentCode workbuddy --grant-type once --format json
```

6. `--grant-type session` 只有在已知 `--session-id` 时才能使用；不要执行缺少 `--session-id` 的旧命令：

```bash
dws pat chmod <scope>... --agentCode workbuddy --grant-type session --session-id <id> --format json
```

7. 同一工作流已知会连续触发多个 scope 时，可在用户确认后一次性合并授权，减少反复中断。例如：

```bash
dws pat chmod drive:upload-info drive:commit --agentCode workbuddy --grant-type once --format json
```

8. 只有用户明确要求长期授权时，才使用 `--grant-type permanent`。
9. replay 原始业务命令.

## 不要做的事

- 不要把首次登录写成“等待客户端改造后才能用”。
- 不要在未登录时反复尝试业务命令；看到 `not_authenticated` 就进入首次授权流程。
- 不要为了二维码安装新依赖。
- 不要把 AppKey、AppSecret、access token、refresh token 写进 Skill 或日志。
