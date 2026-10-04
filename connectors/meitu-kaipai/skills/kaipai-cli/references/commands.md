# 命令与参数

适用于本 Skill 说明的 CLI `0.1.2` 命令接口。使用 `kaipai --help` 查看命令目录，使用 `kaipai <command> --help` 查看参数；工具使用 `kaipai tool <工具名> --help`。Windows 将 `kaipai` 替换为 `kaipai.cmd`。

以下示例中的文件、URL、会话、Task 和媒体 ID 都是占位示例，执行时使用真实值。未特别说明时，可选字符串参数省略即不传；布尔开关省略即不启用。

## 通用参数

| 参数 | 类型 | 必填 / 默认值 | 适用命令与约束 |
|---|---|---|---|
| `-r, --room-id <id>` | 非空字符串 | 见各命令 | Viva 会话 ID；与 `--session-id <id>` 等价，两者同时提供必须相同 |
| `--lang <lang>` | 字符串 | 否；`zh-Hans` | `chat / reply / tool / history-detail` 的客户端语言 |
| `--detach` | 布尔开关 | 否；默认等待 | `chat / reply / tool`：收到受理事件后退出，远端继续运行；若直接返回结果也可分离退出 |
| `--image-file <path...>` | 本地路径数组 | 按输入要求 | 图片附件 |
| `--image-url <url...>` | URL 数组 | 按输入要求 | 图片附件 |
| `--video-file <path...>` | 本地路径数组 | 按输入要求 | 视频附件 |
| `--video-url <url...>` | URL 数组 | 按输入要求 | 视频附件 |

四种附件参数用于 `chat / add-media`，合计最多 10 个。图片工具仅有图片参数，视频工具仅有视频参数，固定工具合计必须恰好一个源媒体。带 `<...>` 的数组参数可在同一参数后传多个独立值，例如 `--image-file './a.png' './b.png'`；不是逗号拼接字符串。

## 媒体限制

| 媒体 | 支持格式 | 本地文件上限 |
|---|---|---|
| 图片 | jpg / jpeg / png / webp | 20 MB；最长边 4096 px |
| 视频 | mp4 / mov / m4v / 3gp / avi | 1024 MB；20 分钟；短边 2160 px、长边 4096 px |

- 本地视频元信息校验需要可用的 `ffprobe`；连接器托管 Node.js 不代表已安装 `ffprobe`。缺失时说明实际依赖错误；可以使用用户已有的有效视频 URL，不擅自上传到其他服务或跳过校验。
- URL 必须是 HTTP(S)。路径有扩展名时必须匹配媒体格式；无扩展名的 URL 可通过本地格式检查。URL 不会在本地完整下载测量大小、时长或尺寸，仍需真实可访问且符合服务端要求，不能借 URL 绕过媒体限制。
- CLI 在上传前校验整个附件批次。本地文件由 CLI 上传；普通聊天的会话内附件由 CLI 自动登记。仅把外部 URL 写入 prompt 不等于添加媒体附件。
- 不支持独立音频、文档附件或通用 `--file` 参数。不要从产品介绍推导未提供的 CLI 参数。

## 登录与账号

| 命令 | 参数、默认值与行为 | 返回 |
|---|---|---|
| `auth login` | `--timeout <seconds>`：数值，默认 `285`，范围 `1–285` 秒；`--no-open`：默认会打开浏览器，启用后仅打印授权链接但继续等待 | 先打印实际 HTTPS 授权 URL，成功后打印 `connected`；成功 `0`，失败或超时非零 |
| `auth status` | 无必填参数；只检查本地凭证是否存在。可加 `--check` 远端校验，不修改登录态 | `connected` / `disconnected`；退出码分别为 `0` / `1` |
| `auth logout` | 无参数；清除本地登录数据，仅用于用户要求断开连接 | 打印 `disconnected`，成功退出码 `0` |
| `user-info` | 无参数；需登录，查询当前账号信息并补全本地用户 ID | 服务端账号 JSON；字段以实际响应为准 |

连接器已设置 `authWaitForExit: true`，使登录进程继续轮询并保存授权结果。所有业务步骤沿用原有登录环境；账号信息仅在用户需要或诊断所必需时查询。

## 创作对话与会话媒体

### `chat`

| 参数 | 类型 | 必填 / 默认值 | 约束 |
|---|---|---|---|
| `-p, --prompt <text>` | 字符串 | 与附件至少提供一项 | 没有附件时需非空文本 |
| `-r / --session-id` | 会话 ID | 否；默认新会话 | 续聊必须传实际会话 ID |
| 四种附件参数 | 路径 / URL 数组 | 否 | 合计最多 10 个 |
| `--silence <0\|1>` | 枚举整数 | 否；默认不传 | 服务端 silence 标记；不会关闭 CLI 的进度和结果输出，仅 `chat` 支持 |
| `--lang / --detach` | 见通用参数 | 否 | 默认语言 `zh-Hans`，默认等待本次任务 |

```bash
kaipai chat -p '根据这段素材做一版竖屏口播视频，增加字幕。' --video-file './source.mp4'
kaipai chat -r '<session_id>' -p '开头更简洁，保留产品介绍。'
kaipai chat -p '根据这张产品图构思宣传视频。' --image-file './product.png' --detach
```

返回会话、执行结果或交互消息，有 Task 时默认跟进任务。准确结构见 [输出与任务恢复](results-and-recovery.md)。不要给 `chat` 传任意 `--action` 或旧卡片字段。

### `create-room` 与 `add-media`

`create-room` 无参数，用于明确需要先创建空会话的场景，返回 `type=session` 及 `session_id / room_id / room_url`。

`add-media` 必须提供 `-r`（或 `--session-id`）和至少一个图片/视频附件，合计最多 10 个；无 `--prompt / --lang / --detach`。它只上传并登记素材，不提交创作任务。每成功一项输出 `type=media`、会话信息、`item_id / kind / url`；中途失败时保留已输出成功项，不盲目重传整个批次。

```bash
kaipai create-room
kaipai add-media -r '<返回的 session_id>' --image-file './product.png'
```

只有需要预先取得媒体 ID 等场景才单独登记，普通 `chat / tool` 直接接收文件或 URL。

## 固定媒体工具 `tool <工具名>`

| 工具名 | 输入类型 | 用途 |
|---|---|---|
| `image-repair` | 图片 | 图片画质修复 |
| `video-repair` | 视频 | 视频画质修复 |
| `image-remove-text` | 图片 | 自动消除图片文字，包括文字水印 |
| `video-remove-auto` | 视频 | 自动视频全量消除 |
| `video-remove-subtitle` | 视频 | 消除视频字幕 |
| `video-remove-watermark` | 视频 | 消除视频水印 |

每次恰好选择一种输入：

- **一个文件或 URL**：提供匹配工具类型的附件参数，`-r` 可选，省略时新建会话。
- **一个已有源媒体 ID**：`--item-id <id>` 为非空字符串，此时 `-r / --session-id` 必填，与全部附件参数互斥。ID 必须真实、属于该会话，且已知是匹配工具类型的源媒体；服务端验证实际媒体类型、归属与状态。不要用失败结果媒体 ID 替代源 ID。

另支持 `--lang / --detach`，默认同通用参数。工具不接受 `--prompt / --silence / --action / --mode` 或额外算法参数。

```bash
kaipai tool image-repair --image-file './photo.png'
kaipai tool video-repair --video-file './source.mp4'
kaipai tool image-remove-text --image-url 'https://cdn.example.com/source.png'
kaipai tool video-remove-auto --video-url 'https://cdn.example.com/source.mp4'
kaipai tool video-remove-subtitle --video-file './source.mp4' --detach
kaipai tool video-remove-watermark -r '<session_id>' --item-id '<source_item_id>'
```

CLI 负责工具协议和本地上传，无需手动构造 action、媒体引用或占位文本。返回与 `chat` 相同的执行/任务结构；本地命令可用不代表远端环境已经支持该工具，失败时保留真实错误。

## 历史与任务查询

| 命令 | 参数 | 返回与等待方式 |
|---|---|---|
| `history` | `--cursor <cursor>`：可选字符串，取上一页返回值；`--limit <n>`：正安全整数，默认 `10` | JSON `list / total_count / next_cursor / has_more`；`total_count` 是本页条数 |
| `history-detail` | 会话 ID 必填；`--last-event-id <n>`：非负安全整数，默认 `0`，别名 `--after-seq`，同时提供必须一致；`--watch`：默认关闭；`--yield-on-update`：默认关闭且必须配合 `--watch`；另有 `--lang` | 默认一次快照；watch 持续查询历史和所观察任务；yield 在实际内容或状态更新后退出。输出 `session / history / task / end` |
| `task-progress` | 会话 ID 必填；`--task-id <id...>`：至少一个真实 Task ID，必填，自动去重；`--watch`：默认关闭 | 默认查询一轮；watch 等待指定任务全部终结；输出 `session / task / end`，包括当前产物 URL |

```bash
kaipai history --limit 10
kaipai history --cursor '<next_cursor>' --limit 10
kaipai history-detail -r '<session_id>'
kaipai history-detail -r '<session_id>' --watch --yield-on-update --last-event-id 42
kaipai task-progress -r '<session_id>' --task-id '<task_1>' '<task_2>' --watch
```

`--last-event-id` 是服务端事件游标，不是历史数组索引。`task-progress` 不接受 Run ID，也没有 `--lang` 或历史游标。watch 默认每 2 秒查询，未提供自定义 `--interval` 参数。

## 交互回复与取消

`reply` 必须指定会话 ID，且以下三项恰好选择一项：

| 参数 | 类型 | 用途 |
|---|---|---|
| `--answer <json>` | JSON 对象字符串 | 当前结构化澄清的原生答案，字段和选项取自当前实际交互，不接受数组或纯字符串 |
| `--approve` | 布尔开关 | 批准当前待处理动作，需要用户对该动作的授权 |
| `--reject` | 布尔开关 | 拒绝当前待处理动作 |

可选 `--reason <text>` 只能和 `--reject` 同用，提供时不能为空。另支持 `--lang / --detach`。它恢复会话当前交互，不能指定旧卡片或中断 ID；普通文本“同意”不会自动转为批准。

```bash
kaipai history-detail -r '<session_id>'
# 仅当实际交互提供 aspect_ratio 字段及对应选项时使用以下答案
kaipai reply -r '<session_id>' --answer '{"aspect_ratio":"9:16"}'
kaipai reply -r '<session_id>' --approve
kaipai reply -r '<session_id>' --reject --reason '请先调整预算'
```

以上三个 reply 示例是互斥选择，不依次执行。普通文本追问使用同一会话的 `chat -p`。答案需要已登记素材时先取得真实媒体 ID；CLI 会在包含媒体 ID 的答案对象中去除同对象的预览 URL。

`cancel -r '<session_id>'` 显式取消该会话当前远端执行，无 Task ID 参数。仅在用户明确要求取消时调用，成功返回 `type=end, reason=cancelled`，退出码 `0`；之后查询状态。停止本地等待或 Ctrl+C 只会断开本地观察。

## 下载、购买与反馈

| 命令 | 参数、默认值 | 返回与副作用 |
|---|---|---|
| `download` | `--url <url...>`：HTTP(S) URL 数组，至少一个，必填；`-o, --output-dir <dir>`：字符串，默认当前目录 `.` | 写入本地文件；返回 `total / succeeded / failed / output_dir / downloaded`；不要求登录，不向产物域名发送开拍凭证 |
| `purchase` | 可选布尔开关 `--open`，默认只返回链接 | `{event:"purchase", action_url, action_command}`；`--open` 同时打开浏览器，不检测付款；不要求登录 |
| `feedback` | 无参数；当前 CLI 需登录 | `{event:"feedback", contact_url, link_text, markdown_link}`；实际仅返回客户反馈入口，不自动发送反馈内容 |

```bash
kaipai download --url '<实际产物 URL>' -o './output'
kaipai purchase --open
kaipai feedback
```

下载文件按 `01_`、`02_` 等序号加 URL 文件名保存，并清理非法文件名字符。最终位置以 `downloaded[].file` 的绝对路径为准；相同目标文件名可能被覆盖，应选择合适的输出目录。部分失败时仍处理其他 URL 并返回非零退出码，逐项检查 `downloaded[].error`。下载 URL 失效时先用 `task-progress` 刷新，不重做生成。

## 配置诊断

常规业务无需修改配置。排查当前环境用 `config list`，返回脱敏配置及 `env / env_source / client_name / client_name_source` 等字段，不读取原始凭证文件。

仅在用户明确要求配置变更时使用：

- `config business <business>`：必填字符串，目前仅接受 `kaipai`。
- `config env <environment>`：必填枚举 `pre / beta / release`，保存兜底环境；运行时 `KAIPAI_ENV` 和构建目标优先，查看返回的 `effective_env / env_source` 确认实际生效值。不要为绕过业务错误切换环境。
- `config access-token`（别名 `access_token`）是旧的凭证参数入口；本连接器使用浏览器授权，不将 Token 写入命令、Skill 或日志。

没有通用 `resume / subscribe` 命令，也不支持旧 A2UI 的 `--card-id / --action / --interrupt-id / --skip`。续交互用 `reply`，续观察用 `history-detail / task-progress`。
