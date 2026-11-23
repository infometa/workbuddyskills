# 密钥与凭证

本章节管理两类不同用途的凭据，切勿混用：

1. **工具密钥（ADP API Key：`adp plugin key`）**：账号级 Bearer 密钥（对应控制台「工具密钥」），用于直接调用平台托管的 MCP 插件网关（`https://adp.cloud.tencent.com/plugin/mcp/<pluginId>/mcp`）。
2. **连接器与插件出站凭证（`adp credential`）**：空间级凭证（`--space-id` 或 `adp.jsonc`），供插件/连接器在执行时访问第三方外部服务（如外部 API Key、OAuth 2.0）。

> **相关索引**：如何使用工具密钥直接调用平台 MCP 插件（如可灵视频生成）、查看实时 MCP 工具列表，或将导出的 MCP 插件通过 CLI + Skill 无缝接入各个 Coding Agent，详见 [mcp.md](mcp.md)。

---

## 安全规则

- 秘密值默认不落日志、不进命令行参数：不要把明文密钥写进命令参数、代码仓库、配置文件（如 `mcp.json` / `SKILL.md`）、日志或对话回复。
- 连接器凭证（`adp credential`）只写不读：`list`/`get` 不返回 token；创建或更新时仅通过 `--token-env <变量名>` 或交互式隐藏输入传入。
- 工具密钥（`adp plugin key`）仅在 `create` 瞬间由云端返回一次明文，CLI 默认直接写入本机 `~/.adp/tool-key`（权限 `0600`），终端输出默认打码；`list` 接口只返回脱敏值（如 `lf***C9lG`），无法从服务端再次取回明文。

---

## 工具密钥（ADP API Key）

用于鉴权直连平台 MCP 插件网关（调用方式见 [mcp.md](mcp.md#2-直接调用-mcp-插件如可灵)）。底层调用 LKE `CreateApiKey`、`DescribeApiKeyList`、`ModifyApiKey`、`ModifyApiKeyStatus`、`DeleteApiKey`。

```bash
adp plugin key list --format json                                      # 列出当前账号的工具密钥（脱敏值、status、lastAccessTime）
adp plugin key create --description "kling" --format json              # 创建并默认写入 ~/.adp/tool-key (0600)，输出脱敏
adp plugin key update --key-id <id> --description "new note" --format json
adp plugin key disable --key-id <id> --format json                     # 禁用密钥（status 变为 2；删除前必须先禁用）
adp plugin key enable --key-id <id> --format json                      # 重新启用密钥（status 变为 1）
adp plugin key delete --key-id <id> --yes --format json                # 删除已禁用的密钥（若与 ~/.adp/tool-key 相同则同步清理本地文件）
```

- **明文保存与显示**：`adp plugin key create` 默认将明文保存到 `~/.adp/tool-key`（权限 `0600`），不在终端回显完整密钥。仅当用户明确需要在终端查看明文时才加 `--reveal`。若传 `--no-save` 则必须同时加 `--reveal`，否则 CLI 拒绝执行，防止密钥创建后丢失。
- **密钥读取优先级**：当执行 `adp plugin tool call` 或 `adp plugin tool list`（见 [mcp.md](mcp.md)）时，按 `--api-key-env <变量名>` → 环境变量 `ADP_API_KEY` → `~/.adp/tool-key` 顺序读取。
- **数量上限与清理流程（`4509400` / `ToolKeyLimitReached`）**：
  - 平台每个账号最多允许同时存在 **2 把**工具密钥。超出时 `adp plugin key create`（以及真实执行的 `--auto-create-key`）报冲突错误 `ToolKeyLimitReached`（云端 `FailedOperation: 4509400-创建的密钥已达到上限`，退出码 `5`）。
  - 由于已有密钥的明文无法从服务端取回，若本机没有 `~/.adp/tool-key` 且未设置 `ADP_API_KEY`：
    1. 先运行 `adp plugin key list --format json` 查看现有密钥（`lastAccessTime` 为 `"0"` 表示从未使用过的闲置密钥）。
    2. 向用户确认要清理哪一把后，**必须先禁用再删除**：先执行 `adp plugin key disable --key-id <id> --format json`，再执行 `adp plugin key delete --key-id <id> --yes --format json`。
    3. 未禁用直接删除会报冲突错误 `ToolKeyNotDisabled`（云端 `4509404-密钥未处于禁用状态，请先禁用后再删除`，退出码 `5`）。
    4. 删除腾出额度后，再执行 `adp plugin key create --format json`。若用户手头已有明文密钥，直接将其设置到环境变量 `ADP_API_KEY` 即可，无需删旧建新。

---

## 连接器与插件出站凭证（`adp credential`）

按空间可见，供插件/连接器调用第三方外部服务时使用。只有创建者能 `get` 详情；别人的凭证报 `CredentialNotFound` 不代表不存在，不要据此删除或重建。

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

---

## 插件工具详情与跨空间共享

```bash
adp plugin tool get --plugin-id <id> --tool-id <id> --format json      # 工具入参/出参，tool-id 见 adp plugin get（直接调用 MCP 工具见 mcp.md）
adp plugin share get --plugin-id <id> [--pending] --format json         # scope: none | all | spaces；--pending 没有待审批配置时返回 hasPending:false
adp plugin share set --plugin-id <id> --scope spaces --space <sp> --yes --format json
adp plugin share set --plugin-id <id> --credential <cid>=all --yes      # 只改某个凭证的共享范围
```

- 共享是对外可见的变更，先问用户；可能进入审批（`status: "pending_approval"`），不要替用户催审或绕过。
- `PluginShareBlocked`：还有应用/智能体在用被收回的范围。把引用方列给用户，由用户决定先解绑；`--force --confirm-name <插件名>` 只给空间管理员用，且必须用户明确要求。
- `PluginShareRevisionConflict`：别人刚改过，直接重跑即可。
