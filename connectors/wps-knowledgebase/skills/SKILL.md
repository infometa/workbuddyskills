---
name: wps-knowledgebase
version: 2.0.2
description: >-
  WPS/zhishi（WPS知识库）云端知识库：列表/详情、文件树、智能问答（ask SSE）、分享链接、创建关闭与文件 CRUD、导入上传与格式转换（OTL 下载限制见正文）。
  当用户用中文只说「知识库」「我的知识库」「在知识库里查/搜/问」「从知识库找答案」「知识库问答」「zhishi」「kwiki」或英文 knowledge base / ask，且意图是云端 Skills Hub 里的内容而非仅搜索本地仓库文件时，必须使用本 skill 并用 `kwiki-cli kwiki <tool>` 执行。
  亦适用于终端、CI、脚本自动化及 access_token / `X_KWIKI_AUTH` 等多账号鉴权场景。
---

# Kwiki Skills Hub CLI（kwiki-cli）

## When to Use（命中关键词）

优先载入并遵循本 skill，当用户表述中出现下列任一意图（**不要求**用户说出 CLI 名称）：

- **中文**：知识库、我的知识库、个人知识库、企业知识库、在知识库里（搜/查/找/问）、知识库问答、从知识库回答、金山/WPS 知识库、`zhishi`、`kwiki`。
- **英文**：knowledge base、ask the knowledge base、skills hub（与 zhishi/kwiki 同语境时）。
- **要做的事**：列出知识库或文件夹、对知识库做智能问答（含可选联网/深度思考）、取分享链接、或做任何 skills_hub 支持的文件/空间管理。

**不要做**：用户明确只要搜索 **当前 Cursor 工作区/本地磁盘** 里的文件且未提及云端知识库时——用编辑器搜索工具即可；若用户区分不清，先用简短一问确认是否要 **WPS/zhishi 云端知识库**。

若 skill 未被自动选中，请让用户在对话中使用 **`/wps-knowledgebase`** 或对 **`wps-knowledgebase`** skill 使用 **`@`** 附加。

## 核心概念

- **Skills Hub API 前缀**：`/kwiki/api/v1/skills_hub`（由 `--base-url` 指定站点根，如 `https://zhishi.wps.cn`）。
- **Kwiki 标识（ID）基础**：

| ID | 说明 |
|------|------|
| `drive_id` | 空间的驱动 ID；与个人知识库 **`kuid`** 常可与后缀数字互推，企业知识库与 **`kuid`** 的对应以后台为准 |
| `kuid` | 通用节点 ID。**`0s` 开头=知识库（空间）**；**`0l` 开头=文件/文件夹等**（与云文档 **`fileId`** 的对应以接口为准） |

**知识库空间 `kuid`（均为 `0s` 开头）**：个人与企业编码形态不同，**共同点仅为前缀 `0s`**（第 3 个字符不一定是 `_`）。

- **个人知识库**：常见如 **`0s_3079998078`**，`0s` 之后多为 **`_<drive_id 数字串>`**，后缀与 **`drive_id`** 在数值上一致、可互推。
- **企业知识库**：常见如 **`0sOVd8PU`**，`0s` 之后为**无数学意义的纯 ID**；**不要**按个人规则把后缀当作 `drive_id` 解析。

- **树与列表**：`file-list` 等返回的树形结构中，**`0l`** 亦可能为文件夹等链接节点；与云文档 **`fileId`** 的对应关系以接口返回字段为准。
- **工具形态**：所有业务接口挂在 `kwiki` 子命令下，仅接受 **flag**，不接受位置参数；输出默认可用 `--format pretty` 美化 JSON。

## 鉴权与环境变量

支持**多账号**（`--account`，大小写不敏感，不指定则为 `default`）。每个账号独立存储 token：

| 账号 | keyring account | 环境变量 |
|------|-----------------|----------|
| `default`（不指定 / 空） | `default` | **`X_KWIKI_AUTH`** |
| 命名账号（如 `john`） | `john` | **`X_KWIKI_AUTH_JOHN`** |

| 方式 | 说明 |
|------|------|
| OS keyring | **读/写优先**：`service kwiki-cli`，`account` 为规范化后的账号名（`auth login` 经 **`keychain.SetAccessToken`** 写入） |
| 环境变量 | **读降级**：keyring 无可用 token 或 keyring 读失败时，用对应账号的环境变量（trim 后非空）。**写降级**：`keyring.Set` 失败时，对本进程 **`os.Setenv`** 写入（**不**持久到 shell；新终端需自行 `export` 或修复 keyring） |
| `kwiki-cli auth login` | 设备码 + 浏览器完成登录后轮询换 token；`--account john` 登录到命名账号 |

```bash
kwiki-cli auth login                    # 登录到 default 账号
kwiki-cli auth login --account john     # 登录到 john 账号
kwiki-cli auth status                   # 成功时输出：Logged in
kwiki-cli --account john kwiki file-list --kuid <kuid>   # 使用 john 账号的 token
```

业务代码通过 **`keychain.GetAccessToken(account)` / `keychain.SetAccessToken(account, token)`** 统一读写，不直接拼环境变量或 keyring。**`SetAccessToken`** 返回 `(storedInKeyring bool, err)`：`false` 且 `err==nil` 表示已退化为仅本进程环境变量。使用环境变量作降级时，进程需能读到该变量（IDE/子进程若未继承用户环境，会出现「本机已设变量但 CLI 仍无 token」）。已带 token 的请求会携带 **`X-Kwiki-Auth: <token>`**。所有对 Kwiki / Skills Hub 的请求还会携带 **`X-Kwiki-Cli-Ver`**（CLI 版本号，供服务端统计；npm **`build:dev` / `build`** 构建的二进制会写入发布版本，裸 `go build` 常为 `dev`）。**所有 `kwiki` 工具均需 token**。

其他常用环境变量：

| 变量 | 说明 |
|------|------|
| `KWIKI_BASE_URL` | API 站点根，默认 `https://zhishi.wps.cn` |
| `X_KWIKI_SOURCE` | 渠道来源标识；非空时每个请求附加 `X-Kwiki-Cli-Source` header，供服务端统计渠道。也可通过 `~/.kwiki-cli/config.json` 的 `source` 字段持久化（环境变量优先） |

## 安装与目录（npm 包）

- **Go**：仓库根执行 **`npm run build:dev`**，编译到 `build/kwiki-cli-<os>-<arch>/bin/`，`scripts/run.js` 自动定位。
- **npm**：包名 `@ks-personal/kwiki-cli`；通过 `optionalDependencies` 按平台安装对应的二进制子包，`run.js` 通过 `require.resolve` 直接从子包定位二进制。`npx kwiki-cli` / `kwiki-cli` 入口为 `scripts/run.js`。
- **Kimi skills 目录**：可用 `KWIKI_KIMI_SKILLS_DIR` 覆盖默认 `~/.kimi/skills`。

## 全局参数

- **`--base-url`**：与 `KWIKI_BASE_URL` 一致，指定 zhishi 根地址。
- **`--account`**：token 账号名（不指定为 `default`）；命名账号环境变量为 `X_KWIKI_AUTH_<UPPER>`。
- **`--dry-run` / `-n`（根命令）**：对 **会改状态** 的 `kwiki` 子命令（`RiskWrite` / `RiskHighRiskWrite`，如删除、移动、创建、重命名、上传、知识库关闭等）**不发起 HTTP**，只打印计划 JSON（含 `service`、`tool`、`risk`、`flags`、`base_url`）；此类 **`--dry-run` 不解析 token**（便于本地核对 flag）。**只读**工具（`RiskRead`）在带 `--dry-run` 时仍会正常请求（需 token）。
- **各 tool 上的 `--format`**：`json`（默认）或 `pretty`。

## 命令形态

```bash
kwiki-cli kwiki <tool> [flags]
kwiki-cli --account <name> kwiki <tool> [flags]
kwiki-cli auth login [--account <name>]
kwiki-cli auth status | logout
```

---

## 工具说明（`kwiki-cli kwiki …`）

### `knowledge-view-list` — 获取知识库列表

**说明**：获取知识库列表

| Flag | 必选 | 说明 |
|------|------|------|
| `--keyword` | 否 | 名称关键字 |
| `--page-size` | 否 | 分页 |
| `--page-token` | 否 | 翻页令牌 |

```bash
kwiki-cli kwiki knowledge-view-list --keyword 项目 --page-size 20
```

---

### `knowledge-view-get` — 查询知识库详情

**说明**：查询知识库详情。**`--kuid` 与 `--name` 至少填一个。**

| Flag | 必选 | 说明 |
|------|------|------|
| `--kuid` | 否 | 按照知识库kuid查询 |
| `--name` | 否 | 按照知识库名称模糊匹配查询 |

```bash
kwiki-cli kwiki knowledge-view-get --kuid "<kuid>"
kwiki-cli kwiki knowledge-view-get --name "演示"
```

---

### `knowledge-view-create` — 创建知识库

**说明**：创建知识库

| Flag | 必选 | 说明 |
|------|------|------|
| `--name` | 是 | 知识库名称 |
| `--img` | 否 | 知识库封面图片 |
| `--desc` | 否 | 知识库简介 |

```bash
kwiki-cli kwiki knowledge-view-create --name "产品库" --desc "简介"
```

---

### `knowledge-view-update` — 修改知识库基础配置

**说明**：用 **`kuid`** 定位知识库；只传需要改的字段（未传的字段服务端保留原值）。请求体含 **`kuid`**（必填）及可选 **`cover_img`**、**`name`**、**`desc`**。

| Flag | 必选 | 说明 |
|------|------|------|
| `--kuid` | 是 | 知识库 kuid |
| `--cover-img` | 否 | 封面；不传则不修改 |
| `--name` | 否 | 名称；不传则不修改 |
| `--desc` | 否 | 简介；不传则不修改 |

```bash
kwiki-cli kwiki knowledge-view-update --kuid "<kuid>" --cover-img "https://zl.wpscdn.cn/2025/06/09/other/4.png" --name "新名称"
kwiki-cli kwiki knowledge-view-update --kuid "<kuid>" --desc "新简介"
```

---

### `knowledge-view-close` — 关闭知识库

**说明**：关闭知识库(根据知识库的kuid)

| Flag | 必选 | 说明 |
|------|------|------|
| `--kuid` | 是 | 知识库的kuid |

```bash
kwiki-cli kwiki knowledge-view-close --kuid "<kuid>"
```

---

### `knowledge-view-share-link` — 获取知识库分享链接

**说明**：GET `knowledge_view/share_link`，查询参数 **`kuid`**。

| Flag | 必选 | 说明 |
|------|------|------|
| `--kuid` | 是 | 知识库 kuid |

```bash
kwiki-cli kwiki knowledge-view-share-link --kuid "<kuid>"
```

---

### `knowledge-view-ask` — 智能问答

**说明**：POST `knowledge_view/ask`，服务端以 **`text/event-stream`** 流式返回。CLI **默认**将 SSE 增量片段（尤其 **`answer_citations[].text`**）**拼接为完整答案**后，按 **`--format json|pretty`** 输出单个 JSON 对象，便于 Agent 直接消费。需要原始 SSE 时加 **`--stream`**。

Body 含 **`input`**；可选 **`kuids`**（重复 **`--kuid`**）、**`scope`**（未传 **`--kuid`** 时 CLI 自动设 **`all_wiki`**）、**`use_web_search`**（**`--web-search`**）、**`switch_thinking`**（**`--switch-thinking`**，深度思考）。

| Flag | 必选 | 说明 |
|------|------|------|
| `--input` | 是 | 问题内容 |
| `--kuid` | 否 | 知识库 kuid，可多次指定；省略时在全库范围问答（`scope=all_wiki`） |
| `--web-search` | 否 | 是否联网搜索 |
| `--switch-thinking` | 否 | 深度思考 |
| `--stream` | 否 | 透传 SSE 原始行（不聚合） |

```bash
kwiki-cli kwiki knowledge-view-ask --input "你的问题"
kwiki-cli kwiki knowledge-view-ask --input "你的问题" --kuid "<kuid>" --web-search --switch-thinking
kwiki-cli kwiki knowledge-view-ask --input "你的问题" --stream   # 原始 SSE
```

**输出字段**：聚合后常见 **`answer_citations`**（`text` 为完整答案，`reply_sources` / `citations` 等为引用来源）；亦可能含 `query`、`process_display` 等元数据。

---

### `skill-update` — 检查并更新 SKILL.md

**说明**：复用 `GET /kwiki/api/v1/skills_hub/skill?skill_name=kwiki&version=latest` 获取最新 SKILL 版本，CLI 端比较版本号后自动写入各 Agent 的 `wps-knowledgebase` skill 目录（Cursor、Claude Code、OpenClaw、Kimi）。无需鉴权。

| Flag | 必选 | 说明 |
|------|------|------|
| `--check-only` | 否 | 仅检查是否有更新，不写入文件 |

```bash
kwiki-cli kwiki skill-update
kwiki-cli kwiki skill-update --check-only
```

---

### `file-list` — 查询知识库或文件夹内文件列表

**说明**：查询知识库或文件夹里面的文件列表(包括文件和文件夹)

| Flag | 必选 | 说明 |
|------|------|------|
| `--kuid` | 是 | 知识库id(0s开头)或文件夹id(0l开头) |
| `--page-size` | 否 | 分页 |
| `--page-token` | 否 | 翻页令牌 |

```bash
kwiki-cli kwiki file-list --kuid "<kuid>" --format pretty
```

---

### `file-create` — 创建知识库文件或文件夹

**说明**：创建知识库文件或文件夹

| Flag | 必选 | 说明 |
|------|------|------|
| `--doc-type` | 是 | 文档类型：folder=文件夹; w=wps文档; s=表格et; o=智能文档fp; p=ppt; d=轻维表 |
| `--kuid` | 是 | 在根目录创建则传知识库kuid, 在文件夹内创建则传文件夹的kuid |
| `--title` | 是 | 新建的文件名或文件夹名 |

```bash
kwiki-cli kwiki file-create --doc-type folder --kuid "<parent_kuid>" --title "归档"
```

---

### `file-delete` — 删除知识库文件或文件夹

**说明**：知识库删除文件或文件夹。删除后进入回收站，可在期限内到 `https://www.kdocs.cn/enttrash/0` 等进行恢复。

| Flag | 必选 | 说明 |
|------|------|------|
| `--kuid` | 是 | 知识库的文件或文件夹id |

```bash
kwiki-cli kwiki file-delete --kuid "<kuid>"
```

---

### `file-rename` — 重命名文件或文件夹

**说明**：重命名文件或文件夹

| Flag | 必选 | 说明 |
|------|------|------|
| `--kuid` | 是 | 知识库的文件或文件夹kuid |
| `--title` | 是 | 新文件或文件夹名 |

```bash
kwiki-cli kwiki file-rename --kuid "<kuid>" --title "新标题"
```

---

### `file-download` — 下载文件

**说明**：下载文件, 根据kuid(仅支持文件), 提供两种返回格式, download_link或file_base64(推荐)。**请求体**始终含 `kuid`；**仅当传入 `--response-type` 时才附带 `response_type`**。不传 `response_type` 则由服务端默认。

**限制**：**OTL 智能文档**（`doc_origin_type` 为 `otl` / `doc_type` 为 `o` 等）**不支持**通过本接口下载；调用 `file-download`（含 `file_base64`、`download_link`）会返回业务错误（如 `400408000`）。需取 OTL 正文时请用 **`file-content`**，勿对 OTL 走 `file-download`。

| Flag | 必选 | 说明 |
|------|------|------|
| `--kuid` | 是 | 知识库文件kuid |
| `--response-type` | 否 | 返回类型；不传则请求体不含该字段。可选 download_link、file_base64（推荐 file_base64，download_link 常需 wps_sid 才能访问） |

```bash
kwiki-cli kwiki file-download --kuid "<file_kuid>"
kwiki-cli kwiki file-download --kuid "<file_kuid>" --response-type file_base64
```

---

### `file-content` — 获取文件正文

**说明**：GET `skill/file/content`，按文件 **`kuid`（`0l` 开头）** 读取正文。适用于 OTL 等不支持 `file-download` 的文档。查询参数始终含 `kuid`；仅当传入 **`--content-format`** 时附带 `format`。

| Flag | 必选 | 说明 |
|------|------|------|
| `--kuid` | 是 | 文件 kuid（`0l` 开头） |
| `--content-format` | 否 | 正文格式：`plain`（默认）、`markdown`、`kdc` |

```bash
kwiki-cli kwiki file-content --kuid "<file_kuid>"
kwiki-cli kwiki file-content --kuid "<file_kuid>" --content-format markdown --format pretty
```

成功时 `data` 含 **`title`**、**`format`**、**`content`**。

---

### `file-convert` — 文件格式转换

**说明**：将指定格式的内容转换为目标格式的文件。目前仅支持 md -> otl（Markdown 转智能文档）。**请求体**始终含 `kuid`、`title`、`content`；**仅当传入 `--from` / `--to` 时才附带对应字段**。

成功时返回 **`file_id`**、**`file_kuid`**（`0l`+`link_id`）、**`file_link_id`**、**`file_name`**。后续读写请优先用 **`file_kuid`**（如 `file-content`）。

注意：md→otl 在服务端创建空模板后异步写入正文，接口返回 `file_id`/`file_kuid` 后，`file-list` 的 `size` 可能短暂为模板值（约 28175），约 1–2 分钟后变为实际大小；刚返回即可用 `file-content` 读正文（内容就绪时机以云端为准）。

| Flag | 必选 | 说明 |
|------|------|------|
| `--kuid` | 是 | 目标知识库的 kuid（以 `0s` 开头），转换后的文件创建在此知识库下 |
| `--title` | 是 | 文件标题（自动补 .otl 后缀） |
| `--content` | 是 | 源内容（markdown 文本） |
| `--from` | 否 | 源格式；不传则请求体不含该字段（由服务端默认） |
| `--to` | 否 | 目标格式；不传则请求体不含该字段（由服务端默认） |

```bash
kwiki-cli kwiki file-convert --kuid "<kb_kuid>" --title "说明" --content "# 标题\n正文"
kwiki-cli kwiki file-convert --kuid "<kb_kuid>" --title "说明" --content "# 标题" --from md --to otl
```

---

### `file-move` — 移动知识库文件或文件夹

**说明**：移动知识库的文件或文件夹；请求体含 **`drive_id`**、**`dest_drive_id`**、**`space_kuid`**、**`file_kuids`** 等。**`drive_id`** / **`kuid`** 可从 **`knowledge-view-list`** 等接口返回获取。

| Flag | 必选 | 说明 |
|------|------|------|
| `--drive-id` | 是 | 源知识库 drive_id |
| `--dest-drive-id` | 是 | 目标知识库 drive_id |
| `--dest-parent-id` | 否 | 目标父节点 ID，不传则移动到根目录 |
| `--space-kuid` | 是 | 源知识库 kuid |
| `--file-kuid` | 是 | 待移动文件的 kuid（可重复 --file-kuid） |

```bash
kwiki-cli kwiki file-move --drive-id b --dest-drive-id c --space-kuid d --file-kuid f1 --file-kuid f2
```

---

### `file-import` — 导入云文档到知识库

**说明**：导入云文档文件到知识库。请求体使用 `file_ids` 数组；CLI 用重复 **`--file-id`** 传入多个 id。

| Flag | 必选 | 说明 |
|------|------|------|
| `--kuid` | 是 | 知识库id |
| `--action` | 是 | 上传云文档副本 copy 上传云文档快捷方式 shortcut |
| `--file-id` | 是 | 导入文件的 fileid（可重复 --file-id，对应接口 file_ids） |

```bash
kwiki-cli kwiki file-import --kuid "<folder_kuid>" --action copy --file-id id1 --file-id id2
```

---

### `file-upload` — 本地上传（multipart）

**说明**：POST /skills_hub/skill/file/upload（multipart，本地上传）。用于本机文件上传到知识库侧的补充场景。

| Flag | 必选 | 说明 |
|------|------|------|
| `--drive-id` | 是 | drive_id |
| `--parent-link-id` | 否 | parent_link_id |
| `--file` | 是 | 本地文件路径 |

```bash
kwiki-cli kwiki file-upload --drive-id "<drive_id>" --file ./a.docx
```

---

## 常用工作流示例

### 查看 kwiki-cli 使用说明（skill 文档）

Skill 正文随 **`@ks-personal/kwiki-cli`** npm 包内的 **`skills/wps-knowledgebase/SKILL.md`** 分发；也可在本仓库 **`skills/wps-knowledgebase/SKILL.md`** 直接阅读。CLI 版本以 **`package.json` / `npm`** 为准。

### 浏览知识库根目录再进入子文件夹

```bash
kwiki-cli kwiki file-list --kuid "<space_kuid>"
kwiki-cli kwiki file-list --kuid "<folder_0l_kuid>" --page-size 50
```

### 新建文件夹并导入云文档

```bash
kwiki-cli kwiki file-create --doc-type folder --kuid "<space_kuid>" --title "资料"
kwiki-cli kwiki file-import --kuid "<new_folder_kuid>" --action shortcut --file-id "<cloud_file_id>"
```

### 列表 / 详情 / 分享 / 问答 / 关闭知识库

```bash
kwiki-cli kwiki knowledge-view-list --keyword 团队
kwiki-cli kwiki knowledge-view-get --kuid "<kuid>"
kwiki-cli kwiki knowledge-view-share-link --kuid "<kuid>"
kwiki-cli kwiki knowledge-view-ask --input "问题" --kuid "<kuid>"
kwiki-cli kwiki knowledge-view-close --kuid "<kuid>"
```

### 检查并更新 Skill

```bash
kwiki-cli kwiki skill-update
kwiki-cli kwiki skill-update --check-only
```

---

## 提示

- **命令形态**：所有 `kwiki-cli kwiki <tool>` **只接受 flag**，不接受位置参数；多余参数会报错。
- **鉴权**：所有 `kwiki` 工具需 **`keychain.GetAccessToken(account)`** 能解析到 token（优先 keyring，对应环境变量降级；默认 **`X_KWIKI_AUTH`**，命名账号 **`X_KWIKI_AUTH_<UPPER>`**）。写操作前确认与 **`--base-url`** 指向正确环境。
- **全局**：根命令持久化 **`--base-url`**（或 `KWIKI_BASE_URL`）、**`--account`**；各 tool 上 **`--format json|pretty`** 控制输出（**`knowledge-view-ask`** 默认聚合 SSE 为 JSON；加 **`--stream`** 时透传原始 SSE）。
- **npm / skills**：安装后若本机 Agent skills 目录未更新，可执行 **`kwiki-cli setup`**（逻辑在 `scripts/setup.js`，支持 `--global`、`--target` 等）。

---

## 常用工作流

> 详细流程与命令示例参见 [`references/workflow.md`](references/workflow.md)。

| 工作流 | 说明 | 核心命令 |
|---|---|---|
| 上传本地文件到知识库 | 常规文件 `file-upload`，Markdown 默认转智能文档 `file-convert` | `file-upload` / `file-convert` |
| 重命名文件或文件夹 | 通过 `kuid` 直接定位并重命名 | `file-rename` |
| 下载知识库文件到本地 | 推荐 `file_base64` 模式；OTL 用 `file-content` 取正文 | `file-download` / `file-content` |
| 把文件放到知识库 | 自动识别来源（本地/网页/云盘），选择上传/转换/导入 | `file-upload` / `file-convert` / `file-import` |
| 查找知识库内的文件 | `file-list` 遍历 + Agent 侧关键词过滤 | `file-list` |
| 智能问答与意图路由 | Agentic RAG：明确意图直接问答，模糊意图先 `file-list` 再降级 `knowledge-view-ask` | `file-list` / `knowledge-view-ask` |
| 整理分类知识库 | 遍历 → 拟方案 → 用户确认 → 批量创建文件夹并移动 | `file-create` / `file-move` / `file-delete` |
| 双库一键融合 | 跨库移动文件，处理同名冲突 | `file-move` |
| 资料归档与合并 | 移动文件到归档目录，可选关闭旧库 | `file-move` / `knowledge-view-close` |
| 知识定期归档管理 | 按时间筛选过期文件，移入归档文件夹 | `file-list` / `file-move` |
| 清理知识库无用文件 | 筛选 → 确认 → 删除（进回收站 7 天可恢复） | `file-delete` |
| 获取知识库分享链接 | 获取知识库的外部分享链接 | `knowledge-view-share-link` |
| 修改知识库基础配置 | 修改名称、简介、封面 | `knowledge-view-update` |

---

## 详细参考文档

`references/` 目录按主题拆分了详细参考，执行对应场景时按需加载，避免一次性读取过多内容。

| 文件 | 何时加载 |
|---|---|
| [`references/workflow.md`](references/workflow.md) | 执行知识库操作时加载。包含每个工作流的触发示例、完整命令链、决策分支与通用规则 |
