# 在线文字（wps）工具完整参考文档

本文件包含金山文档 Skill 中在线文字（`wps.*`）工具的操作说明。该类工具面向在线编辑中的文字文档，适合创建空白文档、导出和原子能力执行等场景。

---

## 通用说明

### 在线文字特点

- 面向在线文字文档，不是本地 `.docx` 文件直传接口
- 支持创建空白在线文档、导出为 DOCX / PDF / 图片 / AP
- 提供结构化原子工具，对文档进行段落/区间级别的增删改查和格式设置等操作
- 若只是读取正文内容，仍优先使用通用工具 `read_file`

### 何时使用 `wps.*`
- 需要新建一个空白在线文字文档
- 需要把在线文字导出为 DOCX、PDF、图片或 AP 文稿
- 需要对文档执行原子操作：读取/修改指定段落内容、查找替换、设置段落格式、设置字符格式等

### 何时不要用 `wps.*`
- 创建空白文档 `.docx` 文件：用 `create_empty_file`
- 创建并写入，优先用工具 `create_file_with_content`
- 上传本地 docx/pdf 等文件：用 `upload_new_file`；覆盖已有文档：用 `upload_replace_file`
- 写 Markdown 富文本内容到智能文档：用 `otl.*`

### `wps.*` 工具调用说明

- 格式：服务名和工具分开，property 级命令保留点号
  例如：`kdocs-cli wps texts.range`、`kdocs-cli wps export`
- 文档定位：除创建空白文档 / 纯任务查询外，统一传 `url` / `link_id` / `file_id` **三选一**


## 导出能力总览

`wps.*` 中的导出能力对外拆分为三个工具：

- `wps.export`：导出 DOCX、创建 PDF 导出任务、发起 AP 导出流程
- `wps.export_image`：导出 PNG / JPEG 图片
- `wps.query_export`：统一查询异步导出结果

### 选择建议

- 需要拿到 `.docx` 下载地址：用 `wps.export`，传 `format=docx`
- 需要导出图片：用 `wps.export_image`，传 `format=png/jpeg`，定位 `url` / `link_id` / `file_id` 三选一
- 需要导出 PDF：先 `wps.export`，传 `format=pdf`；再按需用 `wps.query_export`
- 需要导出 AP：先 `wps.export`，传 `format=ap`；再用 `wps.query_export`（`format=ap` 时须传 export 返回的 `file_id`）

## 结构化文档工具

| 能力域 | 参考 |
|--------|------|
| 文本 | [texts](wps/texts.md) |
| 表格 | [tables](wps/tables.md) |
| 图片 | [images](wps/images.md) |
| 形状 | [shapes](wps/shapes.md) |
| 书签 | [bookmarks](wps/bookmarks.md) |
| 内容控件 | [content_controls](wps/content_controls.md) |
| 脚注尾注 | [footnote_endnotes](wps/footnote_endnotes.md) |
| 页眉页脚 | [header_footers](wps/header_footers.md) |
| 域 | [fields](wps/fields.md) |
| 水印 | [watermarks](wps/watermarks.md) |
| 列表 | [lists](wps/lists.md) |
| 节 | [sections](wps/sections.md) |
| 样式 | [styles](wps/styles.md) |
| 修订 | [revisions](wps/revisions.md) |
| 交叉引用 | [references](wps/references.md) |
| 保护 | [protection](wps/protection.md) |
| OLE | [ole](wps/ole.md) |
| 索引 | [indexes](wps/indexes.md) |
| 超链接 | [hyperlinks](wps/hyperlinks.md) |
| 公式 | [formulas](wps/formulas.md) |
| 题注 | [captions](wps/captions.md) |
| 分隔符 | [breaks](wps/breaks.md) |
| 目录 | [tocs](wps/tocs.md) |
| 批注 | [comments](wps/comments.md) |

### 图片类写操作

以下工具需传入**公网可访问的图片 URL**（服务端会拉取图片）：

| 工具 | 顶层参数 | 说明 |
|------|----------|------|
| `wps.watermarks.image` | `file_path` | 插入图片水印 |
| `wps.shapes.picture` | `file_path` | 插入浮动图片形状 |

## 一、导出

> 异步导出为多种格式及状态轮询

| 工具 | 功能 | 必填参数 |
|------|------|----------|
| [`wps.export`](wps/export.md) | 统一导出在线文字文档 | `url`\|`link_id`\|`file_id`, `format` |
| [`wps.export_image`](wps/export_image.md) | 将在线文字导出为图片 | `url`\|`link_id`\|`file_id`, `format` |
| [`wps.query_export`](wps/query_export.md) | 统一查询异步导出结果 | `format`, `task_id` |

## 二、书签操作

> WPS 文字文档 bookmarks 域相关操作。

属性与工具列表见 [书签操作](wps/bookmarks.md)。

## 三、分隔符操作

> WPS 文字文档 breaks 域相关操作。

属性与工具列表见 [分隔符操作](wps/breaks.md)。

## 四、题注操作

> WPS 文字文档 captions 域相关操作。

属性与工具列表见 [题注操作](wps/captions.md)。

## 五、批注操作

> WPS 文字文档 comments 域相关操作。

属性与工具列表见 [批注操作](wps/comments.md)。

## 六、内容控件操作

> WPS 文字文档 content_controls 域相关操作。

属性与工具列表见 [内容控件操作](wps/content_controls.md)。

## 七、域操作

> WPS 文字文档 fields 域相关操作。

属性与工具列表见 [域操作](wps/fields.md)。

## 八、脚注尾注操作

> WPS 文字文档 footnote_endnotes 域相关操作。

属性与工具列表见 [脚注尾注操作](wps/footnote_endnotes.md)。

## 九、公式操作

> WPS 文字文档 formulas 域相关操作。

属性与工具列表见 [公式操作](wps/formulas.md)。

## 十、页眉页脚操作

> WPS 文字文档 header_footers 域相关操作。

属性与工具列表见 [页眉页脚操作](wps/header_footers.md)。

## 十一、超链接操作

> WPS 文字文档 hyperlinks 域相关操作。

属性与工具列表见 [超链接操作](wps/hyperlinks.md)。

## 十二、图片操作

> WPS 文字文档 images 域相关操作。

属性与工具列表见 [图片操作](wps/images.md)。

## 十三、索引操作

> WPS 文字文档 indexes 域相关操作。

属性与工具列表见 [索引操作](wps/indexes.md)。

## 十四、列表操作

> WPS 文字文档 lists 域相关操作。

属性与工具列表见 [列表操作](wps/lists.md)。

## 十五、OLE 对象操作

> WPS 文字文档 ole 域相关操作。

属性与工具列表见 [OLE 对象操作](wps/ole.md)。

## 十六、文档保护操作

> WPS 文字文档 protection 域相关操作。

属性与工具列表见 [文档保护操作](wps/protection.md)。

## 十七、交叉引用操作

> WPS 文字文档 references 域相关操作。

属性与工具列表见 [交叉引用操作](wps/references.md)。

## 十八、修订操作

> WPS 文字文档 revisions 域相关操作。

属性与工具列表见 [修订操作](wps/revisions.md)。

## 十九、节操作

> WPS 文字文档 sections 域相关操作。

属性与工具列表见 [节操作](wps/sections.md)。

## 二十、形状操作

> WPS 文字文档 shapes 域相关操作。

属性与工具列表见 [形状操作](wps/shapes.md)。

## 二十一、样式操作

> WPS 文字文档 styles 域相关操作。

属性与工具列表见 [样式操作](wps/styles.md)。

## 二十二、表格操作

> WPS 文字文档 tables 域相关操作。

属性与工具列表见 [表格操作](wps/tables.md)。

## 二十三、文字文档文本操作

> WPS 文字文档中与段落、字符区间相关的文本格式与内容操作。

属性与工具列表见 [文字文档文本操作](wps/texts.md)。

## 二十四、目录操作

> WPS 文字文档 tocs 域相关操作。

属性与工具列表见 [目录操作](wps/tocs.md)。

## 二十五、水印操作

> WPS 文字文档 watermarks 域相关操作。

属性与工具列表见 [水印操作](wps/watermarks.md)。

## 二十六、WordML/XML 插入

> WPS 文字文档 xmls 域相关操作。

属性与工具列表见 [WordML/XML 插入](wps/xmls.md)。

## 典型用途

| 场景 | 说明 |
|------|------|
| 空白文档创建 | 新建在线文字后再进入后续编辑流程 |
| 文档导出 | 通过 `wps.export`、`wps.export_image`、`wps.query_export` 完成 |
| AP 生成 | 通过 `wps.export(format=ap)` 与 `wps.query_export(format=ap)` 完成 |
| 内容读写 | 通过 `wps.texts.content`、`wps.texts.range`、`wps.texts.count` 等文本工具完成 |
| 查找替换 | 通过 `wps.texts.search` / `wps.texts.replace` 完成 |
| 段落格式 | 通过 `wps.texts.alignment`、`wps.texts.indent`、`wps.texts.line_spacing` 等完成 |
| 字符样式 | 通过 `wps.texts.font`、`wps.texts.highlight`、`wps.texts.format` 等完成 |
