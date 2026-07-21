# AI 文档生成演示文稿

> 文档生成 PPT 标准链路：创建会话、解析文档、生成大纲、美化风格与生成上传

**适用场景**：用户已有一份文档（金山文档链接 / file_id / 本地上传文件），希望基于文档内容自动生成可编辑的云端演示文稿

**触发词**：文档转PPT、文件转PPT、文档生成PPT、把文档做成PPT、根据文档生成演示文稿

**工具链**：`aippt.doc_create_session` → `aippt.doc_outline_options` → `aippt.doc_outline` → `aippt.doc_beautify` → 本地格式转换 → `aippt.doc_generate_ppt` → `upload_file` → `get_file_link`

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `search_files` / `get_share_info` | drive | 定位用户指定的文档，获取 `file_id`（非链接场景） |
| `aippt.doc_create_session` | aippt | 创建文档转 PPT 的 AI 会话，返回 `session_id` |
| `aippt.doc_outline_options` | aippt | 将文档标识传入，服务端自动解析文档，返回用户确认问题（制作目标、受众等） |
| `aippt.doc_outline` | aippt | 根据用户确认结果（`resume_info` + `checkpoint_id`）生成完整 Markdown 大纲 |
| `aippt.doc_beautify` | aippt | 为大纲生成全局风格（theme / global_style）和逐页 `design_style` |
| `本地格式转换` | 本地 | 将 `03_outline.md` + `04_beautify.json` 合并转换为 `{topic, outlines[]}` 结构 |
| `aippt.doc_generate_ppt` | aippt | 接收 `{topic, outlines[]}` 生成最终 PPTX，返回 `merged_url` |
| `upload_file` | drive | 将生成的 PPTX 上传为云文档 |
| `get_file_link` | drive | 获取最终云文档在线链接 |

## 执行流程

> 该流程对应「文档生成 PPT」标准链路。文档内容**不需要预先读取**，通过 `file_id` 或 `v7_file_id`（从链接提取的 `link_id`）传入后服务端会自动解析。
>
> 文档链路与主题链路的**最终生成步骤完全一致**：都需要先做本地格式转换得到 `{topic, outlines[]}`，再调用 `aippt.doc_generate_ppt`（底层与 `aippt.theme_generate_html_pptx` 相同）。
>
> 若通过 `mcporter` 调用本流程中的步骤，请为**每一步**单独设置超时时间为 **3000 秒**。11 页以上的 PPT 生成可能需要 8-10 分钟。
>
> 所有中间文件必须写入会话专属临时目录 `$AIPPT_WORK_DIR/`，详见 `references/aippt_references.md` 中「临时文件管理」章节。

```
步骤 0: 初始化会话工作目录
        → conversation_id 获取方式（按优先级）：
          1. 从 Agent 运行时上下文获取对话标识（如 VS Code Copilot 从模板变量 VSCODE_TARGET_SESSION_LOG 路径末段提取 UUID）
          2. 若当前环境无可用对话标识，则调用系统 UUID 生成器（如 PowerShell: [guid]::NewGuid()；bash: uuidgen）
        → **禁止**使用自定义名称、缩写或硬编码字符串代替 conversation_id
        → 目录名格式固定为 kdocs_aippt_<conversation_id>
        → 在 OS 临时目录下创建该子目录
        → 记录路径为 $AIPPT_WORK_DIR
        → 同时清理超过 24 小时的残留 kdocs_aippt_* 目录

步骤 1: aippt.doc_create_session()
        → 创建文档转 PPT 的 AI 会话
        → 返回 session_id
        → 写入 $AIPPT_WORK_DIR/01_session.json

步骤 2: aippt.doc_outline_options(session_id, input=[文本指令, 文档标识引用])
        → 文档标识支持两种 type：
           · type="file_id"：传入数字 file_id（如 "100239253236"）
           · type="v7_file_id"：传入从文档链接提取的 link_id（如 "co4Kyv9Ofayq"）
        → 当用户提供金山文档链接时，直接提取 link_id 作为 v7_file_id 传入，无需先调用 get_share_info
        → 服务端自动解析文档内容
        → 返回结构化 JSON：data.checkpoint_id、data.interrupt_id、data.questions[]
        → questions 包含制作目标（choice）、目标受众（choice）、补充说明（text）等
        → 向用户展示选项并收集回答
        → 写入 $AIPPT_WORK_DIR/02_options.json

步骤 3: aippt.doc_outline(session_id, checkpoint_id, input, resume_info=[用户选择])
        → resume_info 格式：[{type:"follow_up", id:<interrupt_id>, data:{items:[...]}}]
        → items 中每项保持与 questions 相同的结构，选择题填入 options，文本题填入 text_input
        → 服务端根据文档内容 + 用户意图生成完整 Markdown 大纲
        → 返回 data.markdown_outline（完整大纲，可能含重复内容）
        → 也可从 data.assistant_messages 中提取最长的含 {.topic} 和 {.end} 的消息作为清洁版大纲
        → 返回 data.user_intention（后续 beautify 需要）
        → 写入 $AIPPT_WORK_DIR/03_outline.md（清洁后的大纲）
        → 写入 $AIPPT_WORK_DIR/03_extra.json（user_intention 等元数据）

步骤 4: aippt.doc_beautify(topic, outline, user_intention)
        → topic 从大纲 {.topic} 行提取
        → outline 传入清洁后的 Markdown 大纲
        → user_intention 传入上一步返回的 data.user_intention
        → 可选传入 user_input（用户原始输入）和 model（默认 IMAGE_V2）
        → 返回 data.theme、data.global_style、data.slides[]（逐页 design_style）
        → slides[].page_type 为大纲原始类型（title/toc/chapter/text/end）
        → 写入 $AIPPT_WORK_DIR/04_beautify.json

步骤 5: 本地格式转换（纯本地，无网络请求）
        → 输入：$AIPPT_WORK_DIR/03_outline.md + $AIPPT_WORK_DIR/04_beautify.json
        → 将 Markdown 大纲按 --- 分隔符拆分为各页 section
        → 将 beautify.slides[] 按 index 排序，与大纲 section 按页对齐
        → 每页生成 outlines[] 项，包含：
           · title: 从大纲 section 的标题行提取（如"## 封面标题 {.title}"→"封面标题"）
           · content_description: 从大纲 section 的正文内容提取
           · design_style: 从 beautify.slides[i].design_style 取值（默认不合并 global_style）
           · page_type: 将 API 返回的 title/toc/chapter/text/end 映射为 pt_title/pt_contents/pt_section_title/pt_text/pt_end
        → topic 取 beautify.data.theme
        → 输出 {topic, outlines[]} 结构
        → 写入 $AIPPT_WORK_DIR/05_config.json

步骤 6: aippt.doc_generate_ppt(topic, outlines[])
        → 传入步骤 5 输出的 {topic, outlines[]} 结构
        → 与 aippt.theme_generate_html_pptx 底层接口一致
        → SSE 流依次返回：generate_pptx_start → generate_pptx_progress → generate_pptx_result(每页) → generate_pptx_merge_result → generate_pptx_finish
        → 返回 merged_url（合并后的 PPTX 下载链接）+ pages[]
        → 写入 $AIPPT_WORK_DIR/06_ppt_result.json

步骤 7: 下载 merged_url 的 PPTX 二进制
        → Base64 编码

步骤 8: upload_file(drive_id, parent_id, name="<文档名>.pptx", content_base64=...)
        → 新建云端演示文稿

步骤 9: get_file_link(file_id)
        → 返回最终云文档链接
        → 写入 $AIPPT_WORK_DIR/07_cloud_result.json

步骤 10: 清理会话工作目录
         → 递归删除 $AIPPT_WORK_DIR
         → 若步骤 1-9 中任一步失败且无法恢复，也应在报告错误后执行清理
```

## 本地格式转换详解（步骤 5）

### page_type 映射表

| API 返回值（beautify.slides[].page_type） | 转换后 page_type |
|-------------------------------------------|------------------|
| `title` / `cover` | `pt_title` |
| `toc` | `pt_contents` |
| `chapter` | `pt_section_title` |
| `text` / `content` / `section` | `pt_text` |
| `end` / `ending` | `pt_end` |

### 转换输出格式（05_config.json）

```json
{
  "topic": "心怀感恩，拥抱青春",
  "outlines": [
    {
      "title": "心怀感恩，拥抱青春",
      "content_description": "封面页展示主题标题",
      "design_style": "封面页·满版居中偏下布局...",
      "page_type": "pt_title"
    },
    {
      "title": "目录",
      "content_description": "- 感恩父母：养育之恩伴成长\n- 感恩老师：传道授业引前路",
      "design_style": "目录页·左右非对称双栏布局...",
      "page_type": "pt_contents"
    },
    {
      "title": "感谢聆听",
      "content_description": "常怀感恩之心，不负青春韶华",
      "design_style": "结束致谢页·温馨收尾",
      "page_type": "pt_end"
    }
  ]
}
```

### 转换规则

1. **大纲按 `---` 分隔符拆分**为各页 section，跳过 `{.topic}` 标记行（文档级元信息，不是独立幻灯片）
2. **title 提取**：从 section 的 `## 标题内容 {.type}` 行提取标题文字（去掉 `{.type}` 标记）
3. **content_description 提取**：section 中标题行以下的所有正文内容
4. **design_style**：直接取 `beautify.slides[i].design_style`，默认**不合并** `global_style`（可选 `--merge-global` 模式合并）
5. **page_type**：将 `beautify.slides[i].page_type` 按映射表转换
6. **页对齐**：beautify.slides 按 `index` 排序后，与大纲 sections 按顺序一一对应

## 与主题生成链路的差异

| 环节 | 主题生成 PPT | 文档生成 PPT |
|------|-------------|-------------|
| 输入 | 用户一句话主题 | 文档 `file_id`（服务端自动解析） |
| 需求澄清 | `aippt.theme_questions` 返回问卷 | `aippt.doc_outline_options` 返回 questions（choice + text） |
| 联网研究 | `aippt.theme_deep_research` | 无（基于文档内容） |
| 大纲生成 | `aippt.theme_outline` | `aippt.doc_outline`（带 `resume_info` + `checkpoint_id`） |
| 风格美化 | 从 `theme_outline` 流式输出提取 | `aippt.doc_beautify` 独立调用 |
| 本地格式转换 | 需要（大纲 → `{topic, outlines[]}`) | **同样需要**（`03_outline.md` + `04_beautify.json` → `{topic, outlines[]}`） |
| 生成 PPTX | `aippt.theme_generate_html_pptx` | `aippt.doc_generate_ppt`（**底层接口一致**，都接收 `{topic, outlines[]}`) |
| 上传云端 | 相同流程 | 相同流程 |

## 注意事项

- **无需预先读取文档内容**：文档通过 `file_id` 或 `v7_file_id` 直接传入 `aippt.doc_outline_options`，服务端会自动解析
- **链接直传优化**：当用户提供金山文档链接（`kdocs.cn`）时，从 URL 提取 `link_id` 后直接以 `type: "v7_file_id"` 传入，无需先调用 `get_share_info` 获取 `file_id`
- `doc_outline_options` 和 `doc_outline` 通过 MCP 调用后返回结构化 JSON（不需要自行解析 SSE 流）
- `doc_outline` 返回的 `markdown_outline` 可能包含重复内容（大纲出现两次），需要去重处理；建议从 `assistant_messages` 中提取完整且干净的大纲
- `doc_outline` 的 `resume_info` 必须是**数组**，格式为 `[{type:"follow_up", id:<interrupt_id>, data:{items:[...]}}]`
- **本地格式转换是必要步骤**：文档链路和主题链路最终生成接口一致，都需要 `{topic, outlines[]}` 格式
- 生成速度约每页 20-30 秒，11 页 PPT 约需 4-8 分钟，请确保超时设置足够
- 所有中间文件使用 UTF-8 编码，JSON 文件必须通过 `JSON.stringify()` 序列化（禁止手动拼接）
- 上传 PPTX 到云端时必须使用编程 API（`callOnce()`），不可通过 `mcporter call` 命令行（Base64 内容超出 OS 命令行长度限制）
- 详细的 MCP 调用规则、脚本模板和中间文件约定见 `references/aippt_references.md`
