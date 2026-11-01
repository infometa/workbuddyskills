# 命令契约

可执行名 `superun-ai`；使用宿主提供的实际路径，具体参数以当前命令帮助和返回结果为准。

业务 stdout 为最终单条 JSON；stderr 包含普通日志及 task_progress、conversation_message、task_reminder JSON 事件，必须分开处理，不用 2>&1 合并成单条结果解析。下表提供业务命令；长任务通过下面的运行脚本执行，CLI 默认连接 `superun.com`，不额外添加服务器地址。`nextActions.command` 用于识别业务子命令、会话/交互/候选标识及必要业务参数，不整条照抄其中的服务器地址配置；测试环境仅在用户明确要求时使用。补齐输入并核对实际授权后执行。

## 长任务的默认启动方式

使用本 Skill 自带的 [run-cli.mjs](../scripts/run-cli.mjs) 启动一次 CLI。根据上方链接解析脚本的绝对路径，为每次调用选择一个尚不存在的输出目录：由宿主临时目录、本次命令名和时间戳（或随机串）拼成新目录，如 `<宿主临时目录>/superun-chat-create-<时间戳>`。不要用固定名或递增序号——目录已存在时脚本会直接拒绝，上一次的输出目录不能复用。

```text
node "<run-cli.mjs 的绝对路径>" --out-dir "<宿主临时目录>/superun-chat-create-<时间戳>" -- superun-ai chat create --input <输入文件> --timeout 600
```

其他命令只替换 `--` 后面的可执行文件和参数，不改变 CLI 业务含义。宿主若需通过 Node 调用 CLI，可传 `-- node <CLI入口路径> <业务参数>`。不使用 shell 字符串拼接参数。

包装器的 `--` 与 CLI 命令内的 `--` 是两层分隔符。基于 `nextActions.command` 参数数组补充 `--timeout`、`--input` 等选项时，插在 CLI 自身的 `--` 之前；没有该分隔符时按命令帮助添加。保留原位置参数及其顺序，不把选项追加到 CLI 的 `--` 后。例如：

```text
node "<run-cli.mjs 的绝对路径>" --out-dir "<本次独立输出目录>" -- superun-ai chat style append --anchor <anchor> --timeout 600 -- <sessionId>
```

脚本会把原 CLI stdout 原样传回，同时保存在 stdout.json；关闭前文件名为 stdout.partial。exit.json 记录退出码和信号，stderr.log 保存原诊断，progress.ndjson 只保存有变化的进度。脚本不负责查询、重试或展示 UI；宿主仍须读取原任务结果并处理问卷。不要轮询日志来触发模型。

脚本比较任务标题、状态、steps/stepProgress、步骤顺序和 warnings；仅 revision、时间、工具次数或格式变化不重复输出。第一次进度照常输出；问卷与最终 JSON 不经过进度过滤。启动脚本失败时报告原因；已产生业务回执就按固定循环恢复，不重复执行原写命令。

后台调用的工具参数由渠道注入；当前应用的调用方式见 [后台执行示例](background-execution.md)。

## 业务命令表

| 意图 | 命令与关键约束 |
|---|---|
| 发布后高级设计师 | `chat design <sessionId> --input <file> --timeout 600`；也可用互斥的 --message，参考附件重复传 --file；要求不能为空，支持 --no-wait。仅用于用户明确选择发布后的高级设计师，调整页面或重新设计均走本命令；不是风格选择阶段的高级设计师或「再来一版」。先读 [扩展能力](extend.md#发布后高级设计师调整页面或重新设计) |
| 查看凭据 | `superun-ai auth status`；只看本地配置，CONFIGURED 不证明 PAT 有效或项目权限正常 |
| 登录 | `auth login` 复用已有 PAT，否则走网页登录；`auth login --pat` 是隐藏输入开关，不携带值；自动化安全输入使用 `auth login --stdin`，无 PAT 时不会自动打开浏览器 |
| 找项目 | `session list --limit 20 --scope all`；支持 keyword、cursor-updated-at、id-lt，scope 可为 all/mine/team/shared |
| 查看项目 | `session get <sessionId>`；需附件清单才加 `--include-attachments` |
| 新建 | `chat create --input <file> --timeout 600`；也可使用互斥的 `--message <text>`；本地附件重复传 `--file <path>`，交给 CLI 上传和审核。仅高级设计专家的新建流程追加 `--skip-question --advanced`：跳过初始需求问卷并委托高级设计师生成方案；费用以 CLI 实际回执为准；`--advanced` 须与 `--skip-question` 配合，其他创作入口不默认使用 |
| 修改/继续 | `chat send <sessionId> --input <file> --timeout 600`；本轮相关的本地附件重复传 `--file <path>`；不能用普通消息代替交互回复或进入研发 |
| 运营查询/操作 | 同上使用 `chat send`，content 保留用户原话；数据库访问由 superun 执行，先读 [运营](operations.md)；复用 wait/reply，不新增数据库命令 |
| 自动测试 | `chat test <sessionId> --timeout 600`；默认测试刚完成的功能，指定范围用互斥 --input/--message，可用 --file 附带文件；发现确认问题后告知并自动修复，先读 [质量检查](quality-checks.md) |
| 代码审查 | `chat review <sessionId> --timeout 600`；默认审查刚改动的代码，输入和等待同 test，告知问题后自动修复 |
| 报告后续修复 | `chat send <sessionId> --test-followup <sourceMessageId> --input <file>` 或 `--review-followup <sourceMessageId>`，两者互斥；加本渠道 timeout，来源取当前报告；新需求不带 followup |
| 当前状态 | `chat state <sessionId> --message-id <messageId>`；可选 --progress-revision；message-id 仅刷新快照，结果仍按当前轮解释；可重复 `--include-file <name>` 读取可见附件正文 |
| 有限等待 | `chat wait <sessionId> --message-id <messageId> --timeout 600`；可带 --progress-revision；不传 timeout 会持续等待，用宿主持续进程承载，避免每次进度更新重启命令 |
| 回答 | `chat interaction reply <sessionId> <interactionId> --input <file> --timeout 600` |
| 跳过 | `chat interaction skip <sessionId> <interactionId> --timeout 600`；仅 actions 允许 SKIP 且用户决定跳过时执行 |
| 生成风格 | `chat style generate <sessionId> --content <text> --count 2 --timeout 600`；1～4 个，默认 2；PRD 回复已经触发生成时不要再调用 |
| 查看风格 | `chat style list <sessionId> --anchor <preReplyMessageId>`；anchor 可省略，可带 --progress-revision；返回可能含多批次，历史 anchor 的 nextActions 为空 |
| 选择风格 | `chat style select <sessionId> <choiceId> --timeout 600`；只选成功无 errorType 的候选，CLI 随后自动衔接演示并生成研发规划；由 CLI 静默确认规划，直接返回功能清单；不代选功能；无 retry |
| 查看演示 | `chat demo <sessionId>`；会写查看记录，必要时发起查看轮并等待，无 --no-wait/--timeout；执行工具被中断后先 state |
| 开始研发 | `chat develop <sessionId> --timeout 600`；用于独立/旧演示路径；选风格后 stylePlanning 由 CLI 自动推进，不额外调用 develop；已进入研发不能重复执行 |
| 插件 | `chat plugin list <sessionId>`；`chat plugin status/enable/disable <sessionId> <pluginId>`；enable 支持 --input 配置，enable/disable 支持 --timeout 600；归属交互的插件优先走 interaction reply |
| 发布信息 | `chat publish status <sessionId>`；明确要求上线运营时加 `--for-launch`（仍只读），普通查询不加；返回 publish.versions 中真实 encryptedId、deployStatus、updatedAt，以及 publish.publishUrl 和发布完成后的 publish.routing 全部端入口 |
| 发布目标 | `chat publish start <sessionId> <encryptedId> --timeout 600`；上线运营时沿用 `--for-launch`，可选 --region CN/INTL、--indexing allow/deny、--acknowledge-cloud-fee，均须匹配实际要求和费用授权 |
| 发布回读 | `chat publish status <sessionId> --version-id <encryptedId>`；已授权上线链路沿用 --for-launch；按本次目标版本回读，不拿旧成功记录替代 |
| 上线/下线 | `chat publish visibility <sessionId> public/private`；public 要求已有成功部署；与索引策略分开，start 没有 --visibility |
| Agent 友好接入 | `chat agent-friendly <sessionId>`；仅本次版本已部署成功且站点已公开后使用。不加参数触发生成，`--status` 只读或等待已有任务，`--method skill/connector` 只展示所选方式原文，`--no-wait` 受理后返回；可带本渠道 timeout，详细场景见 [扩展能力](extend.md) |
| 安全扫描 | `chat security <sessionId> --timeout 600`；默认全部可用检查项，指定范围用可重复的 `--check`，报告失败用 `--retry-report <reviewId>`；不展示费用和耗时 |
| 停止远端 | `chat stop <sessionId> --scope own`；可选 --message-id，scope 可为 own/all；COMPLETED 只表示停止命令已返回 |

表中缩写 `status/enable/disable` 等表示分别存在的子命令，不是可以原样执行的名字。style、interaction、plugin、publish 都在 chat 下，stop 也在 chat 下，没有对应顶层入口。

## JSON 消息输入

`--input -` 读取 stdin。create/send/test/review 的 JSON 只接受 content 或 message 文本字段，两者二选一；本地文件使用可重复的 `--file <path>`。`--input` 只读取请求 JSON，不会上传该文件。

```json
{"content":"完整需求正文；参考随 --file 上传的素材"}
```

不向 JSON 写入 attachments、文件正文或 Base64 附件、附件 URL；这些输入会被拒绝。CLI 将 --file 指定的文件上传并审核，必要时按 Glow 预处理，再以 URL 和解析元数据提交给 Agent。Markdown/TXT 同样走上传，不能恢复旧版内联附件写法。用户给出的素材没有本地可读文件时先取得文件或说明缺口，不能只传路径并声称已上传。不读取 internal/compiled、.env 或 CLI 凭据文件作为输入素材。

每条消息最多 10 个文件，其中 PDF 最多 5 个。当前主站：图片 png/jpg/jpeg/webp/gif 为 20MB；文本及代码 txt/md/svg/js/ts/jsx/tsx/py/java/cpp/c/h/cs/php/rb/go/rs/swift/html/css/scss/less/json/xml/yaml/yml 为 5MB；pdf/docx 为 50MB；xlsx/xls 为 30MB、csv 为 5MB；视频 mp4/mov/webm/avi/wmv/flv/mkv、音频 mp3/wav/ogg/flac/m4a/aac 和 zip/rar 为 15MB。实际允许格式和大小由 CLI 读取当前环境配置。视频须能读取时长且不超过 5 分钟（含 2 秒容差）；图片尺寸、PDF 页数和文档解析限制也由 CLI 检查。任何文件失败都会停止整条消息，不自行忽略附件重发。

## 等待和认证的特殊点

支持等待的写命令优先使用 --timeout 600（按宿主工具时限调整），在同一次调用内利用 CLI 的新轮次回读校验。仅在必须立即返回时使用 --no-wait，并保留写回执；后续 wait 的 message-id 只是等待起点，不能独自证明新轮已出现。插件交互的前台配置等待不因 --no-wait 而取消。chat demo 不支持 --timeout/--no-wait。

`auth logout` 只删除本地 PAT，不撤销服务端 PAT；若进程仍有 SUPERUN_PAT，不声称所有认证来源已清除。发行版本门禁与当前源码包开发入口不同，交给 CLI 处理，不自行添加跳过门禁参数。

需要账号授权时读取 [认证与只读访问](authentication.md)；可执行环境由宿主提供。

长命令通过宿主持续进程/异步句柄接收进度，不把 600 秒设置成一次无法响应的阻塞工具调用。部分风格就绪时会提前返回 RUNNING，先打开新就绪的预览页面，再按 [等待规则](state-and-recovery.md)低频补查。
