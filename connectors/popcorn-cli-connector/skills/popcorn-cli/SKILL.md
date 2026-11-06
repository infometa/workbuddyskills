---
name: "popcorn-cli"
display_name: "秒针爆米花 CLI 图片与视频生成"
display_name_en: "Miaozhen Popcorn CLI Image and Video Generation"
description: "Miaozhen Popcorn CLI is an AI creation toolkit for generating images and videos from the command line, checking task status, uploading reference assets, and managing folders, with browser-based authentication."
description_zh: "秒针爆米花 CLI AI 创作套件，支持通过命令行生成 AI 图片和视频，覆盖任务查询、参考素材上传、文件夹管理等功能，支持浏览器授权登录。"
description_en: "Miaozhen Popcorn CLI is an AI creation toolkit for generating images and videos from the command line, checking task status, uploading reference assets, and managing folders, with browser-based authentication."
examples_zh: ["用秒针爆米花 CLI 按这个人物设定生成一张正面半身参考图，纯色背景。", "把这张分镜图生成4秒的有声视频，镜头缓慢向前推进。", "查询刚才提交的生成任务的状态，将成功的图片或视频下载到项目目录。", "用秒针爆米花 CLI 将这些参考素材上传到素材库，放到我指定的文件夹。"]
examples_en: ["Use Miaozhen Popcorn CLI to generate a front bust reference image with a solid background based on this character setting.", "Generate a 4-second audio video from this storyboard image, with the camera slowly moving forward.", "Check the status of the generation tasks submitted just now, and download the successful images or videos to the project directory.", "Use Miaozhen Popcorn CLI to upload these reference materials to the material library and put them in my specified folder."]
version: "1.1.1"
author: "zhangjx"
---

# 秒针爆米花 CLI 图片与视频生成

通过「秒针爆米花 CLI」（Miaozhen Popcorn CLI）连接器使用 npm 正式版 `@baomihuatop/popcorn-cli@0.3.0`，认证服务和业务服务均为 `https://baomihua.top`。使用已安装的 CLI，不调用 MCP，不直接请求业务 API。

## 认证前置

每次任务先执行 `popcorn-cli config show`，只读核对 `base_url` 必须为 `https://baomihua.top`；若不同，停止调用并引导用户重新连接生产连接器。切换地址会使原地址的登录态失效，不自动迁移凭证。每次 Shell 调用显式携带 OAuth 约束；不同 Shell 不共享 export 或 alias：

~~~bash
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli auth ensure
~~~

| 结果 | 动作 |
| --- | --- |
| 退出 0、verification=remote | 当前身份已核对；业务能力仍独立判断 |
| access 临近到期或已到期、refresh 仍有效 | ensure 在前台按需续期并保存轮换凭证，再查询远端身份；不启动后台 Worker |
| 退出 3、未登录或方式不匹配 | 停止任务，引导用户在【连接器】中选择「秒针爆米花 CLI」（Miaozhen Popcorn CLI）并点击“连接” |
| 正在等待授权 | 等用户完成当前浏览器流程，不重复启动登录 |
| 退出 1、网络/存储/不确定结果 | 报告无法确认；保留凭证，不自动注销或绑定 Key |

每次任务开始及长任务恢复时先执行 ensure，成功后再继续；空闲时不定时刷新。普通 auth status 仍只读，不负责续期，不能将其 local/refresh_required=true 当作远端已核实。刷新响应丢失时不得重放旧 refresh 或自动重新登录，提示用户重新连接。

连接器在安装和发起新授权时通过 `config set-url https://baomihua.top` 明确选择生产服务；宿主的状态检查只读取地址与 `auth status`，不会刷新凭证。连接时 WorkBuddy 执行前台 auth login --no-browser --adapter workbuddy，打开完整授权链接；用户通过现有账号密码登录并明确确认。CLI 自己换票和保存凭证，完成保存后唤起 WorkBuddy 连接器页，再退出成功；唤起失败按提示手动返回。不要自行在 Agent 内另启动授权进程，不使用 --background，不索要密码或授权链接内容。

授权被拒绝或五分钟内未完成时，用户可重新点击连接。没有手动确认码入口，不要求复制任何确认码。取消本次登录不等于注销当前账号；不要为清理失败自动执行 logout。

## 业务能力边界

CLI 已支持模型、生成、任务、资源及目录的 OAuth 请求；发送前自动续期并核对请求身份，实际权限、数据和计费以目标后端为准。若仍出现 BUSINESS_OAUTH_NOT_READY，属于旧 CLI 包的本地门禁，先核对实际路径与版本并更新；不通过重新登录、绑定 API Key、网页 Bearer 或直接 API 绕过。

按 @references/commands.md 使用真实命令，并逐次带相同的 OAuth 环境前缀。参数以服务端返回的模型与 schema 为准；任务创建响应只表示受理，不表示生成成功。写请求超时或结果不确定时不自动重新提交，避免重复任务。

## 视频默认有声

用户未明确要求静音时，优先选择已核实支持音频的模型。构造 video submit 的 `-p` 时，详情 schema 为 `generate_audio: boolean` 就**显式传 `"generate_audio": true`**，不依赖省略后的默认值，不为了省费用、没有对白或减少干扰写 false。其他模型按真实音频字段和调用指导映射；能力未知先查详情，不支持时交代缺口，不静默产出无声视频。

提示词写清原有对白/VO/OS 的原句、人物、语言和时机；无对白时保留与画面一致的环境声或动作音效，不添加来源没有的解说、歌词或背景音乐。只有用户明确要求静音才关闭，并在项目记录该要求。

生成后下载视频，具备 ffprobe 或宿主等效媒体检查能力时核对音轨，并实际回听；工具不可用或无法播放时，明确报告相关检查未完成，不伪造已检查结果。无音轨、全静音或漏台词时报告未通过，不凭任务成功或开关 true 宣称声音合格。检查不自动授权付费重投。generate_audio 控制音频，字幕仍按独立后期计划处理。

## 用户操作

- 缺少 CLI 或版本过旧：引导修复/更新连接器，使用 WorkBuddy 托管的 Node 与固定 CLI 版本；不自行安装 @latest 或写死托管 bin 目录。
- 用户明确要求断开：说明终端和 WorkBuddy 共用当前登录态后，可按下面命令注销；远端未确认时如实报告。

~~~bash
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli auth logout
~~~

- 旧连接器 baomihua-aigc 需要先通过宿主受支持的入口停用并重载旧 Skill/会话，避免它继续自动绑定 Key；不要读取或删除旧凭证。
- 不自动切换服务地址。用户主动切换地址会使共享当前态失效，应说明影响。
- 不读凭证文件、不回显密码、Key、access/refresh、pcd1 或含 pcv1 的完整链接；授权失败材料须先脱敏。宿主原生日志可能包含短期链接，不宣称 Skill 能替宿主完成脱敏。
- 图片超过 10 张或视频超过 5 条的批量操作沿用先确认、先试产 1 个的约定；权限未确认时不提交，提交或上传响应不确定时不自动重发。


## Windows 调用约定

Windows 使用 `popcorn-cli.cmd`，参数与其他平台相同。Agent Shell 为 PowerShell 时，每次调用使用：

~~~powershell
$env:POPCORN_REQUIRED_AUTH_METHOD = 'oauth'
$env:POPCORN_OAUTH_CLIENT_ID = 'popcorn-workbuddy'
popcorn-cli.cmd auth ensure
~~~

参考文档中的 Bash 环境变量前缀不适用于 PowerShell；调用后续命令时同样在本次 Shell 中设置上述约束并使用 `.cmd` 入口。宿主负责发起浏览器授权，Agent 不额外启动登录。凭证 ACL 无法验证时报告存储错误，不以绑定 Key 或放宽权限继续。
