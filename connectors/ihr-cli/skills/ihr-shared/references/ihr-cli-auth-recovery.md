# WorkBuddy Connector 鉴权恢复

本文件只解释业务调用失败后如何交还 WorkBuddy Connector 控制面。Skill 本身不执行安装或认证命令。

## 可触发恢复的证据

- CLI JSON envelope 明确为 `error.code=AUTH_REQUIRED|AUTH_EXPIRED|CREDENTIAL_MISSING`，或机器可读 HTTP 状态明确为 401。
- `config_error`、`auth_center_not_configured`、`credential_store_error` 属于本地控制面错误，停止并展示安全摘要，不自行修改配置目录或凭证存储。
- HTTP 403 是权限不足；网络失败、429 或 5xx 是暂时性调用失败。它们都不触发登录。
- 自然语言、stderr 片段、字符串包含“401”或模型推断都不是恢复证据。

## WorkBuddy 路由

1. 停止当前业务命令，不继续尝试其他 Domain 或 raw 接口。
2. 提示用户在 WorkBuddy 的 iHR Connector UI 中执行连接或重新连接。
3. 不直接运行 `ihr-cli auth login/status/logout/ensure/wait/verify`，不创建并行授权 Session。
4. WorkBuddy 显示连接成功后，原业务命令最多重试一次。
5. 再次返回 401 或认证错误时停止，并保留结构化错误摘要供排查。

## 安全边界

- 不输出 token、device_code、授权内部字段、完整认证 JSON、敏感配置或认证中心内部地址。
- 不删除旧 credential，不切换 `IHR_CLI_CONFIG_DIR`，不强制使用第二种 credential store。
- Connector 与普通终端首版共享现有 iHR CLI 配置和登录态；断开连接可能同时影响终端当前 profile。
