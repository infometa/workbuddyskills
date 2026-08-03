# kwiki-cli 常见工作流

本文档描述 Agent 在处理用户知识库操作请求时的常见工作流，包含完整的 `kwiki-cli` 命令链和决策逻辑。

> 所有命令均为 `kwiki-cli kwiki <tool> [flags]` 形式，只接受 flag，不接受位置参数。

---

### 上传本地文件到知识库

**触发示例**：「把本地 XX 文件归档/上传/同步/放到 XX 库的 XX 文件夹」「把这些资料归档/上传/同步/放到 XX 库」

**流程**：

1. **获取知识库标识**：用户**精确提供**了完整知识库名称时，调用 `knowledge-view-get --name "准确名称"` 直接获取；仅提供**模糊关键词**或未指定时，调用 `knowledge-view-list --keyword "关键词"` 检索，若有多个结果则列出后询问用户
2. 如需放入子文件夹：
   - `file-list --kuid <知识库kuid>` 定位目标文件夹，获取其 `kuid`
   - 放入根目录则不传 `--parent-link-id`
3. 按文件类型选择上传方式：

**常规文件（docx/pdf/pptx/xlsx 等）**：

```bash
kwiki-cli kwiki file-upload --drive-id <知识库drive_id> --parent-link-id <目标文件夹link_id> --file ./本地文件
```

**Markdown 文件（.md）**：

> 默认转为在线智能文档，保留格式和结构化内容。仅当用户明确要求"上传并保持 md 格式"时，才使用 `file-upload` 直接上传原始 `.md` 文件。

- 读取本地 `.md` 文件内容
- 一步完成创建智能文档并写入内容：

```bash
kwiki-cli kwiki file-convert --kuid <知识库kuid> --title "文件名（不含后缀）" --content "<markdown原文>"
# 返回含 file_kuid / file_link_id / file_id / file_name；取正文（可能需轮询至有内容）：
kwiki-cli kwiki file-content --kuid <file_kuid>
```

- 从 `file-list` 返回中获取 `kuid`，拼接在线链接 `https://www.kdocs.cn/wiki/l/<kuid>`

---

### 重命名知识库内的文件或文件夹

**流程**：

1. `knowledge-view-get --name "知识库名"` 获取知识库的 `kuid`
2. `file-list --kuid <知识库kuid>` 定位目标文件，获取文件/文件夹的 `kuid`
3. 执行重命名：

```bash
kwiki-cli kwiki file-rename --kuid <文件kuid> --title "新名称"
```

> CLI 版 `file-rename` 直接使用文件的 `kuid` 定位，无需 `drive_id` 或 `file_id`。
> 文件须带后缀（如 `"新报告.docx"`），文件夹不带后缀（如 `"项目资料"`）。

---

### 下载知识库文件到本地

**流程**：

1. `file-list --kuid <目标目录kuid>` 定位目标文件，获取 `kuid`、`title`、`doc_type`
2. 下载文件（推荐 `file_base64`）：

```bash
kwiki-cli kwiki file-download --kuid <文件kuid> --response-type file_base64
```

3. **Agent 侧执行分发**：
   - `file_base64` 模式：CLI 返回 base64 内容，Agent 可直接写入本地文件
   - `download_link` 模式：获取下载链接后，调用 `curl -L -o "文件名" "<download_url>"` 下载（注意 `download_link` 常需 `wps_sid` 才能访问，推荐优先用 `file_base64`）
   - 如无本地执行权限，向用户输出下载链接或完整 `curl` 命令

> **注意**：
> - **OTL 智能文档**（`doc_type` 为 `o`）**不支持**通过 `file-download` 下载，会返回业务错误。需取正文时用 `file-content --kuid <文件kuid>`。
> - 如遇受保护文件（SecureDocumentError / forbidProtectedFile），所有导出接口均无法操作，需提示用户。

---

### 把文件放到知识库

**触发示例**：「帮我把 XX 放到 XX 知识库」「把这些文件归档到 XX 库的 XX 文件夹」「帮我把本地文件放到 XX 库」「把公众号文章存入 XX 知识库」「把这个链接存到知识库里」

**流程**：

1. **定位知识库**：用户精确提供库名 → `knowledge-view-get --name "..."` ；仅提供模糊关键词或未指定 → `knowledge-view-list --keyword "..."` 检索，多结果时列出询问用户，零结果时引导创建
2. **定位目标路径**：指定文件夹 → `file-list` 逐层查找，不存在则创建：

```bash
kwiki-cli kwiki file-create --doc-type folder --kuid <父级kuid> --title "文件夹名"
```

未指定 → 根目录

3. **按来源选择归档方式**：
   - **本地文件/文件夹** → 按「上传本地文件到知识库」流程逐个上传，保持子目录结构时递归创建文件夹
   - **网页内容** → 先用 `web_fetch`、`web_search` 或浏览器抓取网页内容转为 Markdown，再转为智能文档存入知识库：

```bash
kwiki-cli kwiki file-convert --kuid <知识库kuid> --title "页面标题" --content "<markdown内容>"
```

   - **云盘已有文件** → 导入到知识库：

```bash
kwiki-cli kwiki file-import --kuid <知识库kuid> --action copy --file-id <云文档fileId>
# 或创建快捷方式
kwiki-cli kwiki file-import --kuid <知识库kuid> --action shortcut --file-id <云文档fileId>
```

4. **确认结果**：`file-list` 返回存放路径与直达链接；批量时展示成功/失败明细

---

### 查找知识库内的文件

**触发示例**：「帮我找一下 XX 文件」「在 XX 库里找 XX 相关的资料」「我要找关于 XX 的文档」

**流程**：

1. **提取条件**：从用户指令中识别关键词、指定库名、文件类型等筛选条件
2. **定位搜索范围**：
   - 精确指定库名 → `knowledge-view-get --name "..."` 确认库存在，获取 `kuid`
   - 模糊关键词或未指定 → `knowledge-view-list --keyword "..."` 检索，多结果时列出询问用户
3. **遍历文件列表**：

```bash
kwiki-cli kwiki file-list --kuid <知识库kuid>
```

如需递归子文件夹，继续用文件夹 `kuid` 调用 `file-list`

4. **Agent 侧过滤**：按用户关键词匹配 `title`，按 `doc_type` 过滤文件类型
5. **返回结果**：展示文件名、类型、创建时间、直达链接（`https://www.kdocs.cn/wiki/l/<kuid>`）；结果过多时提示用户按文件类型或时间范围二次筛选
6. **展示结果并询问用户** → 展示文件信息 + **主动询问是否下载到本地或打开查看（提供在线链接）**

- `file-list` 返回的 `kuid` 可用于 `file-download` 获取文件内容
- 根据文件类型选择下载方式，详见「下载知识库文件到本地」流程

---

### 整理分类知识库

**触发示例**：「帮我整理一下 XX 知识库」「把 XX 库里的文件按类型分类」

> ⚠️ **场景识别**：当用户明确提到「知识库」「库」「资料库」等关键词时，优先使用 `kwiki-cli kwiki` 系列命令完成整理/分类。

**流程**：

1. `knowledge-view-list --keyword "库名"` 搜索目标知识库，获取 `drive_id`、`kuid`
2. `file-list --kuid <知识库kuid>` 遍历根目录内容；如需递归遍历子文件夹，继续用文件夹的 `kuid` 调用 `file-list`。收集每个文件的 `kuid`、`title`、`doc_type` 信息
3. 列出需新建的分类文件夹、文件移动目标、建议删除的内容，明确标注操作影响范围，**提交用户确认后再执行**
4. 批量操作：

```bash
# 创建分类文件夹
kwiki-cli kwiki file-create --doc-type folder --kuid <知识库kuid> --title "分类名"

# 移动文件到分类文件夹
kwiki-cli kwiki file-move --drive-id <源drive_id> --dest-drive-id <目标drive_id> --space-kuid <知识库kuid> --file-kuid <文件kuid>

# 删除确认的冗余内容（进入回收站，7 天内可恢复）
kwiki-cli kwiki file-delete --kuid <文件kuid>
```

---

### 双库一键融合

**触发示例**：「把 XX 库的资料同步到 XX 库」「合并这两个知识库」「把 A 库和 B 库合并」

**流程**：

1. `knowledge-view-list` 查询源库和目标库，获取各自的 `drive_id`、`kuid`
2. `file-list --kuid <源库kuid>` 盘点源库全部文件
3. `file-list --kuid <目标库kuid>` 盘点目标库，检查是否有同名文件冲突
4. **向用户展示合并方案**：列出待移动文件清单及同名冲突处理策略（跳过 / 覆盖 / 重命名），**等待确认**
5. 跨库批量移动：

```bash
kwiki-cli kwiki file-move \
  --drive-id <源库drive_id> \
  --dest-drive-id <目标库drive_id> \
  --space-kuid <源库kuid> \
  --file-kuid <文件1_kuid> \
  --file-kuid <文件2_kuid>
```

> `--dest-parent-id` 不传则移动到目标库根目录。

6. `file-list --kuid <目标库kuid>` 验证文件已到达目标库

---

### 资料归档与合并

**触发示例**：「帮我把 XX 的知识库归档到 XX 库」「把 A 的资料合并到团队库 B」「归档 A 库并关闭」

**流程**：

1. `knowledge-view-get` 分别查询待归档库和目标库的详情
2. `file-list` 分别盘点两个库的文件，识别重复内容
3. 在目标库创建归档文件夹：

```bash
kwiki-cli kwiki file-create --doc-type folder --kuid <目标库kuid> --title "XX归档"
```

4. `file-list --kuid <目标库kuid>` 获取归档文件夹的 `kuid`
5. `file-move` 将待归档库的全部文件/文件夹跨库移入归档目录
6. （如有重复）`file-delete` 清理重复文件
7. **向用户确认后**关闭旧库：

```bash
kwiki-cli kwiki knowledge-view-close --kuid <旧库kuid>
```

8. `file-list --kuid <归档文件夹kuid>` 验证归档完整

> ⚠️ 关闭知识库不可恢复，必须向用户二次确认。

---

### 知识定期归档管理

**触发示例**：「每季度归档一次 XX 库的旧文件」「把 3 个月未修改的文件归档」

**流程**：

1. `knowledge-view-get --name "..."` 定位目标知识库
2. `file-list --kuid <知识库kuid>` 遍历全库文件，收集 `kuid`、`title`、`ctime`
3. Agent 按 `ctime` 筛选：早于归档阈值（如 3 个月前）的文件列入归档清单
4. 创建时间维度归档文件夹：

```bash
kwiki-cli kwiki file-create --doc-type folder --kuid <知识库kuid> --title "YYYY-QN归档"
```

5. `file-list --kuid <知识库kuid>` 获取新文件夹的 `kuid`
6. `file-move` 将过期文件移入归档文件夹
7. `file-list --kuid <归档文件夹kuid>` 验证归档结果

---

### 清理知识库无用文件

**触发示例**：「清理 XX 库里 1 个月未修改的文件」「删掉 XX 库里的空文件夹」

**流程**：

1. `file-list --kuid <空间kuid>` 递归遍历全库，获取每个文件/文件夹的 `kuid`、`title`、`doc_type`、`ctime`
2. Agent 按 `ctime` 或用户指定条件筛选待删除文件
3. **向用户展示待删除清单并确认**
4. 逐个删除（进入回收站，7 天内可恢复）：

```bash
kwiki-cli kwiki file-delete --kuid <文件kuid>
```

5. 空文件夹可同样通过 `file-delete` 删除

---

### 获取知识库分享链接

**触发示例**：「给我一个 XX 库的分享链接」「把 XX 库的二维码给我」「分享 XX 知识库」

**流程**：

1. **定位知识库**：用户精确提供库名 → `knowledge-view-get --name "知识库名"`；模糊关键词 → `knowledge-view-list --keyword "关键词"` 检索
2. **获取分享链接**：

```bash
kwiki-cli kwiki knowledge-view-share-link --kuid <知识库kuid>
```

3. **展示结果**：向用户返回分享链接和二维码图片

---

### 知识库智能问答与意图自适应路由（Agentic RAG）

**触发示例**：「在 XX 库里找关于"XX政策"的信息」「总结一下 XX 方案」「问下知识库关于 XX」「帮我找下 XX 库的 XXX」

**流程（按意图类型分流）**：

#### 路径 A：明确问答意图（直接走 RAG）

当用户明确表达提问/总结/查找知识意图时（如"总结一下 XX"、"问下知识库 XX"、"XX 的规定是什么"）：

1. **定位知识库（可选）**：若用户指定了特定知识库，`knowledge-view-get --name "知识库名"` 或 `knowledge-view-list --keyword "关键词"` 获取 `kuid`
2. **执行智能问答**：

```bash
# 在指定知识库问答
kwiki-cli kwiki knowledge-view-ask --input "用户问题" --kuid <知识库kuid>

# 全库问答（不指定 --kuid）
kwiki-cli kwiki knowledge-view-ask --input "用户问题"
```

3. **深度与联网调度**：Agent 在调用 `knowledge-view-ask` 时，按以下顺序判断参数：
   
- **联网搜索 (`--web-search`)**  
   默认 **关闭**，优先仅从知识库中查找答案。  
   只有在知识库返回空结果、明显不相关或信息不足以回答问题时，Agent 才自动追加 `--web-search` 进行联网搜索。
     
- **深度思考 (`--switch-thinking`)**  
   由 Agent 根据问题复杂度自主决定是否开启
     
```bash
# 基础查询（不联网，不深度思考）
kwiki-cli kwiki knowledge-view-ask --input "用户问题"

# 知识库无结果，补上联网搜索，同时根据问题复杂度决定是否深度思考
# 仅当需要深度思考时才加 --switch-thinking
kwiki-cli kwiki knowledge-view-ask --input "用户问题" --web-search --switch-thinking
```

4. **组织回答**：基于问答结果组织总结结构，**严格附带引用来源**（来源文件名 + 完整链接：`https://www.kdocs.cn` + `source.url`）

#### 路径 B：模糊意图 — 元数据优先，RAG 兜底

当用户意图不明确时（如"帮我找下 XX 库的 XXX"、"查一下 XX"），遵循**「元数据优先，RAG 兜底」**原则：

1. **定位知识库**：`knowledge-view-get --name "知识库名"` 或 `knowledge-view-list --keyword "关键词"` 获取 `kuid`
2. **先调用 `file-list`** 进行标题级模糊匹配：

```bash
kwiki-cli kwiki file-list --kuid <知识库kuid>
```

Agent 侧按用户关键词匹配返回结果的 `title` 字段

3. **分支判断**：
   - **若命中文件** → 优先展示文件信息（名称、类型、链接 `https://www.kdocs.cn/wiki/l/<kuid>`），并辅以快捷追问：
     - "是否需要针对这个问题进行问答？"
     - "是否需要下载该文件？"
   - **若 `file-list` 无结果** → 判定用户查找的是正文细节内容，**无缝降级**至智能问答：

```bash
kwiki-cli kwiki knowledge-view-ask --input "原始问题"
```

4. **输出**：问答结果必须提取答案并附带【来源出处】（来源文件名 + 链接：`https://www.kdocs.cn` + `source.url`）

---

### 修改知识库基础配置

```bash
# 修改名称
kwiki-cli kwiki knowledge-view-update --kuid <kuid> --name "新名称"

# 修改简介
kwiki-cli kwiki knowledge-view-update --kuid <kuid> --desc "新简介"

# 修改封面
kwiki-cli kwiki knowledge-view-update --kuid <kuid> --cover-img "https://example.com/cover.png"
```

---

## 通用规则

以下规则适用于所有工作流：

1. **知识库查询优先**：任何涉及知识库的操作，第一步始终是获取知识库标识。用户精确提供了完整库名时用 `knowledge-view-get --name "..."`，仅有模糊关键词或未指定时用 `knowledge-view-list --keyword "..."` 检索，再由 Agent 按 `space_name` 进行名称匹配。
2. **模糊匹配多结果**：`knowledge-view-list` 返回多个匹配时，列出名称、简介、创建时间，询问用户选择。超过 5 条折叠分页。
3. **零匹配处理**：用户指定了知识库名称但列表中无任何 `space_name` 包含该关键词时，告知用户"未找到名为 XX 的知识库，是否为您创建？"。**严禁在此场景下列出其他不相关知识库供选择。**
4. **创建前必须确认（强制）**：调用 `knowledge-view-create` 或 `file-create` 创建知识库/文件夹**之前**，必须先向用户说明即将创建的内容并等待用户明确确认。**严禁跳过确认直接创建。** 此规则适用于所有创建场景，包括但不限于：目标知识库不存在需新建、已有知识库状态异常需重建、需要新建分类文件夹等。
5. **分类方案必须确认（强制）**：涉及文件分类上传时，Agent 拟定或用户指定的分类方案必须以表格形式完整展示，**等待用户明确回复确认后**才能开始创建文件夹和上传文件。严禁展示方案后在同一轮对话中直接执行。
6. **上传后验证**：上传完成后，调用 `file-list` 验证文件是否出现在目标位置。
7. **进度反馈**：批量操作时逐个反馈进度，不要静默等待全部完成。
8. **错误恢复**：单个文件上传失败不应中断整个流程，记录失败项，全部完成后汇总告知用户。
9. **链接输出规范**：拼接完整链接时**必须使用 `https://www.kdocs.cn` 作为域名**，文件链接格式为 `https://www.kdocs.cn/wiki/l/<kuid>`。严禁使用 `zhishi.wps.cn` 或其他域名拼接用户可访问的链接。
10. **CLI 命令格式**：所有 `kwiki-cli kwiki <tool>` **只接受 flag**，不接受位置参数。多值参数通过重复 flag 传入（如 `--file-kuid f1 --file-kuid f2`、`--file-id id1 --file-id id2`）。
11. **ID 字段使用规范（强制）**：CLI 版接口已简化 ID 体系，大部分操作统一使用 `kuid`：
    - `file-rename`、`file-delete`、`file-download`、`file-content`：使用文件的 `kuid`（`0l` 开头）
    - `file-list`、`file-create`、`file-convert`：使用知识库 `kuid`（`0s` 开头）或文件夹 `kuid`（`0l` 开头）；`file-convert` 成功返回的 `file_kuid` 可用于后续文件操作
    - `file-upload`：使用 `drive_id` + 可选 `parent_link_id`
    - `file-move`：需要 `drive_id`、`dest_drive_id`、`space_kuid`、`file_kuid`
    - `file-import`：使用知识库/文件夹 `kuid` + 云文档 `file_id`
    - `knowledge-view-close`：使用知识库 `kuid`（`0s` 开头）
12. **同名文件冲突处理**：在执行上传（`file-upload`）、新建（`file-create`）或重命名（`file-rename`）遇到同名冲突报错时，Agent 应在文件名后自动追加数字（如 `文件名(1)`）进行重试，或向用户询问是否需要覆盖原始文件。
13. **空结果处理**：在调用 `file-list` 进行文件查找时，若返回结果为空，Agent 应明确告知用户"该目录下未找到符合条件的文件"，并主动建议用户更换搜索关键词或检查知识库名称。
14. **OTL 下载限制**：OTL 智能文档（`doc_type` 为 `o`）不支持通过 `file-download` 下载，调用会返回业务错误。需取正文时用 `file-content`。
15. **file-convert 异步可见性**：md→otl 返回 `file_kuid` 后，正文/size 可能约 1–2 分钟才就绪；用 `file_kuid` 轮询 `file-content`，勿仅凭 size 判断内容丢失。
15. **dry-run 预览**：对高风险写操作（删除、移动、关闭知识库等），可先加 `--dry-run` 预览计划再执行：

```bash
kwiki-cli --dry-run kwiki file-delete --kuid <kuid>
kwiki-cli --dry-run kwiki knowledge-view-close --kuid <kuid>
```

16. **输出格式**：需要人类阅读时加 `--format pretty` 美化 JSON 输出；程序消费时用默认 `json`。`knowledge-view-ask` 默认将流式 `answer_citations[].text` 拼接为完整答案后输出 JSON；原始 SSE 加 `--stream`。
