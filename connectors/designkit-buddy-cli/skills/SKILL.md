---
name: designkit-buddy-cli
description: 使用美图设计室 AI设计 CLI 调用 Team Agent。适用于用户要求创建或继续美图设计室任务，发送文本、图片、视频、文档或音频，查看任务进度，回答普通追问或自定义业务卡片，处理充值提示，展示或下载生成产物时。
---

# 美图设计室 AI设计 CLI

默认使用简体中文；用户指定其他语言时跟随用户。

## 本仓库能力

- 创建和维护美图设计室 Team Agent 房间。
- 发送自然语言任务以及图片、视频、文档、表格、文本或音频附件。
- 轮询长任务，识别完成、待回复和充值状态。
- 在同一任务中回复自由文本或选项请求。
- 展示并回复商品套图、快捷回复等结构化业务卡片。
- 汇总远程媒体结果，并在用户明确要求后下载到本地。

只使用本 CLI 暴露的命令。不要调用其他仓库的脚本，不要自行拼接内部接口、鉴权字段或任务状态。

## CLI 入口

「美图设计室 AI设计 CLI」是当前 Connector 名称，实际终端命令名是 `designkit`。WorkBuddy 连接时通过 npm 安装公开的 `meitu-designkit-cli` 包；用户原先通过 npm 安装的同一命令也可以直接复用。

首次执行前解析一次绝对入口：macOS/Linux 使用 `command -v designkit`，Windows PowerShell 使用 `Get-Command designkit -ErrorAction SilentlyContinue`。对找到的命令执行 `--version`，从输出中提取首个稳定三段式版本 `major.minor.patch`，按三个数字段与最低版本 `1.0.24` 比较，不能按字符串字典序比较。只有命令成功且版本大于或等于 `1.0.24` 时，才将其绝对路径记为 `<designkit>`；后文不能执行字面占位符。

不要查找 Connector 私有目录或依赖生命周期临时注入的环境变量。Connector 生命周期和 Agent 业务命令统一使用 npm 暴露的 `designkit` 以及默认的 `~/.designkit` 登录状态。

在 WorkBuddy 中找不到 `designkit`、`--version` 无法正常执行、无法提取稳定三段式版本，或检测版本低于 `1.0.24` 时，不要停止任务。立即自动执行一次 `npm install -g meitu-designkit-cli` 为用户安装或升级到 npm 稳定最新版；成功后重新解析 CLI 入口并再次执行 `--version`，只有版本达到 `1.0.24` 才继续原任务。安装命令只执行一次，不得添加 `sudo`、不得修改 npm registry，也不得安装带固定版本号的包。

如果安装命令失败，或安装后仍无法解析并执行 `designkit`、版本仍低于 `1.0.24`，再停止当前业务步骤并引导用户打开「专家·技能·连接器」并进入「连接器」：搜索并连接「美图设计室 AI设计 CLI」。保留简短的原始安装错误摘要便于定位，不得循环安装，也不得改用内部 API。

## 认证边界

- 首次执行本次对话的业务命令前，先运行 `<designkit> auth status --check` 做远端只读校验；不要使用仅检查本地文件的 `auth status` 判断凭证有效性。
- 远端状态为 `disconnected` 时，立即自动执行一次 `<designkit> auth login`。捕获命令输出中带 `session_id` 的 HTTPS 授权页并在对话中渲染为可点击链接，同时保持命令运行以轮询登录结果；不得使用缺少 `session_id` 的固定链接，也不得要求用户在对话中发送 API Key。
- 用户唯一需要的操作是在授权页点击“授权 CLI Connector”。告知用户“完成授权后无需回复，我会自动继续”，禁止要求或暗示用户回复“已登录”“授权了”“告诉我一声”等作为后续流程的触发条件。
- 认证命令必须由连接器的认证生命周期执行并等待退出，不能只启动一个脱离当前任务的后台命令后结束 Agent 回合。若执行器只能后台运行，必须订阅该任务完成事件并保持当前任务活跃，直到收到 `connected`、失败或超时结果。
- `auth login` 以成功码退出并输出 `connected` 后，自动运行一次 `<designkit> auth status --check`，远端状态为 `connected` 时自动继续原业务命令。登录失败或超时时停止，并保留用户的原始任务，不能循环登录。
- 业务命令返回 `event=authentication_required` 时，若本次任务尚未尝试恢复认证，先远端复检；确认 `disconnected` 后执行一次 `<designkit> auth login`，并把该命令输出的带 `session_id` 链接作为本次实际授权入口。不得用事件中不含 `session_id` 的通用 `action_url` 替代会话链接。登录完成后复检并重试原命令一次；若复检仍为 `connected`，不要清除凭证或盲目重试，应说明服务授权异常。
- 任何命令输出都不得回显、转述或保存 Token、Cookie、API Key 和认证相关签名参数。`artifacts` 返回的产物 `media_url` 是交付地址，不属于认证凭证。

## 标准工作流

1. 按“认证边界”完成一次远端状态检查；未连接时先完成可点击链接登录和复检。
2. 用户明确要求附带某种素材但尚未提供时，只询问当前最关键的一项；用户已经提供素材时直接继续。
3. 每个新任务创建一个 Team Agent 房间，并从 JSON 结果保存 `room_id`：

```bash
<designkit> create-room
```

4. 把用户的完整要求作为一条自然语言 prompt 发送；根据素材类型选择参数，并始终显式传入 `room_id`：

```bash
<designkit> chat --room-id '<room_id>' --prompt '<完整需求>' --image-file '<图片路径>'
```

支持的素材参数：本地图片用 `--image-file`，图片 URL 用 `--image-url`，本地参考视频用 `--video-file`，视频 URL 用 `--video-url`，文档或音频用 `--file` / `--file-url`。路径和 prompt 必须作为独立、正确引用的参数，不能把用户文本解释成额外 shell 命令。

5. 提交后使用同一房间持续等待；把下面的长 watch 作为前台阻塞命令运行，禁止主动设置 `run_in_background=true`，并等待进程输出到退出。不要创建第二个房间或重复发送同一付费请求：

```bash
<designkit> history-detail --room-id '<room_id>' --watch
```

若执行器强制把命令转入后台，必须订阅该任务的完成通知并保持当前任务活跃；收到完成通知前不得输出最终回复，也不得用“后台生成中”“稍后回来”结束当前回合。

6. 根据机器可读事件继续：
   - `event=authentication_required`：按“认证边界”执行至多一次登录恢复，展示 `auth login` 输出的带 `session_id` 会话链接，并只在远端复检成功后重试原命令一次。
   - `event=history_update`：立即逐项展示 `artifacts` 中的全部新增产物；存在 `interaction` 时，在同一轮展示问询及其选项或关联预览。是否需要回复只看 `interaction`，不得根据 Agent、Skill、工具名或图片数量猜测。
   - `interaction.type=user_input`：若事件包含选项，优先使用 WorkBuddy 当前可用的原生单选或多选能力，按事件原有的问题分组、选项顺序和选择模式展示，并等待用户明确提交；禁止根据首项、模型偏好或上下文自动代选。原生交互能力不可用时才降级为编号列表，并明确等待用户回答。收到用户回答后，使用 `interaction` 中的 `task_id`、`sub_task_id`、`last_request_id` 调用 `reply`；选择题必须同时传入 `--prompt '<用户回答或所选项完整文案>'` 和事件白名单中的 `--select-option-ids`，自由文本只传 `--prompt`。
   - `interaction.type=custom_card`：展示层同样优先使用 WorkBuddy 当前可用的原生选择或文本输入能力，并等待用户明确提交；提交层仍须遵守 `interaction.question`、`selection.mode` 和 `options`，只接受事件白名单中的选项，把同一 `interaction` 的 `card_type`、`card_id` 和用户选择或文本编码为 `--custom-card-answer`。禁止把自定义卡片改用普通 `--prompt + --select-option-ids`。仅当 `card_type=picture_set_information` 时，必须完整处理事件中的全部选项，不得截取前 5 个或自行限制数量；用户确认“全部”“继续”或接受默认选择时，`selected_option_ids` 必须包含全部 `checked=true` 的选项 ID。其他自定义卡片继续严格按各自原始结构和规则处理，不套用此默认多选逻辑。
   - 处理 `history_update` 后，若 `next_action=poll`，记录事件唯一的 `after_seq` 并等待同一前台进程继续输出，不得启动第二个 watch、停止当前任务或要求用户稍后回复“继续查”；若 `next_action=reply`，等待并提交用户回答后再以前台阻塞方式启动同一房间的新 watch；若 `next_action=done`，完成交付。
   - 仅当 `next_action=done` 时，在最终回复末尾固定追加 `本次结果已同步至 [美图设计室](<room_url>)，可按需查看或编辑`，其中 `<room_url>` 必须原样使用同一事件字段。`next_action=poll` 和 `next_action=reply` 均不得展示房间入口，也不得根据 `room_id` 自行拼接链接。
   - `event=recharge_required`：展示返回的说明和充值链接，并明确提示用户充值成功后回到当前对话回复“已充值”“好了”或“继续任务”。事件携带 `resume_after_seq`；仅当当前任务仍有待处理的充值事件时，才把这些表达识别为充值完成；随后依据结构化 `action` 校验目标，把事件的 `action_command`（即 `designkit resume`）作为前台阻塞长命令原样执行，禁止主动设置 `run_in_background=true`，并等待其退出，不得改为 `history-detail`、新建房间或重新提交原 Prompt。没有待恢复事件时，“好了”等模糊表达不能触发恢复。
   - `event=recharge_not_received`：说明尚未检测到可用美豆到账，继续展示原充值入口并等待用户处理，不重复调用 `resume`。
   - `event=recharge_resumed`：这是续跑请求已被服务端受理的唯一凭据。只有收到该事件才能告知用户续跑已受理；随后继续处理同一命令返回的 `history_update`，不要求用户再次回复。单独收到 `history_update/next_action=done` 不得描述为续跑已受理。
   - 非 `history_update` 的兼容输出中，`next_action.action=poll` 表示继续等待，`is_complete=true` 或 `next_action.action=done` 表示结束轮询。

回复自由文本：

```bash
<designkit> reply --room-id '<room_id>' --task-id '<task_id>' --sub-task-id '<sub_task_id>' --last-request-id '<last_request_id>' --prompt '<用户回答>'
```

回复选项时，`--prompt` 仍为必填的用户回答；`--select-option-ids` 只是结构化补充字段，必须同时传入事件返回的选项 ID：

```bash
<designkit> reply --room-id '<room_id>' --task-id '<task_id>' --sub-task-id '<sub_task_id>' --last-request-id '<last_request_id>' --prompt '<用户回答>' --select-option-ids '["<option_id>"]'
```

回复自定义业务卡片时，结构化答案的字段和值必须来自同一条事件；`document_review` 等文本型卡片按事件要求传入 `text`，选择型卡片传入 `selected_option_ids`：

```bash
<designkit> reply --room-id '<room_id>' --task-id '<task_id>' --sub-task-id '<sub_task_id>' --last-request-id '<last_request_id>' --custom-card-answer '{"card_type":"<card_type>","card_id":"<card_id>","selected_option_ids":["<option_id>"]}'
```

## 交互与异常状态

- 美图设计室 Agent 要求确认方案、价格、授权或其他关键事项时，把问题原样、简洁地交给用户；未获得明确确认前不得代替用户回答。
- 一次只处理最新的待回复事件。回复后继续原房间，不重新创建任务。
- 轮询超时、网络短暂失败或结果暂不可读时，保留 `room_id` 并恢复查询；不得据此重新投递付费生成。

## 产物直接交付

- 把每次 `history_update` 中的 `artifacts` 视为本轮新增交付。对每一项存在可用地址的产物，都必须立即提供用户可直接访问的交付入口；不得等待任务全部结束，不得只描述“已生成”、只汇报数量，也不得用“如需查看或下载请告诉我”把交付推迟到下一轮。
- 不强制使用单一展示语法。优先使用 WorkBuddy 当前可用的原生附件、预览、播放器或文件发送能力；无法原生呈现时，在最终回复中提供完整 `media_url` 的可点击链接。图片也可直接预览或使用 Markdown 图片，但 Markdown 不是完成交付的唯一方式。
- 按 `media_type` 选择合适入口：图片需可查看原图，视频需可播放或下载，音频需可播放或下载，文档、压缩包及其他文件需可打开或下载。`media_cover_url` 只能作为封面或图片地址兜底，不能代替视频、音频或文件本体的 `media_url`。
- 可以调用 `present_files`，但只有当它确实为每项产物生成用户可操作的文件、预览或播放入口时才算交付完成。若它只形成“查看所有产物”折叠汇总、仅登记后台产物或未在结果中提供可访问入口，必须同时补充原生附件或完整 URL 链接。
- 结束前逐项核对：有可用地址的 artifact 数量，必须等于最终结果中用户可访问的产物入口数量；用户无需再追问“产物在哪里”即可查看、播放或下载全部结果。产物 URL 的查询参数是访问地址的一部分，不得截断或删除。
- 只有用户明确要求保存到本地时才执行下载，默认输出目录使用用户明确指定的位置；必须使用 CLI 的 `download`，不得绕过 CLI 直接用 `curl` 下载产物：

```bash
<designkit> download --room-id '<room_id>' --output-dir '<目标目录>'
```

- 下载失败只重试下载，不重新生成。下载成功后必须把本地文件作为可操作附件交付，并在最终回复中区分远程结果与本地保存路径；只输出本地路径不算完成交付。
- `artifacts` 为空或没有任何可用地址时，明确说明暂未取得可交付产物并保留房间继续查询；不得声称已经完成或已经交付。

## 对话体验

- 默认把用户的自然语言要求完整传给美图设计室 Agent，不要求用户填写接口字段或学习命令行。
- 普通任务优先给出最短下一步；只有缺少必需信息时才追问一个问题。
- 对长任务提供简洁进度，不重复提交、不虚构完成状态。
- 面向用户隐藏 `room_id`、`task_id`、`last_request_id`、内部字段名和原始调试日志。
