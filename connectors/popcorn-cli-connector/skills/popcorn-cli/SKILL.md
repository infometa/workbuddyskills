---
name: popcorn-cli
display_name: 秒针爆米花 CLI 图片与视频生成
display_name_en: Miaozhen Popcorn CLI Image and Video Generation
description: Miaozhen Popcorn CLI is an AI creation toolkit for generating images and videos from
  the command line, checking task status, uploading reference assets, and managing folders, with browser-based
  authentication.
description_zh: 秒针爆米花 CLI AI 创作套件，支持通过命令行生成 AI 图片和视频，覆盖任务查询、参考素材上传、文件夹管理等功能，支持浏览器授权登录。
description_en: Miaozhen Popcorn CLI is an AI creation toolkit for generating images and videos from
  the command line, checking task status, uploading reference assets, and managing folders, with browser-based
  authentication.
examples_zh:
- 用秒针爆米花 CLI 按这个人物设定生成一张正面半身参考图，纯色背景。
- 把这张分镜图生成4秒的有声视频，镜头缓慢向前推进。
- 查询刚才提交的生成任务的状态，将成功的图片或视频下载到项目目录。
- 用秒针爆米花 CLI 将这些参考素材上传到素材库，放到我指定的文件夹。
examples_en:
- Use Miaozhen Popcorn CLI to generate a front bust reference image with a solid background based
  on this character setting.
- Generate a 4-second audio video from this storyboard image, with the camera slowly moving forward.
- Check the status of the generation tasks submitted just now, and download the successful images
  or videos to the project directory.
- Use Miaozhen Popcorn CLI to upload these reference materials to the material library and put them
  in my specified folder.
version: 1.1.2
author: zhangjx
---

# 秒针爆米花 CLI 图片与视频生成

## 适用范围

通过「秒针爆米花 CLI」（Miaozhen Popcorn CLI）连接器生成图片/视频、查询远端任务、上传或检索素材、管理文件夹。使用已安装的 `@baomihuatop/popcorn-cli@0.3.1`，服务地址为 `https://baomihua.top`。

仅写提示词、整理剧本或只读查看用户已有的本地媒体时，不提交生成、不发起连接授权。生成、模型/任务查询、素材及文件夹等远端业务操作只走本连接器的 CLI；CLI 不可用或未授权时暂停，不改用 ImageGen、VideoGen、其他供应商、MCP 或直接业务 API。

成功任务返回的媒体允许用宿主下载能力或系统下载工具取回；这些工具只用于下载已有结果和本地检查，不用于替代生成或直接调用业务 API。CLI 当前没有媒体下载子命令，取回步骤见 @references/commands.md 第 6.2 节。

## 输入与输出

| 项目 | 约定 |
| --- | --- |
| 输入 | 用户请求的操作、数量与范围；生成所需提示词、真实参考文件及当前模型能力；必要时提供任务 ID、目录 ID 或会话 ID。 |
| 输出 | 实际返回的任务/资源标识、查询状态、已取回的文件路径，以及已知消耗、异常和未完成项。 |
| 参数 | 按当前模型的 schema 构造 UTF-8 JSON 参数文件；保留本次实际提交参数，便于查询与复核。 |

不为单张图片、单条视频或素材查询强制创建漫剧项目结构；已有项目按其台账与路径约定记录。

## 执行步骤

### 1. 确认连接并检查身份

#### 宿主连接与安装定位

先确认 WorkBuddy 中本连接器已安装并连接；本机存在 CLI 不等于宿主连接完成。缺少 CLI 或版本不足时，引导用户安装/更新连接器；不自行安装 @latest、修改托管路径或启动登录进程。

- 连接器使用 WorkBuddy 托管的 Node.js 22，普通连接器使用不要求用户另装 Node.js。
- 版本检查针对配套 CLI 0.3.1，不把连接器或 Skill 的版本当作 CLI 版本。
- 命令找不到、npm 安装信息与实际版本不一致时，先只读核查当前 Shell 的 PATH、命令入口及版本，再引导处理；不能仅凭系统终端找不到命令断言宿主未安装。
- 定位命令见 @references/commands.md 第 2 节，用户明确询问手动安装或登录时再引用包内 README。

#### 任务前的远端身份核验

每次远端任务开始及中断恢复时，执行前置检查。每次 Shell 调用均显式携带两个 OAuth 环境变量，不假设不同 Shell 共享设置。

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

读取 CLI 自身的退出码：Bash 使用 `$?`，PowerShell 使用 `$LASTEXITCODE`，在检查命令结束后立即记录；后续命令可能覆盖该值。不能只凭 Shell 工具显示“执行成功”或标准输出中出现登录提示就认定前置检查通过。

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
- `auth ensure` 可按需续期已有 OAuth；普通 `auth status` 或本地可续期状态不能代替远端核验。
- 状态核查与注销细节见 @references/commands.md 第 3 节。

### 2. 查询真实能力并准备输入

先按请求选择 image/video models、任务、素材或文件夹命令，分别见 @references/commands.md 第 4、6、7、8 节。生成前查看具体模型详情，核对 `params_schema`、`model_limit`、参考要求和计费配置；未查明的模型、参数或权限不猜测。

仅上传本次所需的真实文件；优先复用已核验的资源。上传资源目录使用 `cli_upload`，生成产物目录使用 `cli_generate`，目录 ID 必须来自实际查询或创建结果。

用户只要求查询、上传或文件夹操作时，执行对应命令后结束，不额外提交生成；下面的范围、声音和生成提交步骤仅用于实际生成请求。

### 3. 核对范围与消耗

生成前，按用户已授权的数量、参数、参考、预计消耗和有限重试范围执行；费用按当前模型真实计费单位与实际参数估算，未知项标明未知，不伪造余额查询。新增费用或扩大范围超出已有授权时，先说明变化再确认。

- 默认图片超过 10 张或视频超过 5 条的批量操作先试产 1 个，再扩展本批；这属于本技能操作默认，不是平台限制。
- 用户已明确授权批次和重试范围时按授权执行，不重复询问同一许可。

### 4. 设置视频声音

#### 默认有声与模型参数

- 用户未明确要求静音时选择已核验支持声音的模型。schema 支持布尔 `generate_audio` 时显式传 true；其他模型按实际音频字段映射，能力未知或不支持时先说明，不静默改为无声。

#### 静音例外

- 只有用户明确要求静音才关闭并记录该要求。

#### 对白与声音边界

保留原有对白/VO/OS 的内容、人物、语言与时机；无对白时使用符合画面的环境声或动作音效，不擅自增加旁白、歌词或音乐。生成声音和制作字幕分别处理。

### 5. 提交、查询并取回

#### 参数快照与提交

- 将核对后的参数保存为本次尝试独立的 UTF-8 JSON 文件，不覆盖历史快照；写入失败时停止提交。
- 用 `image submit` 或 `video submit` 的 `--params-file` 提交，不要同时传 `--params`。
- Windows 使用 `.cmd` 入口和 PowerShell 文件写法，不照搬 Bash 内联 JSON。
- 防覆盖示例见 @references/commands.md 第 5.2、5.3 节。

#### 受理登记与结果取回

- 受理后立即记录真实 `task_id`、会话 ID（如有）、名称、参数和提交时间。
- 用 `task list -t` 查询原任务；queued/running 继续等待，不能把受理响应说成生成成功。
- 按 @references/commands.md 第 6 节查询并下载成功媒体，检查下载结果后记录真实本地路径；临时私有 URL 不直接作为最终交付。

## 异常与恢复

| 情况 | 动作 |
| --- | --- |
| 退出 3、无凭据、方式不匹配或授权失效 | 暂停远端任务，提示用户在【专家·技能·连接器 → 连接器】中安装/更新「秒针爆米花 CLI」，点击「连接」，在浏览器登录授权，返回 WorkBuddy 等待显示已连接后重新检查。 |
| 正在等待浏览器授权 | 等待当前授权完成；不重复启动登录，也不凭旧登录态认定本次成功。 |
| 服务地址不符 | 暂停并只读核对 `config show`；按命令参考第 9 节转到 README 的手动恢复说明。解释共享登录态会受影响，由用户确认后手动恢复；不自动切换地址或迁移授权，仅重新连接不会修正已有地址。 |
| 退出 1、网络/存储错误、无效输出或刷新结果不确定 | 报告无法确认并暂停；保留已有凭据，不自动登录、绑定 Key、放宽凭证权限或执行 logout。 |
| 参数解析或模型约束失败 | 修正本次 UTF-8 参数文件并重新校验；不靠更换供应商或拼接长 JSON 绕过。 |
| 查询失败、排队或等待超时 | 保留原 task_id 和真实状态，继续查询原任务，不新建 submit。 |
| 提交/上传响应丢失，结果是否受理不明确 | 按已有会话、名称、时间或资源记录先查询；未查明前不重复提交或上传。 |
| 远端明确失败或素材需重做 | 说明证据和预计新增消耗，仅在既有费用与次数授权内重试；超出范围先确认。 |

只有用户明确要求断开时，才按命令参考执行 `auth logout`，并说明终端与 WorkBuddy 共享当前登录态。取消一次等待不是注销，CLI 没有远端任务取消或余额查询命令。

按注销响应区分本地清理与远端撤销，核对退出码以及 `logged_out`、`local_cleared`、`remote_revoked`；远端撤销未确认时如实说明，不把本地已退出说成远端已全部撤销。

不读取凭据文件、不回显密码、Key、access/refresh 或完整临时授权链接；诊断资料先脱敏。空闲时不定时刷新认证。

## 完成检查

- 区分已受理、执行中、成功、失败、未决与未审查；汇报真实任务/资源标识和可用文件路径。
- 视频下载后检查音轨并实际回听；工具不可用或不能播放时说明检查未完成。无音轨、全静音或缺失关键对白不能仅凭任务成功判为合格。
- 音频检查、画面审查、字幕和剪辑分别说明结果；不声称 CLI 已完成未接入的自动剪辑或声音后期。
- 汇报已知消耗及未知项，保留本次提交参数和恢复线索；检查失败不自动授权付费重投。

## 按需参考

- @references/commands.md：第 2 节定位与版本，第 3 节认证，第 4 节模型，第 5 节提交及参数文件，第 6 节任务与下载，第 7 节素材，第 8 节文件夹，第 9 节错误恢复；仅阅读当前操作需要的小节。
