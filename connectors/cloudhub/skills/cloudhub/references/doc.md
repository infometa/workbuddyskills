# doc（知识库与文档）

## URL 识别入口

用户粘贴 `https://{host}/knowledge/#/share/doc/<shareToken>?docId=<DOC_ID>` 形式的链接时，按 [doc/url-patterns.md](./doc-url-patterns.md) 提取 `DOC_ID`，再继续下方流程。提取出的 ID 直接传给 `--id`，**禁止**把整个 URL 传给 `--id`。

## 核心概念

- **知识库（Workspace）**：文档的顶层容器，通过 `doc workspace list` 获取 `KB_ID`
- **节点（Node）**：知识库内的文档（在线文档 otl 或多维表格 dbt）；文档可作为父节点，子文档挂在它下面形成层级
- **块（Block）**：文档内的内容单元，支持块级读写

关键区分：`--workspace` 是知识库 ID（`KB_ID`），不是本地文件系统路径。

## 意图映射

| 用户说 | 命令 |
|--------|------|
| 我有哪些知识库 / 列出知识库 | `doc workspace list` |
| 我的个人知识库 / 查询个人知识库 / 我自己的知识库 | `doc workspace list --type personal` |
| 企业知识库 / 共享知识库 | `doc workspace list --type enterprise` |
| 知识库详情 | `doc workspace get --id <KB_ID>` |
| 新建知识库 | `doc workspace create --name "..."` |
| 删除知识库（不可恢复） | `doc workspace delete --id <KB_ID>`（须用户确认后带 `--yes`） |
| 看知识库里的文档 / 浏览子文档 / 文档列表 | `doc list --workspace <KB_ID> [--parent-id <DOC_ID>]` |
| 最近访问的文档 / 我最近看过什么 | `doc recent [--limit <N>]` |
| 文档内容 / 看文档 | `doc get --id <DOC_ID>` |
| 写文档 / 新建在线文档 | `doc create --workspace <KB_ID> --title "..."` |
| 新建文件夹 / 建目录 / 归类 / 分组 | `doc create --workspace <KB_ID> --title "..."`（知识库没有独立文件夹类型，建一个文档作为父节点即可） |
| 改名 / 重命名 | `doc rename --id <NODE_ID> --title "..."` |
| 移动到 / 挂到另一个文档下 | `doc move --id <NODE_ID> --target-parent-id <DOC_ID>` |
| 删除文档 / 删了它 | `doc delete --id <NODE_ID>` |
| 导入文件到知识库 / 导入文档 / 把文件传到知识库 | `doc import`（md 直接导入为在线文档；其他格式先 `file upload` 取 fileId 再导入） |
| 下载文件 / 下载到本地 | `doc download --id <DOC_ID> [--output <PATH>]` |
| 读取 Office/HTML 文件内容（docx/xlsx/pptx 等） | `doc download --id <DOC_ID> [--output <PATH>]` → 解析文件内容 |
| 文档结构 / 块列表 | `doc block list --id <DOC_ID>` |
| 在文档里插入内容 / 追加段落 | `doc block insert --id <DOC_ID> --element '[...]'` |
| 改某段内容 / 更新块 | `doc block update --id <DOC_ID> --operations '[...]'` |
| 删一段 / 删除块 | `doc block delete --id <DOC_ID> --operations '[...]'` |
| 重写某章节 / 替换多个块 | `doc block replace --id <DOC_ID> --start <N> --end <N> --content '[...]'` |

### 易混淆

| 用户说 | 用 | 不用 | 理由 |
|---|---|---|---|
| 新建在线文档 | `doc create` | `sheet create` | `doc create` 建的是 otl 在线文档（`fileSuffix=otl`）；多维表格走 `sheet create` |
| 想建文件夹 / 目录 / 归类 | `doc create`（作为父文档） | （无 `doc folder create`） | 知识库没有独立文件夹类型；建一个文档作为父节点，子文档挂在它下面形成层级 |
| 列出知识库 | `doc workspace list` | `doc list` | `workspace list` 列知识库容器；`doc list --workspace` 列知识库内的文档节点 |
| 列出我最近看过的文档 | `doc recent` | `doc list` | `doc recent` 按访问时间倒序跨所有知识库；`doc list` 列的是指定知识库的一层子节点 |
| 改文档标题 | `doc rename --id <NODE_ID>` | `doc block update` | 改节点标题（文件名）用 `doc rename`；改文档正文某段用 `doc block update` |
| 删除文档 | `doc delete --id <NODE_ID>` | （无 `doc folder delete`） | 删除节点统一走 `doc delete` |
| 导入 md 文件 | `doc import --items '[{"fileName":"*.md","content":"..."}]'`（inline 模式） | `doc create` + 手动粘贴 | `doc import` inline 模式自动解析 md 内容并转为在线文档结构；`doc create` 只建空文档 |
| 导入 docx/pdf/xlsx 等格式 | `file upload` → `doc import --items '[{"fileName":"*.docx","fileId":"...","fileSize":...}]'`（reference 模式） | 直接传本地路径 | 非 md 格式必须先上传到文件服务取得 fileId，再以 reference 模式导入 |
| 下载知识库中的 Office/HTML 文件 | `doc download --id <DOC_ID> [--output <PATH>]` | `file download --id <FILE_ID>` | `doc download` 直接下载知识库文件节点到本地；`file download` 按 fileId 下载 IM 上传的附件 |

## 核心工作流

```
查询知识库 → 获取 KB_ID → 浏览文档树 → 找到目标节点 → 执行操作 → 返回文档链接
```

**写入前必须先查**：不要猜测 KB_ID 或节点 ID，先 `doc workspace list` / `doc list` 获取。

**写入后返回链接**：创建/导入/写入内容后，拼接文档链接返回给用户（`https://www.yunzhijia.com/knowledge/lingee/#/store/doc/<DOC_ID>`，`<DOC_ID>` 取返回的节点 ID；详见本文档「文档链接返回」章节）。

## 命令速查

```bash
# 知识库（默认 all；--type 过滤个人 / 企业）
yzj-cli doc workspace list
yzj-cli doc workspace list --type personal       # 仅个人知识库（visibility=2）
yzj-cli doc workspace list --type enterprise     # 仅企业知识库（visibility=1）
yzj-cli doc workspace get --id <KB_ID>
yzj-cli doc workspace create --name "Team Notes" --description "共享笔记"
yzj-cli doc workspace create --name "团队知识库" --visibility 1 --all-member 3   # 企业知识库，全员可查看

# 删除知识库（❗ 不可恢复，需用户确认）
yzj-cli doc workspace delete --id <KB_ID> --yes

# 文档树
yzj-cli doc list --workspace <KB_ID>
yzj-cli doc list --workspace <KB_ID> --parent-id <PARENT_DOC_ID>

# 文档详情
yzj-cli doc get --id <DOC_ID>

# 最近访问
yzj-cli doc recent
yzj-cli doc recent --limit 10
yzj-cli doc recent --last-visit-time <MS_TIMESTAMP>   # 翻页游标

# 创建在线文档（otl）
yzj-cli doc create --workspace <KB_ID> --title "在线文档"
yzj-cli doc create --workspace <KB_ID> --title "在线文档" --parent-id <PARENT_DOC_ID>
# 想建文件夹/归类时，也用 doc create 建一个文档作为父节点
yzj-cli doc create --workspace <KB_ID> --title "项目资料"  # 之后子文档挂在其下
# 多维表格（dbt）请使用 sheet scope：yzj-cli sheet create（详见 sheet.md）

# 搜索文档
yzj-cli doc search --keyword "产品需求"
yzj-cli doc search --keyword "测试" --workspace <KB_ID>   # 在指定知识库内搜索
yzj-cli doc search --keyword "报告" --page-num 1 --page-size 10

# 覆盖/追加智能文档内容（仅支持 otl 类型）
yzj-cli doc write --id <DOC_ID> --content "# 标题

正文内容"
yzj-cli doc write --id <DOC_ID> --content "## 新章节
追加内容" --mode append
yzj-cli doc write --id <DOC_ID> --content "<h1>标题</h1><p>正文</p>" --format html

# 节点操作
yzj-cli doc rename --id <DOC_ID> --title "New Title"
yzj-cli doc move   --id <DOC_ID> --target-parent-id <PARENT_DOC_ID>
yzj-cli doc delete --id <DOC_ID> --yes   # ⚠️ 不可恢复；须用户确认后加 --yes，未加会被 CLI 拒绝

# 块操作（仅入口，详细说明与示例见 [doc/block_operation.md](./doc-block_operation.md)）
yzj-cli doc block list   --id <DOC_ID>
yzj-cli doc block list   --id <DOC_ID> --block-id <BLOCK_ID>
yzj-cli doc block insert --id <DOC_ID> --element "[{\"type\":\"text\",\"text\":\"内容\"}]"
yzj-cli doc block insert --id <DOC_ID> --parent-block-id <BLOCK_ID> --element "[...]"   # 在指定父块下插入
yzj-cli doc block update --id <DOC_ID> --operations "[...]"     # 字段结构详见 block_operation.md
yzj-cli doc block delete --id <DOC_ID> --operations "[...]" --yes     # ⚠️ 不可恢复，须用户确认后加 --yes；字段结构详见 block_operation.md
yzj-cli doc block replace --id <DOC_ID> --start 2 --end 5 --content "[...]"   # 先删后插，startIndex必须>=1

# 导入文件到知识库
# inline 模式（md 文件）
yzj-cli doc import --workspace <KB_ID> --items '[{"fileName":"notes.md","content":"正文内容"}]'
yzj-cli doc import --workspace <KB_ID> --parent-id <PARENT_DOC_ID> --items '[{"fileName":"notes.md","content":"正文内容"}]'
# reference 模式（非 md 格式，先 file upload 拿 fileId）
yzj-cli doc import --workspace <KB_ID> --items '[{"fileName":"report.docx","fileId":"<FILE_ID>","fileSize":204800}]'
yzj-cli doc import --workspace <KB_ID> --parent-id <PARENT_DOC_ID> --items '[{"fileName":"report.docx","fileId":"<FILE_ID>","fileSize":204800}]'

# 下载文档到本地（30 分钟有效临时地址；仅支持 Office/HTML 文件，不支持 otl/dbt/md）
yzj-cli doc download --id <DOC_ID>
```

## doc workspace（知识库容器）

`doc workspace create [--visibility {1,2}] [--all-member {2,3}]`、`doc workspace get --id`、`doc workspace create --name`、`doc workspace delete --id` 的完整命令表、`--type` 取値、返回字段（`visibility` / `permissionLevel` / `bizType` 等）与常见问题，统一在 [doc/workspace.md](./doc-workspace.md)。

## doc workspace create 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--name <NAME>` | 是 | 知识库名称，最大 100 字符 |
| `--description` | 否 | 知识库描述 |
| `--visibility` | 否 | 1=企业知识库，2=个人知识库（默认 2） |
| `--all-member` | 否 | 企业全员权限：2=可编辑，3=可查看（仅 `--visibility 1` 时有效） |

## doc search 参数（搜索文档）

按关键词模糊搜索文档标题和文件名，结果已按权限过滤。

| 参数 | 必填 | 说明 |
|------|------|------|
| `--keyword <关键词>` | 是 | 搜索关键词，模糊匹配标题和文件名 |
| `--workspace <KB_ID>` | 否 | 限定在指定知识库内搜索 |
| `--page-num` | 否 | 页码，从 1 开始（默认 1） |
| `--page-size` | 否 | 每页条数，默认 20，最大 50 |

返回：`data.list` 为文档数组（格式同 `doc get`），`data.count`（本次返回条数）、`data.total`（关键词总命中数）、`data.more`（是否还有下一页；末页时可能仍为 true，是否继续翻页以 `total` 与已取条数对比判断）。

> 建议传 `--workspace` 缩小搜索范围，提升性能和结果准确性。

## doc write 参数（覆盖/追加文档内容）

覆盖或追加智能文档（otl）的整体内容。仅支持 `otl` 类型，不支持 `dbt`。

| 参数 | 必填 | 说明 |
|------|------|------|
| `--id <DOC_ID>` | 是 | 文档 ID（必须是 otl 类型） |
| `--content <内容>` | 是 | 文档内容（Markdown 或 HTML 格式） |
| `--mode` | 否 | `overwrite`（默认，整体替换）或 `append`（追加到末尾） |
| `--format` | 否 | `markdown`（默认）或 `html` |

> 首次写入推荐 `--mode overwrite`；在末尾补充内容用 `--mode append`。需对文档有编辑权限。

## doc block replace 参数

整段替换智能文档（otl）中连续多个块（先删后插）。仅支持 `otl` 类型。

| 参数 | 必填 | 说明 |
|------|------|------|
| `--id <DOC_ID>` | 是 | 文档 ID（必须是 otl 类型） |
| `--start <N>` | 是 | 删除起始索引（包含，**必须 >= 1**；index=0 是文档标题，不可删除） |
| `--end <N>` | 是 | 删除结束索引（不包含，必须 > start） |
| `--content <JSON>` | 是 | 替换后插入的块节点 JSON 数组，格式与 `doc block insert --element` **完全一致**（详见 [block_operation.md](./doc-block_operation.md)） |
| `--parent-block-id` | 否 | 父块 ID，默认 `"doc"`（文档根块） |

> 与 `doc block update` 的区别：`update` 改单块内容且块数量不变；`replace` 整段替换，适合整节重写或块数量会变化的场景。执行前必须先 `doc block list` 确认索引，向用户确认后执行。详见 [block_operation.md](./doc-block_operation.md)。

## doc list 返回字段

返回 `data.list` 数组，每项字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 节点 ID |
| `type` | int | 2=文档（当前主要使用）；1=旧版目录（兼容保留） |
| `title` | string | 节点标题 |
| `parentId` | string | 父节点 ID，null 表示根级 |
| `hasChildren` | bool | 是否有子节点 |
| `fileSuffix` | string | 仅支持 `otl`=在线文档，`dbt`=多维表格 |
| `permissionLevel` | int | 1=可管理，2=可编辑，3=可查看，9=无权限 |
| `createTime` / `updateTime` | string | 创建/更新时间 |
| `creatorName` | string | 创建人姓名 |

## doc get 返回字段

字段同 `doc list`，额外返回 `kbId`（所属知识库 ID）。用于按文档 ID 查单条详情。

## doc recent 参数与返回

列出当前用户最近访问的文档，按访问时间倒序。

| 参数 | 必填 | 说明 |
|------|------|------|
| `--limit` | 否 | 返回数量，默认 20，最大 100 |
| `--last-visit-time` | 否 | 翻页游标，上一页最后一条记录的 `visitTime`（毫秒时间戳） |

返回字段同 `doc list`，额外包含 `kbName`（所属知识库名称）与 `visitTime`（最近访问时间戳，毫秒）。用于回答"最近看过哪些文档"。

## doc create 参数

`doc create` 创建**在线文档（otl）**。多维表格（dbt）请使用 `sheet create`（见 [sheet.md](./sheet.md)）。

> **知识库没有独立的文件夹类型。** 当用户想"建文件夹/目录/归类"时，用 `doc create` 建一个文档作为父节点，后续子文档通过 `doc create --parent-id` 或 `doc move --target-parent-id` 挂在其下，形成层级。

| 参数 | 必填 | 说明 |
|------|------|------|
| `--workspace <KB_ID>` | 是 | 知识库 ID |
| `--title` | 是 | 文档标题 |
| `--parent-id` | 否 | 父文档 ID，省略则创建在根级 |

> ⚠️ **标题去重**：`--title` 的值已作为节点标题（文件名）展示在知识库列表中。后续通过 `doc block insert` 写入正文时，**不得**再以与 `--title` 相同的文本作为一级标题（`heading level 1`）插入，否则文档会出现两个标题。

## doc import 参数（导入文件到知识库）

支持将文件导入知识库，通过 `--items <JSON>` 传递导入条目数组（reference 和 inline 两种模式）。

### 支持的格式与导入模式

| 格式 | 模式 | 结果 |
|------|------|------|
| `.md` | inline（传 `content` 字段） | 内容解析为在线文档（otl），成为在线可编辑文档 |
| `.docx` `.xlsx` `.xls` `.csv` `.pptx` `.pdf` `.html` `.htm` | reference（先 `file upload` 取 `fileId`，传 `fileId` 字段） | 以原文件格式存入知识库，不转换内容 |

### 不支持的格式

- 上述列表之外的文件格式（如 `.txt`、`.json`、`.zip` 等）不支持导入
- 单文件超过 **100MB** 不支持导入

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--workspace <KB_ID>` | 是 | 目标知识库 ID |
| `--items <JSON>` | 是 | 导入条目 JSON 数组（inline 或 reference 模式，见下方） |
| `--parent-id` | 否 | 父节点 ID，省略则导入到根级 |

**items 两种模式**：

| 模式 | 适用场景 | 必填字段 | 示例 |
|------|----------|----------|------|
| inline | `.md` 文件，直传文本内容 | `fileName`、`content` | `[{"fileName":"笔记.md","content":"正文内容"}]` |
| reference | 非 md 格式，已通过 `file upload` 上传 | `fileName`、`fileId` | `[{"fileName":"报告.pdf","fileId":"<FILE_ID>","fileSize":204800}]` |

模式由 `fileName` 后缀自动判断：`.md` → inline；其他 → reference。

### 标题去重规则

> ⚠️ **inline 模式下，`fileName` 的值（去掉后缀）会成为文档节点标题。`content` 中不得再以相同文本的一级标题（`# 标题`）开头，否则文档会出现两个标题。**
>
> 正确做法：`fileName` 作为标题，`content` 直接从正文或二级标题开始。
>
> ❌ **错误**（fileName "会议纪要" 与 content 首行 `# 会议纪要` 重复）：
>
> ```json
> [{"fileName":"会议纪要.md","content":"# 会议纪要\n\n2026-08-12 同步会..."}]
> ```
>
> ✅ **正确**（content 直接从正文开始）：
>
> ```json
> [{"fileName":"会议纪要.md","content":"2026-08-12 同步会..."}]
> ```
>
> ✅ **正确**（content 从二级标题开始，与文件名不同）：
>
> ```json
> [{"fileName":"周报.md","content":"## 本周进展\n\n..."}]
> ```

### 导入工作流

**md 文件（inline 模式）**：
```bash
yzj-cli doc import --workspace <KB_ID> --items '[{"fileName":"notes.md","content":"正文内容"}]'
```

**非 md 文件（reference 模式，docx/xlsx/xls/csv/pptx/pdf/html/htm）**：
```bash
# 第一步：上传到文件服务
yzj-cli file upload --file ./report.docx
# 第二步：用返回的 fileId 以 reference 模式导入到知识库
yzj-cli doc import --workspace <KB_ID> --items '[{"fileName":"report.docx","fileId":"<FILE_ID>","fileSize":204800}]'
```

### 易混淆

| 场景 | 用 | 不用 | 理由 |
|------|----|------|------|
| md 文件导入为在线文档 | `doc import --items '[{"fileName":"*.md","content":"..."}]'`（inline 模式） | `doc create` + 手动粘贴内容 | `doc import` inline 模式自动解析 md 内容并转为在线文档结构；`doc create` 只建空文档。⚠️ inline 模式 `content` 不得以与 `fileName` 相同的一级标题开头（标题去重，见上方「标题去重规则」） |
| docx/xlsx 等格式存入知识库 | `file upload` → `doc import --items '[{"fileName":"*.docx","fileId":"...","fileSize":...}]'`（reference 模式） | 直接传文件路径 | 非 md 格式必须先上传到文件服务取得 fileId，再以 reference 模式导入 |
| 上传文件用于 IM 消息 | `file upload`（不调 import） | `doc import` | 只发给 IM 不需要导入知识库时，`file upload` 的 fileId 直接用于消息发送 |

## doc download（下载文件到本地）

下载知识库中 Office/HTML 文件到本地，自动处理临时 URL 的获取与流式下载。

### 支持的格式

与 `doc import` 支持的非 md 格式一致：

| 格式 | 后缀 |
|------|------|
| Word | `.docx` |
| Excel | `.xlsx` `.xls` `.csv` |
| PowerPoint | `.pptx` |
| PDF | `.pdf` |
| HTML | `.html` `.htm` |

> ⚠️ 不支持在线文档（`fileSuffix=otl`）和多维表格（`fileSuffix=dbt`）——在线文档无独立文件可下载。不支持 `.md`（导入时已解析为 otl）。

### 参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--id <DOC_ID>` | 是 | 文档 ID（知识库节点 ID） |
| `--output <PATH>` | 否 | 保存路径，省略则按原文件名保存到当前目录 |
| `--overwrite` | 否 | 文件已存在时覆盖，默认自动重命名（如 report (1).pdf） |

### 使用场景

**场景一：下载文件到本地**
```bash
# 直接下载到当前目录，输出：downloaded N bytes to report.pdf
yzj-cli doc download --id <DOC_ID>
# 指定保存路径
yzj-cli doc download --id <DOC_ID> --output ./reports/合同.pdf
```

**场景二：读取 Office/HTML 文件内容**

知识库中的 docx/xlsx/pptx 等文件无法通过 `doc get` 直接读取正文内容，需先下载到本地再解析：
```bash
# 1. 下载到本地
yzj-cli doc download --id <DOC_ID>
# 2. 用 Read 工具读取下载的文件内容
```

## doc block（块级读写）

所有 block 相关命令的参数、块类型、内联节点属性、insert / update / delete / replace 完整 JSON schema 与示例，统一在 [doc/block_operation.md](./doc-block_operation.md)。

> ⚠️ `doc block update` 必须传 `{"operation":"update_content"/"update_attrs","blockId":...,"content"/"attrs":...}`；`doc block delete` 的 `blockId` 是**父块 ID**（不是被删块本身），且必须带 `{"startIndex":N,"endIndex":M}` 三字段齐全。`doc block replace` 的 `--start` 必须 >=1（index=0 是文档标题不可删除）。详见子文档。

## 文档链接返回

执行以下命令后，**必须**拼接文档链接并返回给用户：

- `doc create` — 创建文档后
- `doc import` — 导入文件后
- `doc write` — 覆盖/追加内容后
- `doc block insert` — 插入内容后
- `doc block update` — 更新内容后

链接格式：

```
https://www.yunzhijia.com/knowledge/lingee/#/store/doc/<DOC_ID>
```

- `<DOC_ID>` 取命令返回的节点 ID
- 示例：节点 ID `6a684c293814fd27380acc8e` → `https://www.yunzhijia.com/knowledge/lingee/#/store/doc/6a684c293814fd27380acc8e`

## 危险操作

- `doc delete` — 删除节点，**不可恢复**，执行前必须向用户展示目标节点名称并获得确认；确认后命令须带 `--yes`（未带会被 CLI 拒绝）
- `doc workspace delete` — 删除知识库，**不可恢复**，会同时删除其下所有文档，执行前必须向用户确认；确认后命令须带 `--yes`（未带会被 CLI 拒绝）
- `doc move` — 移动节点，改变位置，执行前需确认目标路径
- `doc block delete` — 删除块内容，**不可恢复**，执行前需确认并带 `--yes`（详见 [block_operation.md](./doc-block_operation.md)）
- `doc block replace` — 替换块范围（先删后插），破坏性编辑，执行前应向用户确认替换范围
