---
name: ppt-gen
description: "创建演示文稿（.pptx）并设置主题字体、配色方案，支持插入幻灯片和导出 PDF/图片。可浏览目录管理 PPT 文件。 当用户要求「做 PPT」、「创建演示文稿」、「创建幻灯片」、「设置 PPT 主题」时使用。 若需要读取或编辑已有文档内容，请使用 doc-to-markdown 或 doc-writer 技能。
"
homepage: 
version: 2.6.4
metadata: {"openclaw":{"category":"kdocs","emoji":"🎨"}}
---

# 主题生成 PPT

主题生成 PPT 技能支持一键创建并美化演示文稿。

> 本技能依赖 `kdocs` 技能的基础文档操作能力（认证、文件管理等），请确保已安装该技能。详见 `references/core/` 目录。

## 严格规则

### 禁止（NEVER）

- 权限不足时禁止重试或绕过，立即告知用户无权限

---

## 能力范围

### 通用工具总览

#### 文档创建与上传
| 工具 | 用途 |
|------|------|
| [`create_empty_file`](references/drive/create_and_upload.md) | 新建空白在线文档 |
| [`scrape_progress`](references/drive/create_and_upload.md) | 查询网页剪藏任务进度 |
| [`scrape_url`](references/drive/create_and_upload.md) | 网页剪藏，抓取网页内容并自动保存为智能文档 |
| [`upload_new_file`](references/drive/create_and_upload.md) | 上传本地文件新建云文档 |
| [`upload_replace_file`](references/drive/create_and_upload.md) | 通过上传本地文件全量覆盖已有云文档 |

#### 文档读取与下载
| 工具 | 用途 |
|------|------|
| [`list_files`](references/drive/read_and_download.md) | 获取指定文件夹下的子文件列表 |
| [`download_file`](references/drive/read_and_download.md) | 获取文件下载信息 |
| [`read_file`](references/drive/read_and_download.md) | 读取文档内容为 Markdown/结构化数据 |

#### 文件组织
| 工具 | 用途 |
|------|------|
| [`move_file`](references/drive/organize.md) | 批量移动文件(夹) |
| [`rename_file`](references/drive/organize.md) | 重命名文件（夹） |

#### 分享与访问
| 工具 | 用途 |
|------|------|
| [`share_file`](references/drive/share.md) | 开启文件分享 |
| [`set_share_permission`](references/drive/share.md) | 修改分享链接属性 |
| [`cancel_share`](references/drive/share.md) | 取消文件分享 |
| [`get_share_info`](references/drive/share.md) | 获取分享链接信息 |
| [`get_file_link`](references/drive/share.md) | 获取文件的云文档在线访问链接 |

#### 搜索
| 工具 | 用途 |
|------|------|
| [`search_files`](references/drive/search.md) | 按关键词搜索云文档（文件/文件夹） |

#### 演示文稿与页面
| 工具 | 用途 |
|------|------|
| [`wpp.insert_slide`](references/wpp/slide.md) | 在已有演示中插入空白页 |
| [`wpp.import_slides`](references/wpp/slide.md) | 将外部 PPTX 的指定页面导入到已有演示文稿 |

#### 主题（字体与配色）
| 工具 | 用途 |
|------|------|
| [`wpp.set_font_presentation`](references/wpp/theme.md) | 全文更换字体 |
| [`wpp.set_font_slide`](references/wpp/theme.md) | 单页更换字体 |
| [`wpp.set_color_presentation`](references/wpp/theme.md) | 全文更换配色 |
| [`wpp.set_color_slide`](references/wpp/theme.md) | 单页更换配色 |

#### 下载与导出
| 工具 | 用途 |
|------|------|
| [`wpp.export_image`](references/wpp/export.md) | 导出为图片 |
| [`wpp.export_pdf`](references/wpp/export.md) | 异步导出 PDF |

### 详细参考

| 文档类型 | 参考文件 | 说明 |
|----------|----------|------|
| 演示文稿（pptx / wpp） | `references/pptx_references.md` | PPT 创建与读写、字体与配色设置、下载、导出 |

---

## 操作指南

### 通用操作路由

| 意图 | 路由 |
|------|------|
| 读取文档内容 | `read_file`（统一入口，按后缀自动返回 Markdown 或结构化数据） |
| 创建/写入 | 新建并写入、上传本地文件、新建空白文档 → **见下方「创建/写入」** |
| 局部更新 | 改块/改段/改单元格，已有目标文档上的修改 → 按「支持的文档类型」→ 对应 reference |
| 类型专属能力 | 条件格式、导出转换、翻译、PDF 拆分、幻灯片主题、数据校验 | 按「支持的文档类型」→ 对应 reference 中的专属功能章节 |
| 获取文件标识指南 | **必读** `references/file-locating-guide.md` |

### 高频流程指引

#### 创建/写入

| 用户意图 | 工具 | 适用后缀 |
|----------|------|----------|
| 仅需空白文档 | `create_empty_file` | .doc .docx .otl .dbt .xlsx .xls .ksheet .pptx .ppt |
| 已有正文或表格数据要写入 | `create_file_with_content` | .otl .docx .pdf .xlsx .ksheet .dbt |
| 通过上传本地文件新建云文档 | `upload_new_file` | .doc .docx .xls .xlsx .ppt .pptx .pdf .md .txt .html .zip .png .jpg .jpeg .csv .json .dps .et .wps .gif |
| AI 生成 PPT | `aippt.execute` | .pptx |

后缀不确定时默认 `.otl`。指定文件夹时先按 `references/file-locating-guide.md` 取 `drive_id`、`parent_id`。

选定工具后，阅读 `references/drive/create_and_upload.md` 对应章节获取参数约束（`aippt.execute` 见 `references/aippt.md`）。

#### 创建并美化演示文稿

**步骤 1**：创建演示文稿
- `create_empty_file(drive_id=..., parent_id=..., name="xxx.pptx", file_extension=pptx)` → 获取 `file_id`

**步骤 2**：插入幻灯片
- `wpp.insert_slide(file_id=..., index=0)` → 在指定位置插入空白页

**步骤 3**：设置主题样式
- `wpp.set_font_presentation(file_id=..., font_theme=...)` → 设置整体字体方案
- `wpp.set_color_presentation(file_id=..., color_theme=...)` → 设置整体配色方案
- 单页设置：`wpp.set_font_slide` / `wpp.set_color_slide`
> 字体和配色主题的可选值见 `references/wpp.md`

**步骤 4**：导出（可选）
- 导出 PDF：`wpp.export_pdf(file_id=...)` → 返回下载链接
- 导出图片：`wpp.export_image(file_id=..., format="png")` → 返回图片链接

**步骤 5**：返回结果
- `get_file_link(file_id=...)` → 在线编辑链接

---
## 风险控制

以下工具不可逆，调用前必须向用户确认（详细约束见各工具参考文档的「操作约束」区）：

`cancel_share`、`cancel_collaborator_permissions`

---


## 错误速查

| 错误特征 | 原因 | 处理方式 |
|----------|------|----------|
| `403` / 权限不足 / `无权访问` / `forbidden` | 当前凭据对目标文档、目录或资源无操作权限 | 停止操作，禁止重试或尝试其他接口绕过；告知用户当前账号无权限，并建议联系文档所有者开通权限、确认分享链接权限，或切换到有权限的账号 |

---

## 工具组合速查

| 用户需求 | 推荐工具组合 |
|----------|-------------|
| 创建/写入 | `create_file_with_content` |
| 需要将演示文稿导出为可打印、可分享的 PDF 文件 | `wpp.export_pdf`（创建任务）→ `wpp.export_pdf`（轮询至 finished） |
| 用户需要创建 PPT 演示文稿并设置样式 | `create_empty_file(.pptx)` → `wpp.insert_slide` → `wpp.set_font_presentation` / `wpp.set_color_presentation` → `wpp.export_pdf` |
