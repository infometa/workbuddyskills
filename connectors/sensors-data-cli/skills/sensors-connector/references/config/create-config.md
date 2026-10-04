# config.create 首次配置引导

> 工具 `config.create` · 命令 `sensors config init` · 类型 写入

## 用途

本机尚未配置 `~/.sensors/config.toml` 时，在对话中一步步引导用户完成初始化：逐项收集连接与项目信息，非交互写入配置文件，验证生效后回到会话建立。以下任一输出即为本工具的进入信号：

- `context.session-start` 返回 `{"ok": false, "error": {"type": "param", "message": "无法初始化会话上下文: [auth] No configuration found at ~/.sensors/config.toml | Hint: 先补充基础配置信息，再重新执行当前操作，请先运行 sensors setup 完成配置"}}`
- 业务命令以 Python traceback 形态抛出 `cli.core.errors.ConfigNotFoundError: [auth] No configuration found at ~/.sensors/config.toml`
- `sensors doctor` 报告首项为 `[失败] 还没有找到配置文件。`

判定口径：输出含 `No configuration found` 即未配置；`doctor` 的 `config_exists` 检查通过说明配置已存在，直接跳过本工具建立会话，不重复初始化。仅修改局部字段（如开启写操作、补默认项目）用 `sensors config update-context`，不重跑本命令。

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 | 示例值 |
|---|---|---|---|---|---|
| `--base-url` | string | 是 | — | 神策平台访问地址，须为完整 URL（`http(s)://host[:port]`），来自平台地址栏或内网访问地址 | `https://demo.sensorsdata.cn` |
| `--api-key` | string | 是（或 `--api-key-stdin`） | — | 调用平台接口的凭证，在神策平台 API Key 管理页面创建或复制；`--api-key-stdin` 改从 stdin 首行读取 | `—` |
| `--project` | string | 否 | 空 | 默认项目英文名；缺省时业务命令需显式传 `--project` | `default` |
| `--org-id` | string | 否 | 空 | 组织 ID，Horizon / SF 平台命令需要 | `1` |
| `--account-id` | string | 否 | 空 | 账户 ID，SF 平台命令需要 | `—` |
| `--env-name` | string | 否 | `default` | 环境（base_url + api_key 组合）名称 | `default` |
| `--context-name` | string | 否 | `default` | 上下文（环境 + 项目）名称 | `default` |
| `--from-env` | path | 否 | — | 从 key=value 文件导入 `base_url` / `api_key` / `project` / `org_id` / `account_id` | `./sensors.env` |
| `--reset` / `--yes` | flag | 否 | 关 | 清空并重建全部配置，属破坏性动作；本工具禁止使用 | — |

本命令是本地配置操作，不产生平台请求，不需要 `--ai-session-id`，也不支持 `--dry-run`。

写入语义（命令层事实）：配置文件不存在时按提供值全新初始化（安全）；已存在且未加 `--reset` 时为合并模式——只更新本次显式提供的字段，保留其它环境 / 上下文与当前活跃上下文。

## 输入 Schema

无 `--input` 复杂输入，参数见上表。执行成功后配置落盘结构：

| 配置项 | 落盘位置 | 必填 | 说明 |
|---|---|---|---|
| `base_url` | `environments.<env-name>` | 是 | 平台访问地址 |
| `api_key` | `environments.<env-name>` | 是 | 认证密钥，明文存储于本机 |
| `project` | `contexts.<context-name>` | 否 | 默认项目英文名，业务命令缺省项目时使用 |
| `org_id` / `account_id` | `contexts.<context-name>` | 否 | Horizon / SF 平台命令需要时提供 |
| `write_operations_enabled` | `contexts.<context-name>` | 否 | 写操作开关，默认关闭，不随本命令开启 |

## 构造流程

命令层固定步骤：判定现状 → 逐项收集 → 写入前确认 → 写入 → 验证 → 补默认项目 → 回到会话建立。

1. **判定现状**：以触发本工具的错误输出为准；不确定时先跑 `sensors doctor`（本地体检，含轻量网络检查）。`config_exists` 通过即配置已存在，不进入初始化。
2. **逐项收集**：向用户说明需要以下信息并逐项取得，不猜测、不编造：
   - Base URL：平台访问地址；
   - API Key：用户在神策平台 API Key 管理页面创建或复制；
   - 默认项目英文名：用户知道则一并收集，不知道可留空，第 6 步从项目列表引导选择；
   - `--org-id` / `--account-id`：仅用户表明是 Horizon / SF 平台时询问。
   同时告知用户两点：API Key 会明文写入 `~/.sensors/config.toml`，并出现在本对话的命令中；不希望如此可改为自己在终端运行 `sensors setup`（交互式向导，另可安装各平台技能），配置完成后回到对话继续。
3. **写入前确认**：向用户复述将写入的值——Base URL、项目名原样展示，API Key 只展示前 3 后 3 位脱敏形式；获用户明确同意后才执行下一步。
4. **写入**（未配置时为全新初始化，安全）：

   ```bash
   sensors config init --base-url https://demo.sensorsdata.cn --api-key <api_key> [--project default]
   ```

   禁止携带 `--reset` / `--yes`：会清空已有配置，本工具只在无配置时新建。参数校验失败（如 `Invalid URL`）按错误修正后重试，修正上限一次。
5. **验证**：运行 `sensors doctor`，要求各项检查全部「通过」后再继续。失败项处理：`base_url_reachable` 失败 → 与用户核对地址或网络（含代理环境）；`api_key_project_access` 失败 → API Key 无效或无项目权限，回到第 2 步更正后以合并模式重写（不带 `--reset`）。
6. **补默认项目**（第 2 步未收集项目名时）：先 `sensors context session-start --ai-goal "<目标>"` 取得 `ai_session_id` 与 `number_of_projects`，再 `sensors context project-list --ai-session-id <id> --format json` 列出项目；多候选时把清单交用户选择，禁止代选。用户选定后写入：

   ```bash
   sensors config update-context default --project <项目英文名>
   ```

7. **回到会话建立**：重新执行 `context.session-start`（此前因未配置失败的会话不算数），拿到 `ai_session_id` 后继续原任务。

## 输出

```json
{
  "ok": true,
  "data": {
    "message": "Configuration initialized at ~/.sensors/config.toml"
  }
}
```

- 全新初始化输出 `Configuration initialized at <path>`；配置已存在且走合并模式输出 `Configuration merged at <path> (other config preserved)`。
- 验证阶段 `sensors doctor` 输出中文体检报告（纯文本，每项一行「通过 / 失败 / 提醒 / 跳过」并附修复建议）。
- 需要向用户展示当前生效配置时用 `sensors config show`：API Key 输出为脱敏形式（前 3 位 + `***` + 后 3 位），不暴露完整密钥。

## 错误

| 错误 | 触发条件 | 修正方式 |
|---|---|---|
| `Invalid URL: <值>`（code param） | `--base-url` 缺协议头或不是合法 URL | 补全 `http://` 或 `https://` 前缀后重试 |
| `API key cannot be empty`（code param） | 未提供 API Key | 回到收集步骤取得后重试 |
| doctor `base_url_reachable` 失败 | 地址错误或网络不通（含代理环境） | 与用户核对地址与网络后以合并模式重写 |
| doctor `api_key_project_access` 失败 | API Key 无效或对项目无权限 | 用户在平台核对密钥与权限后重写，不换项目重试 |
| `覆盖现有配置需显式确认：请加 --yes` | 非交互场景携带了 `--reset` | 本工具禁止 `--reset`；确需重置时引导用户在终端自行确认执行 |
| 写入成功但业务命令仍报未配置项目 | 未配置默认项目且未传 `--project` | 执行构造流程第 6 步补默认项目 |

## 使用约束

- 真实写入前完成「写入前确认」：向用户复述将写入的配置项并获明确同意；信息变化后重新确认。未加 `--reset` 时本命令对已有配置只合并显式字段，不会覆盖用户其它环境或上下文。
- 写操作开关（`write_operations_enabled`）默认关闭且不随本命令开启；是否开启由用户决策，需要时引导用户执行 `sensors config update-context <上下文名> --write-operations-enabled`，不代开。
- 不在对话输出中回显完整 API Key，展示一律脱敏；告知用户密钥明文存储于本机 `~/.sensors/config.toml`。
- `sensors setup` 是终端交互式向导（含技能安装），Agent 不代跑；用户倾向自行操作时推荐该入口并在配置完成后继续任务。
- 引导完成后必须重新执行 `context.session-start` 建立会话；原任务的业务请求在会话建立后进行。
