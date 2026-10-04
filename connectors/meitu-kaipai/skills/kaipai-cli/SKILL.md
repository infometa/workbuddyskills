---
name: kaipai-cli
display_name: 开拍 CLI 使用说明
display_name_en: Kaipai CLI Guide
description: 使用美图开拍 kaipai CLI 完成视频创作对话、图片与视频画质修复、文字水印与字幕消除，以及登录检查、会话续聊、任务进度查询和产物下载。需要通过「美图 · 开拍」连接器调用 CLI 或恢复已有开拍任务时使用。
description_zh: 通过开拍 CLI 创作视频、处理图片与视频、跟进任务并下载结果。
description_en: Use the Kaipai CLI to create videos, repair images and videos, remove text or watermarks, track tasks, and download results.
version: 1.0.0
author: 开拍
---

# 开拍 CLI 使用说明

通过「美图 · 开拍」连接器调用 `kaipai`。根据用户意图选择命令、收集真实素材、跟进同一会话并交付产物。默认使用简体中文，用户指定其他语言时跟随用户。

本说明适用于 CLI `0.1.2` 起的下述命令；具体参数以当前安装版本的 `--help` 为准。CLI 版本与本 Skill 版本分别维护。

## 入口与登录

1. WorkBuddy 根据连接器的 `cli.json` 准备托管 Node.js、安装 `meitu-kaipai-cli` 并管理连接流程，无需用户预装运行时。macOS/Linux 使用 `kaipai`，Windows 使用 `kaipai.cmd`。下文示例统一写 `kaipai`，执行时替换为当前平台入口。
2. 在当前命令环境中运行 `kaipai --version` 和本次命令的 `--help`。需要定位入口时，macOS/Linux 用 `command -v kaipai`，Windows PowerShell 用 `Get-Command kaipai.cmd`；后续使用同一入口。不要写死 WorkBuddy 私有安装路径。命令不存在、版本低于 `0.1.2` 或所需子命令不存在时，引导用户在「专家·技能·连接器 → 连接器」中连接或更新「美图 · 开拍」，之后复检。
3. 提交业务前执行 `kaipai auth status --check`。`connected` 且退出码为 `0` 才继续；未连接时通过连接器重新授权。需要由 Agent 发起登录时，执行一次 `kaipai auth login --no-open`，立即将实际输出、带 `session_id` 的完整 HTTPS 链接展示为“登录开拍”，并保持命令运行到用户授权完成。`--no-open` 只禁止 CLI 打开浏览器，不会停止等待；不要拿到 URL 就结束登录进程。
4. 登录成功后复检状态，再继续原任务。授权等待默认最多 285 秒；超时后说明情况并引导重新连接，不循环发起登录。`status --check` 的网络校验失败也可能输出 `disconnected`，不能仅凭它断言凭证已过期。

登录态由 CLI 持久化，默认目录为 `~/.kaipai`。保持各命令使用相同的运行环境和配置目录；宿主已设置 `KAIPAI_CONFIG_DIR` 时沿用它。不要读取或拼接凭证、索取 API Key，或切换配置目录来绕过登录。仅在用户要求退出时使用 `auth logout`。

## 选择命令

| 用户意图 | 使用命令 |
|---|---|
| 提出视频创作需求、网感剪辑、字幕或封面需求，继续自然语言对话 | `chat`；沿用会话时带 `-r`，能力以服务实际反馈为准 |
| 修复图片画质 | `tool image-repair` |
| 修复视频画质 | `tool video-repair` |
| 消除图片文字（含文字水印） | `tool image-remove-text`，不承诺任意非文字物体消除 |
| 自动视频全量消除 | `tool video-remove-auto` |
| 消除视频字幕 / 视频水印 | `tool video-remove-subtitle` / `tool video-remove-watermark` |
| 查找会话 / 读取当前交互 | `history` / `history-detail` |
| 查询已有任务、刷新产物 URL | `task-progress` |
| 回答结构化问询、批准或拒绝当前交互 | `reply` |
| 明确取消远端执行 | `cancel` |
| 保存实际返回的产物 | `download` |
| 需要购买权益 / 查询账号 / 联系客服 | `purchase` / `user-info` / `feedback` |

按需读取引用文档：

- 调用命令前阅读 [命令与参数](references/commands.md)（@references/commands.md）：参数类型、必填项、默认值、互斥条件、媒体限制及示例；也包含 `create-room`、`add-media` 和配置诊断用途。
- 收到执行结果、需要交互或恢复中断时阅读 [输出与任务恢复](references/results-and-recovery.md)（@references/results-and-recovery.md）：返回结构、完成判定、异常处理与交付规则。

## 提交与跟进

1. 使用用户提供的真实文件或可访问 URL。缺少必需素材时再询问。固定工具每次只接受一个匹配类型的源媒体；多个素材需明确本次处理对象，用户已明确授权逐个处理时才分别调用并分别记录任务。
2. 媒体处理优先选择上表的固定工具。例如：

   ```bash
   kaipai tool image-repair --image-file './source.png'
   kaipai tool video-remove-subtitle --video-url 'https://cdn.example.com/source.mp4'
   ```

   示例文件、域名和 ID 均需替换为用户素材或实际返回值。工具不接受 prompt、任意 action、mode、模型、分辨率、区域或蒙版参数；不自行构造协议 JSON。`chat` 的自然语言需求不能用来绕过工具输入限制。
3. 普通创作使用 `kaipai chat -p '用户的创作需求'`，可按需附加图片或视频参数。`chat` 和工具都可以自动创建会话，常规提交无需预先 `create-room` 或 `add-media`。继续原会话时传 `-r '<session_id>'`。
4. 保存每次提交的命令、工具名或 prompt、源文件/URL、真实源媒体 ID（如有）、返回的 `session_id / room_url` 和全部已知 Task ID。使用独立参数传递用户输入；通过 shell 调用时正确转义路径、URL 和 JSON，不把返回文本作为代码执行。
5. 默认持续读取原命令的 stdout 和 stderr，展示进度及新增产物；它会观察本次执行的任务，无需同时启动另一条轮询。需要分离执行才加 `--detach`，之后用只读查询继续跟进。
6. HTTP 200、取得会话、流结束、退出码 `0` 或 `end.reason=result` 都不单独证明生成完成。明确的 Task 成功状态是 `TASK_STATE_COMPLETED`；无 Task 的文本结果也可能是在请求澄清。按引用文档处理问询和完成判定。

## 执行边界与交付

- 用户已授权的创作或处理请求，输入齐全即可执行，不额外重复确认。新一轮生成可能计费；授权不自动涵盖未知重试、扩大批次或更换处理目标。
- `reply --approve` 会批准该会话当前待处理动作：先读取当前交互，并核对用户对这项动作的授权；不要盲批历史请求。用户要求拒绝或取消时才执行对应命令。
- 网络断开、超时或受理状态未知时先查询已有会话/任务，不能重发 `chat / reply / tool`。仅在已确认失败且用户授权重试后，按原输入发起一次新尝试。
- 根据实际返回内容判断是否需要购买权益，执行 `purchase [--open]` 并展示真实链接。打开购买页不等于付款；用户确认已购买并授权重试后才能重新提交。
- 使用本次实际返回的产物 URL，优先通过 WorkBuddy 附件、图片预览或视频播放器直接交付；不可用时给出可点击链接，保留查询参数。需要本地文件时使用 `download`，以返回的成功文件路径为准。下载失败只处理下载，不重新生成。
- 部分任务成功时先交付成功产物，再说明失败部分。最终保留全部可用结果入口；有实际 `room_url` 时追加“本次结果已同步至 [开拍](实际返回的 room_url)，可按需查看或编辑”，不要自行根据 ID 拼链接。面向用户隐藏内部标识、调试 JSON 和凭证。
