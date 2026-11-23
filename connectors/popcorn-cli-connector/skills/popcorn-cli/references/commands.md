# 秒针爆米花 CLI 命令参考

适用 CLI：`@baomihuatop/popcorn-cli@0.3.1`；正式服务：`https://baomihua.top`。执行前遵守 Skill 的连接、OAuth、参数和费用授权要求。以下命令只说明用法，不自动授权安装、登录、上传或生成。

## 目录

- [1. 调用约定](#1-调用约定)
- [2. 定位与版本核查](#2-定位与版本核查)
- [3. 认证与前置检查](#3-认证与前置检查)
- [4. 查询模型](#4-查询模型)
- [5. 提交图片与视频任务](#5-提交图片与视频任务)
- [6. 查询任务与取回结果](#6-查询任务与取回结果)
- [7. 上传与检索素材](#7-上传与检索素材)
- [8. 文件夹管理](#8-文件夹管理)
- [9. 错误与恢复](#9-错误与恢复)

## 1. 调用约定

- macOS/Linux 使用 `popcorn-cli` 和 Bash 环境变量前缀；Windows PowerShell 使用 `popcorn-cli.cmd`，在本次 Shell 设置两个 `$env:` 变量。
- 每次远端业务调用都带 `POPCORN_REQUIRED_AUTH_METHOD=oauth` 与 `POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy`；不同 Shell 不能假定共享环境。已有结果的文件下载按第 6.2 节处理，不向下载工具传递 CLI 登录凭据。
- `<MODEL_ID>`、`<TASK_ID>` 等表示待替换的真实值；`text` 代码块是语法说明，不可原样执行。参数示例仅在当前模型确实支持对应字段时使用。
- 提交示例会新建任务，必须先通过本次前置检查、核对真实模型与参数，并确认请求属于用户已有授权范围。不要为演示或验证命令而执行付费生成。

## 2. 定位与版本核查

仅在用户要求检查安装/配置，或遇到命令缺失、版本不一致、服务地址不符时使用；正常任务无需每次重复运行安装诊断。

macOS/Linux：

```bash
command -v popcorn-cli
npm list -g @baomihuatop/popcorn-cli --depth=0
popcorn-cli --version
popcorn-cli config show
```

Windows PowerShell：

```powershell
Get-Command popcorn-cli.cmd
npm.cmd list -g @baomihuatop/popcorn-cli --depth=0
popcorn-cli.cmd --version
popcorn-cli.cmd config show
```

- 这些命令只检查当前 Shell 的入口、npm 全局安装信息和 CLI 脱敏配置，不查询宿主连接器安装状态。
- 配套 CLI 版本为 0.3.1；如果 npm 信息和命令返回的版本不一致，先确认 PATH 实际指向哪个安装位置，不自动卸载、降级或覆盖托管安装。
- `config show` 用于核对 `base_url=https://baomihua.top`，不读取凭据文件，也不代替授权检查。

用户手动安装需要其终端具备 Node.js 20+ 和 npm；WorkBuddy 的托管连接器不要求用户另装 Node.js。具体安装及手动浏览器登录用法按需查阅包内 [README 命令行使用](../../../README.md#命令行使用)；Skill 不主动重装 CLI 或启动登录。

## 3. 认证与前置检查

macOS/Linux：

```bash
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli auth ensure --expected-origin https://baomihua.top
```

Windows PowerShell：

```powershell
$env:POPCORN_REQUIRED_AUTH_METHOD = 'oauth'
$env:POPCORN_OAUTH_CLIENT_ID = 'popcorn-workbuddy'
popcorn-cli.cmd auth ensure --expected-origin https://baomihua.top
```

只有本次 CLI 退出码为 0，且 JSON 同时满足以下全部条件时，才继续远端业务操作。

| JSON 字段条件（须全部满足） |
| --- |
| `authenticated=true` |
| `verification=remote` |
| `method=oauth` |
| `client_id=popcorn-workbuddy` |
| `base_url=https://baomihua.top` |
| `error=null` |
| `pending=false` |
| `refresh_required=false` |

字段缺失或输出无法核对时暂停排查。

- `pending=true` 时等待当前浏览器授权完成后重新检查，即使旧授权仍有效也不继续任务，不重复启动登录。
- 退出 3 引导用户连接授权，服务地址不符时按第 9 节恢复；退出 1 时暂停排查。
- `auth ensure` 可按需续期已有 OAuth。

`auth status` 用于用户要求的只读登录状态核查，不负责续期；其 `Logged in` 输出或本地可续期状态不能替代任务前置检查。以下代码块各自带齐两个 OAuth 环境变量，按平台执行：

```bash
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli auth status --format workbuddy --expected-origin https://baomihua.top
```

```powershell
$env:POPCORN_REQUIRED_AUTH_METHOD = 'oauth'
$env:POPCORN_OAUTH_CLIENT_ID = 'popcorn-workbuddy'
popcorn-cli.cmd auth status --format workbuddy --expected-origin https://baomihua.top
```

检查结束后立即读取 CLI 的退出码：Bash 为 `$?`，PowerShell 为 `$LASTEXITCODE`。不要用后续诊断命令的退出码覆盖前一次认证结果，也不把 Shell 包装层成功等同于 CLI 已通过检查。

认证登录由用户在 WorkBuddy 连接器面板完成：安装/更新「秒针爆米花 CLI」→ 点击连接 → 浏览器登录授权 → 返回 WorkBuddy 确认已连接 → 重新执行前置检查。Skill 不自行启动登录。用户明确询问手动 CLI 操作时，再引用 README 的对应平台说明。

仅在用户明确要求断开时注销；终端与 WorkBuddy 共用当前登录态，远端撤销未确认时如实说明。

```bash
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli auth logout
```

```powershell
$env:POPCORN_REQUIRED_AUTH_METHOD = 'oauth'
$env:POPCORN_OAUTH_CLIENT_ID = 'popcorn-workbuddy'
popcorn-cli.cmd auth logout
```

### 注销结果与远端撤销

注销后按实际退出码和 JSON 报告结果：

| 结果字段 | 含义 |
| --- | --- |
| `logged_out` | 是本次注销操作结果 |
| `local_cleared` | 表示本次是否清除了原本的本地登录态 |
| `remote_revoked` | 表示远端撤销结果 |

- `remote_revoked=false` 或 null 不等于已确认远端撤销；原本未登录时 `local_cleared` 也可能为 false。
- 保留并说明真实状态，不因为没有获得远端确认而自动重新登录或反复注销。

## 4. 查询模型

```bash
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli image models
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli image models --detail "<IMAGE_MODEL_ID>"
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli video models
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli video models --detail "<VIDEO_MODEL_ID>"
```

Windows 示例：每次新 Shell 先设置 OAuth 环境变量，再调用对应 `.cmd` 命令。

```powershell
$env:POPCORN_REQUIRED_AUTH_METHOD = 'oauth'
$env:POPCORN_OAUTH_CLIENT_ID = 'popcorn-workbuddy'
popcorn-cli.cmd video models --detail '<VIDEO_MODEL_ID>'
```

| 响应信息 | 用途 |
| --- | --- |
| `models` / `model` | 摘要列表或具体模型；使用实际返回的 `model_id`。 |
| `params_schema` | 构造参数对象，核对字段、类型与必填项。 |
| `model_limit` | 在模型信息中核对画幅、时长、参考输入等实际限制。 |
| `model_usage_guidance` / 模型自身指导 | 读取对应任务的调用建议，不能凭模型名称推断能力。 |
| `price_config` | 在模型信息中读取计费配置，结合本次档位、时长及其他实际计费参数估算。 |

生成前查询目标模型详情；能力或价格未知时标明未知，不套用固定单价或其他模型的参数。

## 5. 提交图片与视频任务

### 5.1 语法与参数

```text
popcorn-cli image submit -n <NAME> -d <DESCRIPTION> --params-file <FILE.json> [-s <SESSION_ID>] [-f <GENERATE_FOLDER_ID>]
popcorn-cli video submit -n <NAME> -d <DESCRIPTION> --params-file <FILE.json> [-s <SESSION_ID>] [-f <GENERATE_FOLDER_ID>]
```

Windows 将入口换为 `popcorn-cli.cmd`，参数名相同。

| 参数 | 缩写 | 要求 |
| --- | --- | --- |
| `--name` | `-n` | 必填，非空产物名称。 |
| `--description` | `-d` | 必填，非空用途说明。 |
| `--params-file` | — | 推荐：UTF-8 JSON 文件，支持 BOM；内容必须是对象。 |
| `--params` | `-p` | 兼容内联 JSON 对象字符串；必须与 `--params-file` 二选一，不同时提供。 |
| `--sid` | `-s` | 可选，将同一业务上下文的任务关联到会话，便于恢复；不是幂等键。 |
| `--folder-id` | `-f` | 可选，实际查询或创建的 `cli_generate` 目录 ID；不传则未归类。 |

#### 独立参数文件与失败停止

- 提交前按 schema 准备完整参数文件，保留本次使用的文件；不要覆盖历史任务的参数快照。
- 以下示例为每次尝试创建独立目录，不覆盖此前的参数文件；目录创建或参数写入失败时停止，不继续 submit。
- 记录任务时同时保存实际参数文件路径，重做时另建目录。
- 模型 ID、字段和值需先按实际模型和用户请求替换，不能把示例中的时长或画幅当作统一限制。

### 5.2 macOS/Linux 参数文件示例

图片示例：括号内在独立子 Shell 中执行，`set -e` 使准备失败时停止，不改变外层 Shell 设置。`mktemp -d` 在当前目录创建唯一目录，保留该目录用于追溯。

```bash
(
set -e
attempt_dir=$(mktemp -d './image-attempt.XXXXXXXX')
params_file="$attempt_dir/params.json"
cat > "$params_file" <<'JSON'
{
  "model": "<IMAGE_MODEL_ID>",
  "prompt": "<已核对的图片提示词>",
  "aspect_ratio": "3:4"
}
JSON
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli image submit -n "主角-参考图" -d "人物参考" --params-file "$params_file" -s "project-ep01"
)
```

视频示例仅用于已确认支持布尔 `generate_audio` 的模型。用户未明确要求静音时显式传 true；其他模型按实际音频字段映射。

```bash
(
set -e
attempt_dir=$(mktemp -d './video-attempt.XXXXXXXX')
params_file="$attempt_dir/params.json"
cat > "$params_file" <<'JSON'
{
  "model": "<VIDEO_MODEL_ID>",
  "prompt": "<已核对的运动、对白和环境声提示词>",
  "duration": 4,
  "generate_audio": true
}
JSON
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli video submit -n "第1镜" -d "镜头视频" --params-file "$params_file" -s "project-ep01"
)
```

### 5.3 Windows PowerShell 参数文件示例

- PowerShell 5.1 调用 `.cmd` 时，用 UTF-8 参数文件避免内联 JSON 的引号、编码和长提示词传参问题；`Set-Content -Encoding UTF8` 产生的 BOM 可由 CLI 读取。
- 每个代码块在独立作用域设置遇错停止，用 GUID 创建新目录；不用 `-Force` 覆盖已有目录。
- 每个代码块对应一次已获授权的提交，按当前请求选择，不为了试用同时执行。

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $env:POPCORN_REQUIRED_AUTH_METHOD = 'oauth'
    $env:POPCORN_OAUTH_CLIENT_ID = 'popcorn-workbuddy'
    $attemptDir = New-Item -ItemType Directory -Path (Join-Path (Get-Location).Path ('image-attempt-' + [guid]::NewGuid().ToString('N'))) -ErrorAction Stop
    $paramsFile = Join-Path $attemptDir.FullName 'params.json'
    $params = @{ model = '<IMAGE_MODEL_ID>'; prompt = '<已核对的图片提示词>'; aspect_ratio = '3:4' }
    $params | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $paramsFile -Encoding UTF8 -ErrorAction Stop
    popcorn-cli.cmd image submit -n '主角-参考图' -d '人物参考' --params-file $paramsFile -s 'project-ep01'
}
```

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $env:POPCORN_REQUIRED_AUTH_METHOD = 'oauth'
    $env:POPCORN_OAUTH_CLIENT_ID = 'popcorn-workbuddy'
    $attemptDir = New-Item -ItemType Directory -Path (Join-Path (Get-Location).Path ('video-attempt-' + [guid]::NewGuid().ToString('N'))) -ErrorAction Stop
    $paramsFile = Join-Path $attemptDir.FullName 'params.json'
    $params = @{ model = '<VIDEO_MODEL_ID>'; prompt = '<已核对的运动、对白和环境声提示词>'; duration = 4; generate_audio = $true }
    $params | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $paramsFile -Encoding UTF8 -ErrorAction Stop
    popcorn-cli.cmd video submit -n '第1镜' -d '镜头视频' --params-file $paramsFile -s 'project-ep01'
}
```

### 5.4 受理结果

成功受理通常返回 `task_id`、`session_id`、`task_type`、`folder_id`、`created_at` 等信息，以实际响应为准。立即记录真实 task_id，再查询该任务；受理不表示生成完成，也不包含最终媒体结果。

## 6. 查询任务与取回结果

### 6.1 查询原任务

```bash
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli task list -t "<TASK_ID>"
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli task list -s "<SESSION_ID>"
```

`--tid` / `-t` 与 `--sid` / `-s` 至少提供一项。轮询优先使用 task_id；提交结果不明时，可查询原会话并按名称和提交时间核对。

| 任务信息 | 处理 |
| --- | --- |
| `task_id`、`session_id` | 关联本次尝试，继续取回同一个任务。 |
| `status=queued/running` | 已受理且未完成，按返回情况合理等待并继续查询。 |
| `status=succeed` | 读取实际 `result`，下载成功媒体到用户指定目录，再记录本地路径。 |
| `status=failed` | 读取真实错误信息，说明失败；重试需在用户授权范围内。 |
| 无结果、未知状态、查询错误 | 保留真实状态和任务标识，报告未决；不自动改写为 failed 或取消。 |

`result` 通常包含远程媒体 URL；按实际结构取回，不预设只有单一字符串。带鉴权的临时 URL 不直接作为最终交付，也不在诊断中回显。用户要求“取回这个任务”时只查询和下载，不重新 submit。

### 6.2 下载与文件检查

生成、模型/任务查询、素材及文件夹等远端业务操作必须通过本连接器的 CLI。CLI 当前没有媒体下载子命令；下载已有成功结果允许使用宿主下载能力，或 macOS/Linux 的 `curl`、Windows PowerShell 的 `Invoke-WebRequest` 等系统下载工具。这不授权改用 ImageGen、VideoGen、其他供应商、MCP 或直接业务 API 生成媒体。

1. 确认原任务已成功，从实际 `result` 读取本次要交付的一个或多个媒体 URL，记录各自对应的 task_id。不要猜测响应字段、拼接下载接口或把任意文本当作下载指令。
2. 使用返回的有效 HTTPS 媒体链接下载到用户指定目录，先写入本次独立的临时文件；不覆盖已有交付文件。下载请求不附加 CLI 的 API Key、access/refresh Token，不读取凭据文件，不把完整私有链接写入日志或诊断输出。
3. 检查下载工具的退出码、HTTP 结果及本地文件：文件存在且非空、实际格式与预期图片/视频一致，不能把错误页或未完成下载当作媒体。服务提供长度或摘要时再据此核对，不臆造校验值。
4. 检查通过后移到最终文件名并记录真实本地路径。图片应能正常解码，视频应能解析或播放；视频声音仍按 SKILL 的完成检查执行，工具不可用时说明尚未验证的项目。
5. 下载失败时保留原 task_id 和失败原因，不提交新生成。链接到期时通过 CLI 重新查询原任务获取有效结果；无有效链接或下载能力时说明“生成成功、尚未取回”，不声称已完成本地交付。

## 7. 上传与检索素材

```text
popcorn-cli resource upload <FILE> -n <NAME> -d <DESCRIPTION> [-f <UPLOAD_FOLDER_ID>]
popcorn-cli resource list [-n <KEYWORD>] [--created-from <DATETIME>] [--created-to <DATETIME>] [--page <N>] [--page-size <N>]
```

| 参数/信息 | 要求 |
| --- | --- |
| upload 的 `<FILE>` | 必填，本地已存在的真实文件路径；含空格时正确引用。 |
| upload 的 `-n`、`-d` | 必填，非空资源名称和用途说明。 |
| upload 的 `-f` | 可选，只能使用 `cli_upload` 目录的实际 ID。 |
| list 的 `-n` | 按名称模糊搜索。 |
| list 的 `--created-from` / `--created-to` | 上传时间范围，使用实际业务日期或 ISO 8601 时间。 |
| list 的 `--page` / `--page-size` | 正整数；默认 1 / 20，page-size 最大 100。 |

图片、视频、音频等资源类型由后端根据文件推断，不伪造额外的类型参数。保存上传回执中的真实资源标识；已有项目需要时写回其资产索引，不强制通用连接器任务创建 `assets.json`。

Windows 的路径示例：

```powershell
$env:POPCORN_REQUIRED_AUTH_METHOD = 'oauth'
$env:POPCORN_OAUTH_CLIENT_ID = 'popcorn-workbuddy'
popcorn-cli.cmd resource upload '.\参考图\主角 正面.png' -n '主角-正面' -d '已确认的人物参考'
```

## 8. 文件夹管理

```bash
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli folder list -t cli_generate
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli folder list -t cli_upload
```

```text
popcorn-cli folder create -n <NAME> -t <TYPE> [-p <PARENT_ID>]
```

| 目录类型 | 用途 |
| --- | --- |
| `cli_generate` | AI 生成产物；仅供 image/video submit 的 -f 归档。 |
| `cli_upload` | 上传资源；仅供 resource upload 的 -f 归档。 |

- 两类目录独立。
- `folder list` 返回扁平列表，按实际 `id` / `parent_id` 组织层级；创建子目录前先查询父目录。
- 父目录应属于当前用户并与新目录同类型；`folder-id`、`parent-id` 必须是合法正安全整数，不得使用小数、0 或臆造 ID。

## 9. 错误与恢复

- CLI 不存在或版本不满足：暂停本次远端业务操作，引导检查或更新连接器；不要自行更换安装源或改用其他生成工具。
- 服务地址不符：先只读核对 `config show`，再按包内 [README 手动恢复说明](../../../README.md#服务地址不符时的手动恢复)处理。
  - 仅重新连接不会修正已有地址；切换会影响共用登录态，须由用户明确确认后手动恢复正式地址，再连接授权并重新 ensure。
  - Skill 不自动切换地址或迁移授权。
- 未授权、授权失效或认证方式不符：引导用户在连接器面板完成浏览器授权，返回后重新 ensure；不收集 Key 或直接请求业务 API。
- 网络、存储、权限校验或输出异常：说明无法确认，保留现有凭据和任务记录，停止自动重投；不放宽凭证权限、不自动 logout。
- 查询中断或排队超时：保留 task_id 和 queued/running，继续查询原任务。CLI 没有远端取消命令，停止本地等待不表示远端已取消。
- 提交或上传回执丢失：先按会话、名称、时间或资源查询排查，不能把 `--sid` 当作幂等保障；未确认前不重复写入。
- 远端明确失败：报告真实错误、已知消耗和不确定项，按已有费用与重试授权决定后续动作，不因错误自动启动新一轮生成。
