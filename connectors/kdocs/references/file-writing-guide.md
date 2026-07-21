# 文件创建与写入指南

> 已有文件（用户提供了 `file_id` 或通过搜索/链接定位到文件）→ 跳过「类型选择」和 `create_file`，直接看各类型的「更新」路径。

#### 保存位置（`drive_id` / `parent_id`）

`create_file` / `upload_file`（新建）：`drive_id`、`parent_id` 非必填。**用户未指定文件夹**时可省略两参数。**已说明目标文件夹且已查到drive_id、parent_id** 时必须传入；细则见 `file-locating-guide.md`。

#### 本地文件上传（`upload_file`）

适用场景：用户提供本地文件内容，需要直接上传到云盘（新建）或覆盖已有文件。

- 新建上传：`upload_file(drive_id, parent_id, name, content_base64)`
- 覆盖更新：`upload_file(file_id, content_base64)`
- 已明确目标目录时，建议显式传入 `drive_id`、`parent_id`，避免目录偏差

#### 类型选择决策树

仅在需要新建文件时使用：

```
用户需要创建文档
├── 需要丰富排版/图文混排？ → .otl 智能文档（别名 ap）首选
├── 需要表格/数据处理？
│   ├── 简单表格数据 → .xlsx 表格（别名 et）
│   ├── 需要多视图/字段管理/看板（智能表格产品形态）→ .ksheet 智能表格（别名 as）
│   └── 需要多数据表、关联、丰富字段类型与甘特/画册等多视图（多维表格产品形态）→ .dbt 多维表格（别名 db）
├── 需要生成 PDF？ → .pdf
├── 需要兼容 Word？ → .docx 文字文档（别名 wps）
├── 需要生成 PPT？ → .pptx 演示文稿（别名 wpp）
└── 不确定 → .otl 智能文档（别名 ap）默认推荐
```

#### 写入流程

**智能文档**（.otl / ap）——**勿用 `upload_file`**：

- 新建写入：`create_file` → `otl.insert_content` 写入内容
- 更新：`otl.insert_content` 插入内容（`format=markdown, mode=prepend` 从开头插入，`mode=append` 在末尾追加，`mode=replace` 替换全部内容）

**文字文档**（.docx / wps）：

- 新建写入：`create_file` → `upload_file(file_id, content_base64)` 写入内容
- 更新：优先调用 `wps.*` 基础能力做局部编辑；基础能力不支持或在“整篇重写/覆盖上传”场景使用 `upload_file(file_id, content_base64)` 全量覆盖
- Markdown 源内容须传 `content_format="markdown"`

**PDF**（.pdf）——新建无需 `create_file`：

- 新建写入：`upload_file(drive_id, parent_id, name="xxx.pdf", content_base64=...)`
- 更新：`upload_file(file_id, content_base64=...)` 全量覆盖

**Excel 表格**（.xlsx / et）：

- 新建写入：`create_file` → `sheet.update_range_data` 批量写入
- 更新：`sheet.update_range_data` 按范围写入

**智能表格**（.ksheet / as）：

- 新建写入：`sheet.create_airsheet_file` → `sheet.update_range_data` 批量写入
- 更新：`sheet.update_range_data` 按范围写入

**多维表格**（.dbt / db）：

- 新建写入：`create_file` → `dbsheet.create_sheet` → `dbsheet.create_fields` → `dbsheet.create_records`
- 更新：`dbsheet.update_records` / `dbsheet.create_records` 增改记录

**演示文稿**（.pptx / wpp）：

- 新建：`create_file` 或 `upload_file` 上传本地 pptx
- AI 生成型 PPT：使用 `aippt.execute`，通过 `skill_type` 路由到主题生成（`theme_ppt`）或文档转 PPT（`doc_ppt`）流水线
