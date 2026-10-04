# iHR CLI Agent 授权流程

本文件只用于安装阶段已经结束后的 Agent 授权阶段。授权阶段必须独立于业务 Plan；授权完成前不创建或继续业务 Plan，不执行业务命令。

## 安装后执行边界

- 安装器的平台 Shell 路由到安装阶段结束即终止。安装完成后，授权、状态和业务阶段都通过宿主正常命令通道直接执行正式 `ihr-cli`，不再选择、启动或切换 PowerShell/Bash，也不继承 Windows 安装器“只使用原生 PowerShell”的限制。宿主正常命令通道在 Windows 上底层使用 Bash 不等于安装器回退 Bash。
- 不得为了调用 `ihr-cli` 追加 PowerShell 编码初始化、二次 Shell、输出重定向或把整段命令包装成待重新解释的字符串；直接逐事件消费 CLI 的 stdout NDJSON。
- 命令退出码为 0，但 stdout 为空或没有任何可解析的 JSON/NDJSON 事件时，不得认定授权 `READY`，也不得切换 Shell 或重复创建授权。应停止并报告未获得可解析的结构化结果。

## 发起授权并自动轮询

调用方必须提供自己可信的 `source`，并只在已有可信环境时传入 `env`：

```text
ihr-cli auth ensure --open-browser --wait 1m --stream --source <trusted-source> [--env <trusted-env>]
```

- 第一个非终态 `authorization_required` 事件必须在首次轮询前写出并刷新。宿主与 Agent 必须逐事件消费并立即向用户逐字展示完整 `authorizationUrl` 和 `userCode`，不得把整个命令输出缓冲到进程结束，也不得等到命令终态、截断、改写、重新拼接或用 `verification_uri` 替代；链接对用户可见后，才允许同一前台进程继续自动轮询。
- 前台自动轮询最长 1 分钟，不得改成隐藏的后台任务或 9/10 分钟长轮询。终态 `ready` 到达后立即告知授权成功；若结构化 `companyName`、`userName` 非空，同时原样展示并结束当前响应，不追加状态文件读取、`auth status`、`auth verify` 或业务命令。
- 一分钟后仍返回终态 `authorization_required` 时，保留原 Session，提示“暂未检测到授权，完成后只需回复‘已授权’”，然后结束当前响应。
- 必须以 CLI 的 NDJSON 事件与结构化字段为准；不得依赖模型从普通终端文案或乱码中猜测授权链接、公司或用户信息。
- 不向用户展示 `sessionRef`，也不要求用户提供链接、设备码、用户码或 Session 引用。
- `warningCode=BROWSER_OPEN_FAILED` 只表示未能自动打开浏览器。它不改变授权状态；仍须展示完整链接和用户码并继续本次前台自动轮询，不得重新创建授权。

## 用户回复“已授权”

当用户只回复“已授权”或“我已授权”时，使用与 `auth ensure` 完全相同的可信上下文恢复现有 Session：

```text
ihr-cli auth resume --source <same-trusted-source> [--env <same-trusted-env>] --timeout 1m
```

- `READY`：立即告知授权成功；若 `companyName`、`userName` 非空，同时原样展示并结束当前响应。之后才可开始新的业务阶段。
- `AUTHORIZATION_REQUIRED`：本次一分钟等待尚未检测到授权。保留原 Session，告知用户暂未检测到；不得后台继续轮询，不得创建新链接。
- `authorization_session_expired`：原 Session 已过期，此时才重新执行一次 `auth ensure` 并展示新链接。
- `device_authorization_denied` 或其他明确终止状态：停止并告知用户；只有用户再次明确要求授权时才新建 Session。
- `authorization_session_not_found`：停止并报告无法恢复可信范围内的原 Session，不得猜测或要求用户提供 `sessionRef`。

## 禁止混用旧协议

Agent 不得执行或生成以下流程：

- `auth login --no-wait --json`
- `auth login --device-code <device_code>`
- 把 `device_code` 或 `userCode` 传给 `auth wait --session`
- 手工调用 `auth wait`、在后台轮询，或把前台等待上限设置为 9/10 分钟
- 在 Session 仍为 pending 或一分钟等待超时时重新执行 `auth ensure`

`auth wait --session` 只接受 `auth ensure` 返回的 opaque `sessionRef`，属于 CLI 底层兼容接口；Agent 恢复授权只使用 `auth resume`。
