# 凭证

凭证按空间可见（`--space-id` 或项目里的 `adp.jsonc`），供连接器/工具（插件）调用第三方服务时使用。

## 安全规则

- 秘密值只写不读：`list`/`get` 不返回 token；不要尝试从 CLI 输出里取回密钥。
- API Key 只通过 `--token-env <变量名>` 或交互式隐藏输入传入。不要把密钥写进命令参数、文件、日志或回复里；没有现成环境变量时，让用户自己在终端里设置。
- 只有创建者能 `get` 详情；别人的凭证报 `CredentialNotFound` 不代表不存在，不要据此删除或重建。

## 常用

```bash
adp credential list --space-id <id> --fields credentialId,name,typeLabel,consumer --format json
adp credential consumers --space-id <id> --format json                      # 已配凭证的连接器/工具
adp credential referable --space-id <id> --consumer-id <plugin_id> --format json
adp credential create --space-id <id> --consumer-id <plugin_id> --name <name> --token-env MY_KEY --format json
adp credential update --space-id <id> --credential-id <id> --token-env NEW_KEY --format json
adp credential references --space-id <id> --credential-id <id> --format json
adp credential access --space-id <id> --credential-id <id> --referrer-type app_agent --referrer-id <agent_id> --format json  # 该引用方能否用此凭证
```

- `typeLabel`：`api_key`、`cam`、`oauth`、`aksk`。CLI 只能新建 API Key 凭证；腾讯云 CAM 凭证请用户在控制台创建。
- OAuth：`adp credential authorize --consumer-id <plugin_id>`（新建）或 `--credential-id <id>`（重新授权）返回 `authorizationUrl`，必须由用户本人在浏览器打开并同意；之后用 `adp credential authorization --authorization-id <auth_…>` 查结果（1 授权中、2 成功、4 失败）。平台对过期和不存在的授权号都回 3，CLI 统一报 `CredentialAuthorizationNotFound`（退出码 3），这时让用户重新 `adp credential authorize`。不要替用户打开或提交授权页。
- `credential access` 返回 `accessible` 和 `inaccessibleReason`，用于排查「智能体/工作流调用插件报凭证不可用」。引用方没引用该凭证时报 `CredentialNotReferenced`。
- `delete` 前 CLI 会查引用，被引用时报 `CredentialInUse` 且不删除。先用 `references` 告诉用户哪些应用/工作台在用，由用户决定替换方案；删除需要用户明确同意才加 `--yes`。
- `adp plugin oauth-url --plugin-id <id> --credential-id <id>` 为已有 OAuth 凭证生成授权链接，同样交给用户本人打开；`adp plugin auth check --plugin-id <id> --credential-id <id>` 查是否已授权（部分账号报 450002 无权限）。非 OAuth 2.0 插件报 `PluginNotOAuth`。

## 插件工具与跨空间共享

```bash
adp plugin tool get --plugin-id <id> --tool-id <id> --format json      # 工具入参/出参，tool-id 见 adp plugin get
adp plugin share get --plugin-id <id> [--pending] --format json         # scope: none | all | spaces；--pending 没有待审批配置时返回 hasPending:false
adp plugin share set --plugin-id <id> --scope spaces --space <sp> --yes --format json
adp plugin share set --plugin-id <id> --credential <cid>=all --yes      # 只改某个凭证的共享范围
```

- 共享是对外可见的变更，先问用户；可能进入审批（`status: "pending_approval"`），不要替用户催审或绕过。
- `PluginShareBlocked`：还有应用/智能体在用被收回的范围。把引用方列给用户，由用户决定先解绑；`--force --confirm-name <插件名>` 只给空间管理员用，且必须用户明确要求。
- `PluginShareRevisionConflict`：别人刚改过，直接重跑即可。
