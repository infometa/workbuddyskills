# 认证和配置

CLI 默认推荐 OAuth。先运行 `auth status --format json` 复用当前有效凭据；首次登录使用 `auth login --method oauth`。已连接时沿用当前方式，OAuth 失效时重新授权；用户明确选择 API Key 时使用对应的登录与配置流程。

同一系统用户的终端、Agent 与各安装副本共享一套认证状态。分别保存 OAuth 和 API Key，当前只启用一种；成功登录保存并启用新凭据。

## 命令

```bash
hithink-finance auth status --format json
hithink-finance auth login --method oauth
hithink-finance auth login --method api-key --api-key-stdin --format json
hithink-finance auth use api-key
hithink-finance auth use oauth
hithink-finance auth logout
hithink-finance auth logout --all
hithink-finance config show --format json
```

- 用户选择 API Key 时，在 https://fuyao.aicubes.cn/admin/ 获取。交互隐藏输入使用 `auth login --method api-key`。新 Key 远端验证成功后才保存；`--replace` 继续接受。
- OAuth 登录默认连接生产认证服务。宿主使用 `auth login --method oauth --background --no-browser`，就绪后输出裸 HTTPS URL，再轮询本地 status。
- `auth status` 展示连接状态、当前方式及可用凭据；`--debug` 提供附加诊断。状态检查不联网、不导入环境变量、不创建文件或刷新令牌。`connected` 表示本地存在可使用或可安全续期的当前凭据，不代表实时远端验权。
- 业务命令显式 `--api-key-stdin` 仅覆盖本次请求，不要求持久存储可用。隐藏的兼容 `--api-key <value>` 会发出弃用警告。
- `HITHINK_FINANCE_API_KEY` 仅在首次初始化且没有已存旧 Key 时导入一次；后续改变环境变量或退出均不自动导入。需要更新时使用登录命令。
- 普通业务首次初始化自动迁移旧 default Key 或唯一条目。OAuth 登录初始化不探测旧系统凭据库；其后需要导入旧 Key，或遇多候选/旧非默认 profile，使用 `auth migrate --legacy-profile <name>` 一次性选择，再移除旧 profile 设置。
- `auth status` 已连接时退出 0，未连接时退出 3；stdout 保留 `ok=true` 状态信封，读取 `data.connected`。状态检查只读本地凭据。
- OAuth 失败保持当前选择。权限错误不刷新；刷新结果未知时不重复发送旧 RT，仍有效 AT 可继续使用，到期后重新登录。
- 凭据根使用 OS 用户主目录 `.hithink-finance/auth/production/`，与 npm 安装及数据配置路径独立。统一采用操作系统私有权限保护的明文凭据文件。存储诊断使用 `auth status --debug --format json`。
- `logout` 清当前凭据，`--all` 清两类凭据。OAuth 本地退出先提交，远端撤销失败会明确报告；已签名下载链接按自身期限失效。
- Agent 从用户级 `credentials.env` 读取 Key 时，通过 stdin 显式登录或仅用于本次请求。不要把 Key、Token、授权码或完整授权 URL 写入日志、Markdown、Git 或对话。
- 共享安装副本须升级到支持全局格式的版本。认证目录需位于可靠本地文件系统。

- 旧格式使用 `auth migrate` 一次迁入；迁移后正常请求只访问文件，旧安装副本须一起升级。运行中的旧登录/刷新须结束后再迁移。

## 错误与恢复

- `AUTH_LOGIN_REQUIRED`：为当前方式重新登录。
- `AUTH_MIGRATION_REQUIRED`：运行 `auth migrate`；多份旧条目使用 `--legacy-profile` 明确选择。
- `AUTH_REFRESH_IN_PROGRESS`：稍后重试；`AUTH_REFRESH_UNCERTAIN`：有效 AT 到期后重新登录。
- `AUTH_CREDENTIAL_STORE_UNAVAILABLE`：旧凭据迁入时解锁原存储；`AUTH_STORAGE_PERMISSIONS`：修复凭据文件权限。显式 Key 仍可用于本次业务请求。
- `AUTH_REVOCATION_INCOMPLETE`：本地已退出，远端撤销未确认。
- `CLI_MISSING_ARGUMENT`：非交互 Key 登录使用 `--api-key-stdin`。
- `CLI_CONFLICTING_ARGUMENTS`：选择一种认证方式和一种 Key 输入。
- `CLI_STDIN_TOO_LARGE`：API Key 输入上限 16 KiB，批量代码上限 1 MiB。
- `CONFIG_NOT_FOUND`：修正显式配置路径或移除无效设置。
