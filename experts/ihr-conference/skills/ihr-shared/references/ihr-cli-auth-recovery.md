# iHR CLI 业务鉴权恢复

本文件只解释乐观业务调用的结构化错误含义和允许的恢复边界。它不实现安装、runtime gate、授权 Session 或宿主控制面；实际动作必须由调用方使用自己的可信参数完成。

## 可触发鉴权恢复的证据

- CLI JSON envelope 明确为 `error.code=AUTH_REQUIRED|AUTH_EXPIRED|CREDENTIAL_MISSING|ENVIRONMENT_MISMATCH`；或机器可读 HTTP 状态字段明确为 401。
- `AUTH_EXPIRED`、`CREDENTIAL_MISSING`、`ENVIRONMENT_MISMATCH` 以及 `auth status --env` 完整 JSON 中的 `data.readiness.reason=credential_missing|credential_expired|environment_mismatch|access_token_missing|credential_incomplete` 是本地状态，不等同于远端 401，不能一律强制重授权。
- `error.type=config_error|credential_store_error|validation_error` 是本地控制面失败，不等同于未登录。
- 自然语言、stderr 片段、字符串包含“401”、模型推断都不是触发证据。

## 确定路由

- `AUTH_REQUIRED` 或结构化 HTTP 401：允许调用方先执行可信环境的完整 `auth status --env`。本地非 `READY` 时允许普通登录；本地仍为 `READY` 时只允许一次强制重授权。
- 业务 envelope `error.code=CREDENTIAL_MISSING|ENVIRONMENT_MISMATCH`：允许调用方按自己的可信环境执行普通登录，不添加 `--reauthorize`；环境不匹配时不得继续使用或删除其他环境 credential。
- `credential_missing` / `credential_expired` / `environment_mismatch`：允许普通登录，不添加 `--reauthorize`。环境不匹配时不得把其他环境 credential 判定为可用。
- 业务 envelope `error.code=AUTH_EXPIRED`：允许调用方按本地过期路径普通登录；不得提升为远端 401 或添加 `--reauthorize`。
- `access_token_missing` / `credential_incomplete`：只有调用方能证明可信配置完整且 credential store 可写时才允许普通登录，否则停止。
- `config_error` / `auth_center_not_configured` / `credential_store_error`：停止，不得创建远程 Session、自动覆盖旧 credential 或切换配置目录。
- 未知 state/reason 或 status 中 environment 与调用方可信 runtime env 不一致：按契约错误停止。
- HTTP 403：按权限不足停止，不登录。
- 网络失败、429 或 5xx：保留本地 credential 并提示稍后重试，不登录。
- CLI 不存在：停止业务命令并交还调用方自己的安装入口。

## 一次恢复边界

- 真实 401 或用户明确要求重新登录/切换身份，才允许强制重授权。
- 调用方不得先删除旧 credential；授权失败、拒绝或超时时保留旧 credential。
- 授权成功后原业务命令最多重试一次。再次返回 401/`AUTH_REQUIRED|CREDENTIAL_MISSING|ENVIRONMENT_MISMATCH` 时停止；不得再次授权、递归恢复或形成循环。
- 403、网络错误、429、5xx 和普通自然语言错误不得提升为强制重授权。
- 用户拒绝授权时停止。

## 用户退出

使用公共 guide 确认的 CLI 执行 `auth logout`，再读取普通 `auth status` 确认本地凭证已清除。远端失效 warning 不阻断本地退出。

任何恢复都不得输出 token、设备授权内部字段、完整认证 JSON 或认证中心内部地址。
