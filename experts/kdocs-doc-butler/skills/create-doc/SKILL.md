---
name: create-doc
description: "快速创建各类金山在线文档（智能文档、Word、Excel、PDF、PPT、智能表格、多维表格）并写入内容。 当用户要求「新建文档」、「创建文件」、「写一份文档」、「新建表格」时使用。 若需要读取已有文档，请使用 doc-to-markdown 技能。
"
homepage: 
version: 2.6.4
metadata: {"openclaw":{"category":"kdocs","emoji":"➕"}}
---

# 一键创建在线文档

一键创建在线文档技能支持快速新建各类文档并自动填充内容。

> 本技能依赖 `kdocs` 技能的基础文档操作能力（认证、文件管理等），请确保已安装该技能。详见 `references/core/` 目录。

## 严格规则

### 禁止（NEVER）

- 权限不足时禁止重试或绕过，立即告知用户无权限

---

## 能力范围


### 详细参考

| 文档类型 | 参考文件 | 说明 |
|----------|----------|------|
| 智能文档（otl） | `references/otl_references.md` | 页面、文本、标题、待办等元素操作 |

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

---
## 风险控制

以下工具不可逆，调用前必须向用户确认（详细约束见各工具参考文档的「操作约束」区）：

`otl.block_delete`、`cancel_share`、`cancel_collaborator_permissions`

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
