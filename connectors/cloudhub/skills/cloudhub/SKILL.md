---
name: cloudhub
display_name: 云之家
display_name_en: CloudHub
description: 云之家（CloudHub）技能：通过 yzj-cli 命令管理云之家产品能力，包括知识库文档（doc）、多维表格（sheet/aitable）、日历日程（calendar）、通讯录（contact）、IM 消息（im/chat，含文件上传）。当用户需要操作文档、多维表格、管理日程会议、查询同事信息、查询本人/当前用户信息（whoami/我是谁）、发送 IM 消息、查询 IM 历史聊天记录、查询最近群组会话、上传本地文件用于 IM 消息、导入文件到知识库时使用。
description_zh: 云之家技能：操作知识库文档、多维表格、日历日程、通讯录、IM 消息收发与文件上传下载。
description_en: "CloudHub skill: manage Yunzhijia (Kingdee) knowledge docs, AI tables (sheets), calendar events, contacts, and IM messaging with file upload via the yzj-cli command."
version: 0.6.1
author: 金蝶·云之家·Gil
---

# 云之家 CLI Skill

通过 `yzj-cli` 命令管理云之家产品能力。

## 前置条件（必读）

使用本技能前，必须先完成两步，缺一不可：

1. 安装 CLI（Node.js >= 18）：

```bash
npm install -g @yunzhijia/cli
```

安装后可执行文件名为 `yzj-cli`，用 `yzj-cli --version` 验证。

2. 登录授权（首次使用，一次即可；凭证过期后重新执行）：

```bash
yzj-cli auth login              # 桌面环境，自动打开浏览器
yzj-cli auth login --device     # SSH / CI / 无浏览器环境
```

未登录时所有命令返回 `credentials_missing`，按提示重新登录即可。

## CRITICAL 规则

- **禁止** 使用 yzj-cli 以外的方式操作（禁止 curl、HTTP API、浏览器）
- **禁止** 编造 ID、openId 等标识符——必须从命令返回中提取
- **禁止** 猜测参数值——写入/删除操作前先查询确认
- **禁止** 输出 appSecret、accessToken 等凭据明文
- **必须** 在执行危险操作前向用户展示摘要并获得明确同意
- **必须** 参数不确定时先跑 `yzj-cli <command> --help`，以其输出为准

## 意图判断

### contact

| 用户说 | 命令 |
|--------|------|
| 我是谁 / 我的信息 | `contact user get`（不传 flag 默认自身） |
| 找同事 / 搜人 / 查个人 | `contact user search --keyword "张三"` |
| 查用户详情 / 批量查 | `contact user get --open-id <OPEN_ID> [--open-id ...]` |

### im

`chat` 与 `im` 等价；示例统一使用 `im`，用户明确写 `chat` 时也可以直接执行。

| 用户说 | 命令 |
|--------|------|
| 发送纯文本 | `im message send --group-id <GROUP_ID> --msg-type text --content "..."` |
| 发私聊消息 / 给某人发消息 | 有对方 openId 用 `im message send --to-open-id <OPEN_ID> ...`；有私聊会话 groupId 用 `im message send --group-id <GROUP_ID> ...` |
| 发送文字和图片 | `im message send --group-id <GROUP_ID> --msg-type richText --content "文字 [图片]" --image <IMAGE_FILE_ID>` |
| 单独发送一张图片 | `im message send --group-id <GROUP_ID> --msg-type file --file-id <IMAGE_FILE_ID>`，不传 `--content` |
| 发送普通文件 | `im message send --group-id <GROUP_ID> --msg-type file --file-id <FILE_ID>`，不传 `--content` |
| 上传文件 / 上传本地文件 | `file upload --file <LOCAL_PATH>`（多文件：`--file a b c` 或重复 `--file`，最多 5 并发） |
| @ 指定成员 | `im message send ... --content "@姓名 ..." --at-open-id <OPEN_ID>` |
| @ 全员 | `im message send ... --content "@all ..." --at-all` |
| 回复消息 | 使用 `text` 或 `richText`：`im message send ... --reply-msg-id <MSG_ID>` |
| 获取历史聊天记录 / 看最近消息 | `im message list --group-id <GROUP_ID> --type newest --limit 20` |
| 基于消息向前/向后翻聊天记录 | `im message list --group-id <GROUP_ID> --msg-id <MSG_ID> --type old|new --limit 20` |
| 最近群组 / 最近会话 | `im group recent --limit 20 --page 1` |
| 找群 / 按群名搜群 | `im group search --keyword "群名"` |

### file

通用文件上传与下载。

| 用户说 | 命令 |
|--------|------|
| 上传文件 / 传个附件 / 上传本地文件 | `file upload --file <LOCAL_PATH>` |
| 上传多个文件 / 批量上传 | `file upload --file a.txt b.txt c.txt`（最多 5 并发，超出排队） |
| 上传并改名 | `file upload --file <LOCAL_PATH> --name <NEW_NAME>`（仅单文件可用 `--name`） |
| 下载文件 / 按 fileId 拉 | `file download --id <FILE_ID> [--output <PATH>] [--overwrite]` |

### doc

| 用户说 | 命令 |
|--------|------|
| 我有哪些知识库 / 列出知识库 | `doc workspace list` |
| 我的个人知识库 / 查询个人知识库 / 我自己的知识库 | `doc workspace list --type personal` |
| 企业知识库 / 共享知识库 / 团队知识库 | `doc workspace list --type enterprise` |
| 知识库详情 | `doc workspace get --id <KB_ID>` |
| 新建知识库 | `doc workspace create --name "..."` |
| 删除知识库 | `doc workspace delete --id <KB_ID>`（⚠️ 须先确认，会同时删除其下所有文档，见「危险操作确认」） |
| 看知识库里的文档 / 浏览子文档 / 文档列表 | `doc list --workspace <KB_ID> [--parent-id <DOC_ID>]` |
| 文档内容 / 看文档 | `doc get --id <DOC_ID>` |
| 搜索文档 / 按文档名搜索 / 按标题找文档 | `doc search --keyword <KEYWORD> [--workspace <KB_ID>] [--jq ...]`（仅匹配文档标题和文件名，不支持正文内容检索） |
| 写文档 / 新建文档 / 创建在线文档 | `doc create --workspace <KB_ID> --title "..."` |
| 新建文件夹 / 建目录 / 归类 / 分组 | `doc create --workspace <KB_ID> --title "..."`（知识库没有独立文件夹概念，建一个文档作为父文档，子文档挂在它下面即可形成层级） |
| 覆盖写入文档内容 / 替换全文 | `doc write --id <DOC_ID> --content "..." --mode overwrite` |
| 追加内容到文档末尾 | `doc write --id <DOC_ID> --content "..." --mode append` |
| 改名 / 重命名 | `doc rename --id <NODE_ID> --title "..."` |
| 移动到 / 挂到另一个文档下 | `doc move --id <NODE_ID> --target-parent-id <DOC_ID>` |
| 删除文档 / 删了它 | `doc delete --id <NODE_ID>`（⚠️ 须先确认，见「危险操作确认」） |
| 文档结构 / 块列表 | `doc block list --id <DOC_ID>` |
| 在文档里插入内容 / 追加段落 | `doc block insert --id <DOC_ID> --element '[...]'`（可选 `--parent-block-id` 指定父块，默认文档根；向新建文档插入内容前**必须先读** [doc.md](./references/doc.md) 标题去重规则） |
| 改某段内容 / 更新块 | `doc block update --id <DOC_ID> --operations '[...]'` |
| 删一段 / 删除块 | `doc block delete --id <DOC_ID> --operations '[...]'`（⚠️ 须先确认，见「危险操作确认」） |
| 整节替换 / 替换多个块 | `doc block replace --id <DOC_ID> --start <N> --end <N> --content '[...]'`（详见 [block_operation.md](./references/doc-block_operation.md)） |
| 导入文件到知识库 / 导入文档 | `doc import`（**执行前必须先读** [doc.md](./references/doc.md)） |
| 下载文件 / 下载到本地 | `doc download --id <DOC_ID>`（下载 Office/HTML 文件到本地，30 分钟有效临时地址） |
| 读 Office/HTML 文件内容（docx/xlsx/pptx 等） | `doc download --id <DOC_ID> [--output <PATH>]` → 解析文件内容 |
| 用户粘贴 `yunzhijia.com/knowledge/#/share/doc/...?docId=...` URL | 按 [doc/url-patterns.md](./references/doc-url-patterns.md) 提取 `DOC_ID` → `doc get --id <DOC_ID>` 判类型后路由（doc/sheet 共享规则） |

### sheet（多维表格，`aitable` 为别名）

> sheet 子命令的 ID 参数：`--id <DOC_ID>`（多维表格文件节点 ID，`fileSuffix=dbt`）+ `--table-id <SHEET_ID>`（数据表整数 ID，来自 `sheet get` 的 `sheets[].id`）。`sheet get` / `sheet table *` / `sheet record *` 都用 `--id`。

| 用户说 | 命令 |
|--------|------|
| 新建多维表格 / 建一张表 | `sheet create --workspace <KB_ID> --title "..."` |
| 表结构 / 有哪些字段 / schema | `sheet get --id <DOC_ID>`；加 `--lite` 只返回表名和 ID（不含字段详情），适合快速定位 table-id |
| 看某个数据表结构 | `sheet table get --id <DOC_ID> --table-id <SHEET_ID>` |
| 加一张数据表 / 新建子表 | `sheet table create --id <DOC_ID> --name "..." --fields '[...]' --views '[...]'` |
| 改数据表名字 | `sheet table rename --id <DOC_ID> --table-id <SHEET_ID> --name "..."` |
| 删数据表 | `sheet table delete --id <DOC_ID> --table-id <SHEET_ID>`（⚠️ 须先确认，见「危险操作确认」） |
| 看记录 / 列出数据 / 查记录 | `sheet record list --id <DOC_ID> --table-id <SHEET_ID>` |
| 筛选记录 / 按条件查 | `sheet record list --id <DOC_ID> --table-id <SHEET_ID> --filter '{...}'` |
| 搜记录 / 关键词查 | `sheet record list --id <DOC_ID> --table-id <SHEET_ID> --text-value "..."` |
| 新增记录 / 写一行 | `sheet record create --id <DOC_ID> --table-id <SHEET_ID> --records '[...]'` |
| 改记录 / 更新数据 | `sheet record update --id <DOC_ID> --table-id <SHEET_ID> --records '[...]'` |
| 删记录 | `sheet record delete --id <DOC_ID> --table-id <SHEET_ID> --record-ids rec_a,rec_b`（⚠️ 须先确认，见「危险操作确认」） |
| 多维表格改名 / 移动 / 删除 | 复用 `doc rename` / `doc move` / `doc delete` |

### calendar

| 用户说 | 命令 |
|--------|------|
| 今天/本周日程、看下日历 | `calendar event list --start <DATE> --end <DATE>` |
| 日程详情 | `calendar event get --id <EVENT_ID>` |
| 约个会 / 建日程 / 创建会议 | `calendar event create --title "..." --start ... --end ... --meet-organizer-open-ids <OPEN_ID>` |
| 改时间 / 改日程 | `calendar event update --id <EVENT_ID> ...` |
| 取消日程 / 删了会议 | `calendar event delete --id <EVENT_ID>`（⚠️ 须先确认，见「危险操作确认」） |
| 看参会人 / 谁来 | `calendar event participants --id <EVENT_ID>`（别名 `attendees`） |
| 找会议室 / 哪个会议室空 | `calendar room find --start ... --end ...`（别名 `search`） |

### 关键区分

- "日历" 通常指日程（event），而非日历容器本身
- "在线文档" → `doc create`（仅创建 otl 在线文档）；"多维表格" → `sheet create`（dbt）；用户说"文件夹/目录/归类"时也用 `doc create` 建一个文档作为父节点，子文档挂在它下面形成层级（知识库没有独立文件夹类型）
- "导入文件到知识库" → `doc import`：支持 md（inline 模式，直传内容）和 docx/xlsx 等格式（reference 模式，先 `file upload` 拿 fileId）；格式、限制与标题去重规则详见 [doc.md](./references/doc.md)
- "下载知识库文件" / "读取 Office 文件内容" → `doc download --id <DOC_ID> [--output <PATH>]`：直接下载 Office/HTML 文件（docx/xlsx/xls/csv/pptx/pdf/html/htm）到本地；不支持 otl/dbt/md；读取 Office 文件正文内容时需先下载到本地再解析
- 多维表格本体的列表/重命名/移动/删除复用 `doc` 命令；只有内部数据（数据表/字段/记录）走 `sheet` 子命令
- "会议室" 在 yzj-cli 当前只支持空闲查询（`calendar room find`），不支持预定/取消预定
- "聊天 / chat / IM" → `im`；`chat` 是 `im` 的别名，二者行为一致
- "上传文件" → `file upload`，返回的 `fileId` 可用于 IM 文件消息或富文本图片；下载文件用 `file download --id <FILE_ID>`
- "聊天记录" → `im message list`；`type=newest` 不需要 `--msg-id`，`type=old/new` 需要 `--msg-id`
- IM @ 消息正文里 `@all`、`@姓名` 必须是独立片段：前面是行首或空格，后面跟一个空格，再接正文，例如 `@all 请关注`、`请 @张三 处理`
- IM 发送目标必须在 `--group-id` 和 `--to-open-id` 中二选一；`--group-id` 可用于群聊或已有私聊会话，`--to-open-id` 只用于按 openId 发起私聊
- IM 消息类型用 `text`、`file`、`richText`；`text/richText` 必须传 `--content`，`file` 必须传 `--file-id` 且不支持 `--content`、`--at-all`、`--at-open-id`、`--reply-msg-id`，其他消息类型不传 `--file-id`
- IM `@` 提醒只用于 `text`、`richText` 多人群聊；只写正文不会触发提醒；正文中每个 `@姓名` 对应一个 `--at-open-id`，每个 `@all` 对应一个 `--at-all`，openId 先用通讯录搜索确认
- `--to-open-id` 表示私聊，不能同时传 `--at-all` 或 `--at-open-id`；私聊正文中的普通 `@all`、`@姓名` 文本不受此限制
- 多个 `--at-open-id` 可重复传，也可写成同一个 flag 后跟多个值：`--at-open-id id1 id2`；没有 `--at-open-ids`，也不要用逗号分隔
- 富文本图片先 `file upload`，再用返回的 `fileId` 作为 `--image`；`--image` 只能配 `--msg-type richText`
- 多张富文本图片可重复传，也可写成同一个 flag 后跟多个值：`--image file1 file2`；不要用逗号分隔

## 输出过滤（--jq / -q）

读命令（返回 JSON 的 list/get/detail/search 类）支持 `--jq <EXPR>` 过滤输出，语义同 jq CLI。`--jq` 以整个成功信封为根（get 类业务数据在 `.data` 下，list 类在 `.data.list` 下，伴随字段与 `list` 平级放 `.data` 内）：

- **取值示例**：`doc workspace list --jq '.data.list[].id'`（每行一个 ID）；`doc get --id X --jq '.data.title'`；`im group recent --jq '.data.list | length'`；`doc search --keyword K --jq '.data.total'`
- **字符串原样输出**：结果是字符串时不带引号（`"测试知识库"` → `测试知识库` 换行输出），非字符串为合法 JSON；多结果每行一个
- **支持的命令**：doc（workspace list/get、doc list/get/recent/search、block list）、sheet（get、table get、record list）、calendar（event list/get/participants、room find）、contact（user search/get）、im（message list、group recent）
- **写命令不支持**：create/update/delete/send 等传 `--jq` 会报 unknown argument
- **错误行为**：表达式语法错误 → exit 2，发起任何 API 请求前拦截；求值失败 → exit 5，stdout 干净
- 不确定 JSON 结构时，先去掉 `--jq` 看原始输出再写表达式

## 产品速查

| 产品 | 核心能力 | 详细参考 |
|------|---------|---------|
| `contact` | 搜索员工；获取用户详情 | [contact.md](./references/contact.md) |
| `im` / `chat` | 发送消息；获取历史聊天记录；获取最近群组会话；按群名搜群 | [im.md](./references/im.md) |
| `file` | 通用文件上传与下载 | [file.md](./references/file.md) |
| `doc` | 列出/创建知识库；浏览/创建/移动/重命名/删除节点；块级读写；导入文件到知识库 | [doc.md](./references/doc.md) |
| `sheet` | 创建多维表格（dbt）、获取结构（schema）、数据表（table）管理、记录（record）读写，`aitable` 为别名 | [sheet.md](./references/sheet.md) |
| `calendar` | 查询/创建/修改/删除日程；查询可用会议室 | [calendar.md](./references/calendar.md) |

## 核心工作流

```
1. 意图分类  →  判断属于哪个产品（doc / sheet / calendar / contact / im）
2. 歧义处理  →  指令模糊时先追问，不猜测
3. 查询优先  →  写入/删除前先查询确认目标存在
4. 执行      →  先读产品速查表对应的 reference 文档，按规范执行，禁止凭印象猜命令
```

### IM 组合工作流

执行 IM 相关请求时，优先按下面链路补齐 ID，不要让用户手动补所有参数：

| 场景 | CLI 链路 |
|------|----------|
| 私聊但不知道对方 openId | `contact user search --keyword "<姓名/关键词>"` → 从返回中确认目标 `oId/openId` → `im message send --to-open-id <OPEN_ID> ...` |
| 私聊已有会话 groupId | 直接用 `im message send --group-id <GROUP_ID> ...`，不需要再转成 `--to-open-id` |
| 群聊/会话但不知道 groupId | `im group recent --limit 20 --page 1` → 未命中时扩大到 `--limit 100` 并翻 `--page 1/2/3` → 从最近会话中确认 groupId → `im message send --group-id <GROUP_ID> ...` |
| 发文件消息但只有本地文件路径 | `file upload --file <PATH>` → 从返回中提取 `fileId` → `im message send --msg-type file --file-id <FILE_ID> ...` |
| 单独发送本地图片 | `file upload --file <IMAGE_PATH>` → 从返回中提取 `fileId` → `im message send --msg-type file --file-id <FILE_ID> ...` |
| 发送文字和本地图片 | `file upload --file <IMAGE_PATH>` → 从返回中提取 `fileId` → `im message send --msg-type richText --content "文字 [图片]" --image <FILE_ID> ...` |
| 回复消息但不知道 msgId | `im message list --group-id <GROUP_ID> --type newest --limit 20` → 从返回中确认 `msgId` → 使用 `text` 或 `richText` 执行 `im message send --reply-msg-id <MSG_ID> ...` |
| 查看历史消息但不知道 groupId | 先执行 `im group recent` 找会话，再执行 `im message list` |


## 高频快捷命令

```bash
# 查当前登录用户（whoami）
yzj-cli contact user get

# 搜索同事
yzj-cli contact user search --keyword "张三"

# 搜索同事并只取 openId（--jq 过滤输出；-q 为短 flag）
yzj-cli contact user search --keyword "张三" --jq '.data.list[].openId'

# 查今天日程
yzj-cli calendar event list --start 2026-01-01 --end 2026-01-01

# 列出知识库
yzj-cli doc workspace list

# 只取知识库 ID（每行一个）
yzj-cli doc workspace list --jq '.data.list[].id'

# 全文搜索文档（在指定知识库内搜索）
yzj-cli doc search --keyword "关键词" --workspace <KB_ID>

# 覆盖写入 otl 文档内容（markdown 格式）
yzj-cli doc write --id <DOC_ID> --content "# 标题\n\n正文..." --mode overwrite

# 追加内容到 otl 文档末尾
yzj-cli doc write --id <DOC_ID> --content "追加内容" --mode append

# 浏览知识库节点（找文档 / 多维表；加 --parent-id 浏览子文档）
yzj-cli doc list --workspace <KB_ID> [--parent-id <DOC_ID>]

# 创建在线文档（otl）；用户想"建文件夹/归类"时也用此命令建一个父文档
yzj-cli doc create --workspace <KB_ID> --title "在线文档"
yzj-cli doc create --workspace <KB_ID> --title "项目资料"  # 作为父文档，子文档挂在其下

# 导入 md 文件（inline 模式；注意 content 不得以与 fileName 相同的一级标题开头，否则出现重复标题）
yzj-cli doc import --workspace <KB_ID> --items '[{"fileName":"笔记.md","content":"正文内容"}]'
# 导入其他格式（docx/xlsx/pdf/pptx/html 等，reference 模式）：先上传再导入
yzj-cli file upload --file ./report.docx   # → 取 fileId
yzj-cli doc import --workspace <KB_ID> --items '[{"fileName":"report.docx","fileId":"<FILE_ID>","fileSize":204800}]'

# 获取文件临时下载地址（30 分钟有效；Office/HTML 文件）
yzj-cli doc download --id <DOC_ID>

# 创建多维表格（dbt）并取结构
yzj-cli sheet create --workspace <KB_ID> --title "跟踪表"
yzj-cli sheet get --id <DOC_ID>           # 完整 schema（含字段详情）
yzj-cli sheet get --id <DOC_ID> --lite    # 精简 schema（仅表名+ID，快速定位 table-id）

# 查询多维表记录（sheetId 来自 sheet get）
yzj-cli sheet record list --id <DOC_ID> --table-id <SHEET_ID>

# 发送 IM 文本消息
yzj-cli im message send --group-id <GROUP_ID> --msg-type text --content "CLI 测试消息"

# 获取最近聊天记录
yzj-cli im message list --group-id <GROUP_ID> --type newest --limit 20

# 获取最近群组会话
yzj-cli im group recent --limit 20 --page 1

# 上传本地文件
yzj-cli file upload --file ./demo.txt
```

## 危险操作确认

不可恢复且波及他人的命令（下表）由 CLI 代码层强制拦截。agent（非交互、无 TTY）**永远走信号路径**：exit 10「需确认」专用码 + stderr `confirmation_required` 标识，未发起任何请求——读到该信号不是失败，先向用户展示摘要并获得明确同意，同意后在命令上追加 `--yes` 重试。（真人在交互终端手动执行时 CLI 会改为终端提问；agent 不会遇到。）其他命令传 `--yes` 会报 unknown argument：

| 命令 | 说明 |
|------|------|
| `doc delete` | 删除文档节点（不可恢复） |
| `doc workspace delete` | 删除知识库及其下所有文档（不可恢复） |
| `doc block delete` | 删除文档块（不可恢复） |
| `sheet table delete` | 删除数据表及其所有记录（不可恢复） |
| `sheet record delete` | 删除记录（不可恢复） |
| `calendar event delete` | 删除/取消日程 |

### 如何识别一条命令是高风险

- `--help`：高风险命令的 Options 里会出现 `--yes`（非高风险命令没有此 flag，传入直接 exit 2 unknown argument），且命令描述带「须用户确认后带 --yes 执行」
- 上表即完整清单（代码层由 `#[meta(risk = "high")]` 注解逐命令声明，编译期校验，不存在表外的高风险命令）
- 无需预判：即使漏识别，不带 `--yes` 执行会被闸门拦下（exit 10 + `confirmation_required`，零网络请求），按信号流程补确认重试即可

确认流程：

- **用户已明确要求该操作，且目标无歧义**（如「删掉刚才建的测试文档」，目标唯一可定位）→ 无需二次询问，直接带 `--yes` 执行
- **其余情况**（目标有歧义、操作由 agent 推断发起、批量删除等）→ 展示「操作类型 + 目标名称/ID + 影响范围」→ 用户回复确认 → **带 `--yes`** 执行
- 用户未同意（或未回应）时不得加 `--yes`

另有一类影响较大但未纳入强制拦截的命令（如 `doc move`），仍按上述流程向用户确认后执行。

## 错误处理

1. 报错 → 上报完整错误，禁止自行替代
2. `errorCode 10000400 / 93001` → 引导重新运行 `yzj-cli auth login`
3. `errorCode 43001` → 提示检查应用 API 权限

## 详细参考（按需读取）

- [references/global.md](./references/global.md) — 认证、全局参数、错误码
- [references/contact.md](./references/contact.md) — 通讯录
- [references/im.md](./references/im.md) — IM 消息与聊天记录
- [references/file.md](./references/file.md) — 通用文件上传与下载
- [references/doc.md](./references/doc.md) — 知识库与文档
- [references/sheet.md](./references/sheet.md) — 多维表格（aitable 别名）
- [references/calendar.md](./references/calendar.md) — 日历与日程
- [references/file-url-patterns.md](./references/file-url-patterns.md) — file URL 识别规则（从粘贴的 URL 提取 fileId）
- [references/doc-url-patterns.md](./references/doc-url-patterns.md) — doc/sheet 分享 URL 识别规则（从粘贴的 URL 提取 docId）
