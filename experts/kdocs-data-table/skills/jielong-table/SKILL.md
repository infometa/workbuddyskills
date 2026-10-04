---
name: jielong-table
description: "自动识别接龙文本内容，提取结构化数据并生成在线表格（.ksheet）。 当用户粘贴接龙文本或提到「接龙转表格」、「整理接龙」、「接龙统计」、「文字转表格」时使用。
"
homepage: 
version: 2.6.4
metadata: {"openclaw":{"category":"kdocs","emoji":"📊"}}
---

# 接龙转表格

接龙转表格技能可以将群聊接龙、文字信息自动转换为结构化表格。

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

#### 数据操作
| 工具 | 用途 |
|------|------|
| [`sheet.update_range_data`](references/sheet/data.md) | 批量更新选区数据 |

### 详细参考

| 文档类型 | 参考文件 | 说明 |
|----------|----------|------|
| 表格文档/智能表格（xlsx & ksheet） | `references/sheet_references.md` | 工作表管理、范围数据获取、批量更新 |

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

#### 接龙转表格

**步骤 1**：识别接龙场景 → 根据场景信息和接龙内容，推断表格名称(`sheetName`)和表头(`headerList`)字段；处理重复、取消、修改（同一人以最后一次记录为准），得到最终数据(`infoList`)

**步骤 2**：通过 `create_file_with_content` 一次性创建智能表格（`name` 为 `{sheetName}.ksheet`，传 `file_extension=ksheet`、`sheet_name=sheetName` 与表头+`infoList` 的 `rangeData`；单批 `rangeData` 项数 ≤ 500）

**步骤 3（仅当数据超 500 项时）**：通过 `sheet.update_range_data` 续写剩余数据

**步骤 4（可选 - 汇总统计）**：若用户要求按品类/分类汇总数量，通过 `sheet.update_range_data(op_type=cell_operation_type_formula)` 在数据区域下方写入汇总公式（如 `=SUMIF(品类列, "苹果", 数量列)`）

**步骤 5**：调用 `get_file_link` 获取新表格链接，回复"已将接龙转为表格"并输出表格统计信息和链接

---
## 风险控制

以下工具不可逆，调用前必须向用户确认（详细约束见各工具参考文档的「操作约束」区）：

`sheet.delete_sheets`、`sheet.delete_range_data`、`cancel_share`、`sheet.delete_protection_ranges`、`sheet.delete_data_validations`、`cancel_collaborator_permissions`、`sheet.delete_conditional_format_rules`、`sheet.delete_float_images`、`sheet.delete_filters`、`sheet.delete_pivot_table`

---


## 错误速查

| 错误特征 | 原因 | 处理方式 |
|----------|------|----------|
| `403` / 权限不足 / `无权访问` / `forbidden` | 当前凭据对目标文档、目录或资源无操作权限 | 停止操作，禁止重试或尝试其他接口绕过；告知用户当前账号无权限，并建议联系文档所有者开通权限、确认分享链接权限，或切换到有权限的账号 |

---

## 工具组合速查

| 用户需求 | 推荐工具组合 |
|----------|-------------|
| 用户粘贴接龙内容或意图将文字转表格 | 抽取 infoList → `create_file_with_content` →（必要时）`sheet.update_range_data` 续写 → `get_file_link` |
