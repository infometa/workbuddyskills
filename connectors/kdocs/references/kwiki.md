# 个人知识库（kwiki）工具完整参考文档

本文件说明金山文档 Skill 中个人知识库相关的 `kwiki.*` 工具如何使用。它们面向"知识库空间"和"知识库内资料管理"场景，适合创建知识库、浏览库内目录、导入已有云文档，以及整理知识库中的文件和文件夹。

## 通用说明

### 何时使用 `kwiki.*`

- 需要新建一个个人知识库或资料库空间
- 需要查询已有知识库列表，或按名称/ID 获取某个知识库详情
- 需要浏览知识库根目录或某个知识库文件夹下的资料
- 需要把**已有云文档**导入知识库
- 需要在知识库里新建文件夹或在线文件，并对库内资料做删除、下载
- 仔细阅读接口参数说明，不猜测，不胡编乱造

### 特别说明

> - 仔细阅读接口参数说明，不猜测，不胡编乱造

> - 本地上传不走 `kwiki.*`

### 链接输出规范

接口返回的数据中，`url` 字段为**相对路径**（如 `/l/xxx?source=kmwiki` 或 `/wiki/l/xxx`），`kuid`字段为**知识库/文件夹/文件id**。**Agent 在拼接完整链接时，必须遵循以下规则，不猜测：**

1. **拼接规则**：`https://www.kdocs.cn` + `data.url 原值`。
2. **手动构造**：若接口未返回 `url` 但返回了 `kuid`，格式为 `https://www.kdocs.cn/wiki/l/${kuid}`。

### 标识说明

在 `kwiki.*` 场景里，常见会用到以下标识：

- `drive_id`: 知识库对应的云盘 ID
- `group_id`: 知识库所属组 ID
- `kuid`: 知识库或知识库内文件/文件夹的标识

经验上：

- 知识库本身的 `kuid` 常见为 `0s...`
- 知识库内文件夹/文件的 `kuid` 常见为 `0l...`

如果用户只给了知识库名称，通常先用 `kwiki.list_knowledge_views` 搜，再把返回的 `drive_id` / `group_id` / `kuid` 传给后续工具。

> **注意**： `kuid` 仅用于 kwiki 专属操作（`delete_item`/`import_cloud_doc` 等）。

---

## 一、知识库空间

> 知识库空间的创建、查询、更新、关闭

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`kwiki.create_knowledge_view`](kwiki/create_knowledge_view.md) | 创建个人知识库 | `space_name`, `status` |
| [`kwiki.list_knowledge_views`](kwiki/list_knowledge_views.md) | 查询知识库列表 |  |
| [`kwiki.get_knowledge_view`](kwiki/get_knowledge_view.md) | 获取单个知识库详情 | `drive_id`\|`name` |
| [`kwiki.update_knowledge_view`](kwiki/update_knowledge_view.md) | 修改知识库基础配置 | `drive_id`, `cover_img`, `status` |
| [`kwiki.close_knowledge_view`](kwiki/close_knowledge_view.md) | 关闭（删除）知识库 | `drive_id` |

## 二、库内资料

> 空间内文件夹与文件的浏览、创建、删除、从云盘导入

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`kwiki.list_items`](kwiki/list_items.md) | 列出知识库目录下的内容 | `kuid` |
| [`kwiki.import_cloud_doc`](kwiki/import_cloud_doc.md) | 将已有云文档导入知识库 | `kuid`, `file_infos` |
| [`kwiki.create_item`](kwiki/create_item.md) | 在知识库中创建文件或文件夹 | `doc_type`, `kuid`, `title` |
| [`kwiki.delete_item`](kwiki/delete_item.md) | 删除知识库中的文件或文件夹 | `kuid` |

## 常用工作流

#### 上传本地文件到知识库

**触发示例**：「把本地 XX 文件归档/上传/同步/放到 XX 库的 XX 文件夹」「把这些资料归档/上传/同步/放到 XX 库」「定时归档/上传/同步/放 XX 到 XX 库」

**流程**：
1. `kwiki.get_knowledge_view` 或 `kwiki.list_knowledge_views` 获取目标知识库的 `drive_id`
2. 如需放入子文件夹：
   - `kwiki.list_items` 定位目标文件夹，获取其 `kuid`（用于 kwiki 操作）和 `file_id`（用于通用接口的 `parent_id`）
   - 放入根目录则 `parent_id="0"`
3. 按文件类型选择上传方式：

**常规文件（docx/pdf/pptx/xlsx 等）**：
`upload_file(drive_id=知识库drive_id, parent_id=目标文件夹id, name="文件名.docx", content_base64=...)`

**Markdown 文件（.md）**：
> 默认转为在线智能文档，保留格式和结构化内容。仅当用户明确要求"上传并保持 md 格式"时，才使用 `upload_file` 直接上传原始 `.md` 文件。

- `kwiki.create_item(doc_type="o", kuid=目标文件夹kuid, title="文件名（不含后缀）")` 创建智能文档
- 读取本地 `.md` 文件内容
- `otl.insert_content(file_id=新文档的file_id, content=markdown原文, format="markdown", mode="prepend")` 将 markdown 写入智能文档
  - 如果内容过长（>3000 字符），分段写入：首段用 `mode="prepend"`，后续段用 `mode="append"` 追加
- 从 `kwiki.list_items` 返回中获取 `link_id`，拼接在线链接

#### 重命名知识库内的文件或文件夹

使用通用接口 `rename_file` 重命名知识库内的文件或文件夹：

1. `kwiki.get_knowledge_view(name="知识库名")` 获取知识库的 `drive_id` 和 `kuid`
2. `kwiki.list_items(kuid=知识库kuid)` 定位目标文件，获取 `file_id` 和 `drive_id`
3. `rename_file(drive_id=drive_id, file_id=file_id, dst_name="新名称")`
   - 文件须带后缀（如 `"新报告.docx"`）
   - 文件夹不带后缀（如 `"项目资料"`）

#### 下载知识库文件到本地

**流程**：

1. `kwiki.list_items(kuid=目标目录kuid)` 定位目标文件，获取 `file_id`、`link_id`、`drive_id`
2. 根据文件类型选择下载方式：

**普通文件（docx/pptx/pdf/图片等）**：
1. 使用 `wps.export` 等导出工具获取带签名的下载 URL（`link_id` 来自 `kwiki.list_items`）
2. `curl.exe -L -o "文件名" "签名URL"` 下载

**智能文档（doc_type="o"）**：`wps.export` 不支持直接导出，无特殊情况，默认转换成Markdown格式：
- **Markdown** → `read_file_content(drive_id, file_id, format="markdown")`（异步，需轮询 task_id），将返回的 markdown 内容保存为 `.md` 文件

**快捷方式文件（type="shortcut"）**：通过 `search_files` 搜索原始文件名找到源文件，再用源文件的 `link_id` 走上述通用流程。

> 注意：`download_file` 返回的 URL 需登录态，无法直接 curl。始终优先使用 `wps.export` 获取带签名的下载 URL。受保护文件（SecureDocumentError / forbidProtectedFile）所有导出接口均无法操作，需提示用户。

#### 把文件放到知识库

**触发示例**：「帮我把 XX 放到 XX 知识库」「把这些文件归档到 XX 库的 XX 文件夹」「帮我把本地 XX 文件夹的文件放到 XX 库里面」「帮我把 XX 网页的文章放到知识库」

**流程**：

1. **定位知识库**：指定库名 → `kwiki.get_knowledge_view(name=...)`；未指定 → `kwiki.list_knowledge_views` 推荐或引导创建
2. **定位目标路径**：指定文件夹 → `kwiki.list_items` 逐层查找，不存在则 `kwiki.create_item(doc_type="folder")` 按层级创建；未指定 → 根目录
3. **归档**：
   - 本地文件/文件夹 → 按「上传本地文件到知识库」流程逐个上传，保持子目录结构时递归创建文件夹
   - 网页 → `scrape_url` + `scrape_progress` 轮询完成后，`move_file` 移入目标库
   - 云盘已有文件 → `kwiki.import_cloud_doc(action="copy"/"shortcut")`
4. **确认结果**：`kwiki.list_items` 返回存放路径与直达链接；批量时展示成功/失败明细

#### 查找知识库内的文件

**触发示例**：「帮我找一下 XX 文件」「在 XX 库里找 XX 相关的资料」「我要找关于 XX 的文档」

**流程**：

1. **提取条件**：从用户指令中识别关键词、指定库名、文件类型等筛选条件
2. **定位搜索范围**：
   - 指定库 → `kwiki.get_knowledge_view(name=...)` 确认库存在，获取 `drive_id`
   - 未指定库 → `kwiki.list_knowledge_views` 获取全量知识库列表
3. **执行搜索**：`search_files(keyword="关键词", type="all", drive_ids=[目标drive_id列表])` 跨库或指定库检索
4. **返回结果**：按匹配度排序，展示文件名、所在库/路径、修改时间、直达链接；结果过多时提示用户按文件类型或时间范围二次筛选
5. **展示结果并询问用户** → 展示文件信息 + **主动询问是否下载到本地或打开查看（提供在线链接）用户选择下载时的后续操作**：

- `search_files` 返回的 `file_id` 可直接用于 `read_file_content` 等通用接口
- 根据文件类型选择下载方式，详见「下载知识库文件到本地」流程

#### 整理分类知识库

**触发示例**：「帮我整理一下 XX 知识库」「把 XX 库里的文件按类型分类」

> ⚠️ **场景识别**：当用户明确提到「知识库」「库」「资料库」等关键词时，优先使用 `kwiki.*` 系列接口完成整理/分类，确保知识库内部元数据（索引、搜索等）一致。

**流程**：

1. `kwiki.list_knowledge_views(keyword="库名")` 搜索目标知识库，获取 `drive_id`、`group_id`、`kuid` 等关键标识
2. `kwiki.list_items(kuid=知识库kuid)` 遍历根目录内容；如需递归遍历子文件夹，继续用文件夹的 `kuid` 调用 `kwiki.list_items`。收集每个文件的 `kuid`、`title`、`doc_type` 信息
3. 列出需新建的分类文件夹、文件移动目标、建议删除的内容，明确标注操作影响范围，**提交用户确认后再执行**
4. 批量创建文件夹（`kwiki.create_item`）→ 批量移动文件（`move_file`）→ 删除确认的冗余内容（`kwiki.delete_item`），提示回收站恢复路径（7 天内可恢复）

#### 清理知识库无用文件

**触发示例**：「清理 XX 库里 1 个月未修改的文件」「删掉 XX 库里的空文件夹」「把 XX 库里过期的资料清理一下」

**流程**：

1. `kwiki.list_items(kuid=空间kuid)` 递归遍历全库，获取每个文件/文件夹的 `kuid`、`file_id`、`title`、`doc_type`、`ctime`
2. **如需按修改时间筛选**：用 `list_files(drive_id=知识库drive_id, parent_id=父目录file_id, page_size=500, order_by="mtime")` 获取 `mtime`，通过 `file_id` 匹配到 `kuid`
3. **向用户展示待删除清单并确认**
4. `kwiki.delete_item(kuid=xxx)` 逐个删除（进入回收站，7 天内可 `restore_deleted_file` 恢复）
5. 空文件夹可同样通过 `kwiki.delete_item` 删除

#### 网页内容存入知识库

> **触发示例**：「把公众号文章存入XX知识库」「把这个链接存到知识库里」

**流程**
1. 主流程：scrape_url → scrape_progress(status=1) → move_file → get_file_link
2. 降级流程（scrape_url 失败/status=-1，如公众号等 JS 渲染页面）：
   browser 抓取正文 → create_file(name=xxx.docx)
   → upload_file(drive_id=xxx parent_id=0 file_id=xxx content_format=markdown content_base64=xxx)
   → move_file → get_file_link

| 注意 | 说明 |
|------|------|
| upload_file 必填参数 | `drive_id` 和 `parent_id` 必须显式传递 |
| ID 体系 | kwiki 内部 kuid 需通过 `kwiki.list_items` 获取 |

## 错误速查表

> ⛔ **强制规则**：命中下方任一错误条目时，**必须立即按「处理方式」向用户提示，禁止尝试其他接口绕过或反复重试。**

| 错误特征 | 原因 | 处理方式 |
|----------|------|----------|
| `code: 403000006`，`msg: "当前版本仅支持个人用户"` | 当前登录的是企业/团队账号，该知识库接口仅对个人账号开放 | 提示用户切换至个人账号后重试 |
