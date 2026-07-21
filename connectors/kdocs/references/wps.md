# 在线文字（wps）工具完整参考文档

本文件包含金山文档 Skill 中在线文字（`wps.*`）工具的操作说明。该类工具面向在线编辑中的文字文档，适合创建空白文档、导出和原子能力执行等场景。

---

## 通用说明

### 在线文字特点

- 面向在线文字文档，不是本地 `.docx` 文件直传接口
- 支持创建空白在线文档、导出为 DOCX / PDF / 图片 / AP
- 提供 Core Execute 原子能力，对文档进行段落/区间级别的增删改查和格式设置等操作
- 若只是读取正文内容，仍优先使用通用工具 `read_file_content`

### 何时使用 `wps.*`

- 需要新建一个空白在线文字文档
- 需要把在线文字导出为 DOCX、PDF、图片或 AP 文稿
- 需要对文档执行原子操作：读取/修改指定段落内容、查找替换、设置段落格式、设置字符格式等

### 何时不要用 `wps.*`

- 创建普通 `.docx` 文件：用 `create_file`
- 上传或覆盖本地 docx/pdf 文件：用 `upload_file`
- 写 Markdown 富文本内容到智能文档：用 `otl.*`

### `wps.*` 工具调用说明

- 格式：服务名和工具分开: 服务名 wps.xx
  例如：kdocs wps.export

## 导出能力总览

`wps.*` 中的导出能力对外拆分为三个工具：

- `wps.export`：导出 DOCX、创建 PDF 导出任务、发起 AP 导出流程
- `wps.export_image`：导出 PNG / JPEG 图片
- `wps.query_export`：统一查询异步导出结果

> `wps.export` 和 `wps.export_image` 的必填参数是 `link_id`（非 `file_id`）。`link_id` 来自 `get_file_info`、`list_files`、`search_files` 等接口返回，或从文档 URL 路径末尾提取，详见「获取文件标识指南」。

### 选择建议

- 需要拿到 `.docx` 下载地址：用 `wps.export`，传 `format=docx`
- 需要导出图片：用 `wps.export_image`，传 `link_id` 和 `format=png/jpeg`
- 需要导出 PDF：先 `wps.export`，传 `format=pdf`；再按需用 `wps.query_export`
- 需要导出 AP：先 `wps.export`，传 `format=ap`；再用 `wps.query_export`

## Core Execute 概述

`wps.core_execute` 是在线文字的统一原子操作入口，通过 `command` 选择操作类型，`param` 传递命令参数。

当前已上线 3 个模块。命令查找、完整路由表和参数速查见：[execute.md](wps/execute.md)

| 模块 | 能力 | 详细参考 |
|------|------|---------|
| 文档内容 | 段落/区间读写、查找替换 | [content.md](wps/content.md) |
| 段落格式 | 对齐、缩进、行间距 | [paragraph-format.md](wps/paragraph-format.md) |
| 字符格式 | 字体样式、高亮色 | [character-format.md](wps/character-format.md) |
| 枚举值 | 对齐/行距/颜色/下划线常量 | [enums.md](wps/enums.md) |

---

## 一、导出

### 1. wps.export

#### 功能说明

统一导出在线文字文档，按 `format` 分发到不同导出分支：

- `docx`：返回 DOCX 下载结果
- `pdf`：创建 PDF 导出任务
- `ap`：发起 AP 导出流程



#### 操作约束

- **前置检查**：先通过 `get_file_info` / `search_files` / `list_files` 获取 `link_id`，或从文档 URL 路径末尾提取

**幂等性**：否 — 导出为异步任务，用 task_id 轮询结果而非重复提交

#### 调用示例

`format=docx` 导出 DOCX：

```json
{
  "link_id": "link_xxx",
  "format": "docx",
  "with_checksums": "md5,sha256"
}
```

`format=pdf` 导出 PDF：

```json
{
  "link_id": "link_xxx",
  "format": "pdf",
  "from_page": 1,
  "to_page": 10
}
```

`format=ap` 导出 AP 文稿：

```json
{
  "link_id": "link_xxx",
  "format": "ap",
  "name": "季度经营分析"
}
```


#### 参数说明

- `link_id` (string, 必填): 在线文字文件的链接 ID（非 file_id）
- `format` (string, 必填): 导出格式。可选值：`docx` / `pdf` / `ap`
- `with_checksums` (string, 可选): `format=docx` 时可传，校验算法列表，如 `md5,sha256`
- `cid` (string, 可选): `format=docx` 时可传，分享链接 ID
- `from_page` (number, 可选): `format=pdf` 时可传，起始页码；默认值：`1`
- `to_page` (number, 可选): `format=pdf` 时可传，结束页码；默认值：`9999`
- `client_id` (string, 可选): 导出时可选的客户端标识
- `password` (string, 可选): `format=pdf` 时可传，源文档密码
- `store_type` (string, 可选): `format=pdf` 时可传，如 `ks3`、`cloud`
- `multipage` (number, 可选): `format=pdf` 时可传；默认值：`1`
- `opt_frame` (boolean, 可选): `format=pdf` 时可传；默认值：`true`
- `export_open_password` (string, 可选): `format=pdf` 时可传，导出 PDF 打开密码
- `export_modify_password` (string, 可选): `format=pdf` 时可传，导出 PDF 修改密码
- `name` (string, 可选): `format=ap` 时必填，智能文档名称，不含后缀

---

### 2. wps.export_image

#### 功能说明

将在线文字导出为 `png` 或 `jpeg` 图片。该接口走图片导出链路，入参必须使用 `link_id`，不能使用 `file_id`。



#### 操作约束

- **前置检查**：先通过 `get_file_info` / `search_files` / `list_files` 获取 `link_id`，或从文档 URL 路径末尾提取

**幂等性**：否 — 导出为异步任务，用 task_id 轮询结果而非重复提交

#### 调用示例

导出为 PNG 长图：

```json
{
  "link_id": "link_xxx",
  "format": "png",
  "dpi": 150,
  "from_page": 1,
  "to_page": 3,
  "combine_long_pic": true
}
```


#### 参数说明

- `link_id` (string, 必填): 在线文字文件的链接 ID（非 file_id）
- `format` (string, 必填): 导出图片格式。可选值：`png` / `jpeg`
- `dpi` (number, 可选): 导出图片 DPI。可选值：`96` / `150` / `300`；默认值：`96`
- `water_mark` (boolean, 可选): 是否添加水印；默认值：`true`
- `from_page` (number, 可选): 起始页码；默认值：`1`
- `to_page` (number, 可选): 结束页码；默认值：`9999`
- `combine_long_pic` (boolean, 可选): 是否合并为长图；`false` 表示逐页；默认值：`true`
- `use_xva` (boolean, 可选): 是否启用 XVA 渲染
- `client_id` (string, 可选): 导出时可选的客户端标识
- `password` (string, 可选): 源文档密码
- `store_type` (string, 可选): 存储类型，如 `ks3`、`cloud`

#### 返回值说明

```json
{
  "code": 0,
  "data": {
    "url": "https://xxx.wps.cn/export/image.png",
    "file_id": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.url` | string | 导出图片的下载地址 |
| `data.file_id` | string | 导出图片的文件 ID |

---

### 3. wps.query_export

#### 功能说明

统一查询异步导出结果：

- `format=pdf`：查询 PDF 导出任务
- `format=ap`：查询 AP 导出任务



#### 调用示例

`format=pdf` 查询 PDF 导出结果：

```json
{
  "format": "pdf",
  "task_id": "task_xxx",
  "task_type": "normal_export"
}
```

`format=ap` 查询 AP 导出结果：

```json
{
  "format": "ap",
  "file_id": "ap_file_xxx",
  "task_id": "task_xxx"
}
```


#### 参数说明

- `format` (string, 必填): 导出格式。可选值：`pdf` / `ap`
- `task_id` (string, 必填): 导出任务 ID
- `task_type` (string, 可选): `format=pdf` 时可传，通常为 `normal_export`
- `file_id` (string, 可选): `format=ap` 时必填，传 `wps.export` 返回的新智能文档文件 ID
- `extra_query` (object, 可选): `format=ap` 时可传，补充查询参数

---

## 二、原子操作

### 4. wps.core_execute

#### 功能说明

通过 `id + command + param` 调用在线文字原子能力。
每个 command 对应一种原子操作，param 结构随 command 不同。

**一、文档内容**
- 读取: getFullContent / getParagraphContent / getRangeContent / getParagraphsCount
- 修改: modifyParagraphContent / modifyRangeContent
- 查找替换: findContent / replaceContent

**二、段落格式**
- 对齐: modifyParagraphAlignment / modifyRangeAlignment
- 缩进: modifyParagraph[Left|Right|FirstLine]Indent / modifyRange[Left|Right|FirstLine]Indent
- 行间距: modifyParagraphLineSpacing / modifyRangeLineSpacing

**三、字符格式**
- 字符样式: modifyParagraphFontStyle / modifyRangeFontStyle（key-value 模式）
- 高亮色: modifyParagraphHighlight / modifyRangeHighlight

各命令完整参数与枚举表见 wps 经验文档。



> param 结构随 command 变化，不传则为 {}
> 段落索引 n 从 1 开始，超出范围自动限制到最后一段
> 区间参数 begin/end 为字符位置，从 0 开始
> key-value 类命令（FontStyle）通过 key 选择属性，value 类型随 key 变化

#### 调用示例

读取全文：

```json
{
  "id": "file_xxx",
  "command": "getFullContent"
}
```

读取第 3 段：

```json
{
  "id": "file_xxx",
  "command": "getParagraphContent",
  "param": {
    "n": 3
  }
}
```

修改第 1 段内容：

```json
{
  "id": "file_xxx",
  "command": "modifyParagraphContent",
  "param": {
    "n": 1,
    "str": "新的段落内容"
  }
}
```

全文替换：

```json
{
  "id": "file_xxx",
  "command": "replaceContent",
  "param": {
    "findText": "旧词",
    "replaceText": "新词",
    "isAll": true
  }
}
```

设置段落居中：

```json
{
  "id": "file_xxx",
  "command": "modifyParagraphAlignment",
  "param": {
    "n": 1,
    "algMode": 1
  }
}
```

修改首行缩进 2 字符：

```json
{
  "id": "file_xxx",
  "command": "modifyParagraphFirstLineIndent",
  "param": {
    "n": 1,
    "indent": 2,
    "unit": "ch"
  }
}
```

设置 1.5 倍行距：

```json
{
  "id": "file_xxx",
  "command": "modifyParagraphLineSpacing",
  "param": {
    "n": 1,
    "spacingRule": 1
  }
}
```

设置段落字体加粗：

```json
{
  "id": "file_xxx",
  "command": "modifyParagraphFontStyle",
  "param": {
    "n": 1,
    "key": "Bold",
    "value": true
  }
}
```


#### 参数说明

- `id` (string, 必填): 在线文字文件 ID（file_id）
- `command` (string, 必填): 原子操作命令名，支持以下值：
文档内容: getFullContent / getParagraphContent / getRangeContent / getParagraphsCount / modifyParagraphContent / modifyRangeContent / findContent / replaceContent
段落格式: modifyParagraphAlignment / modifyRangeAlignment / modifyParagraphLeftIndent / modifyParagraphRightIndent / modifyParagraphFirstLineIndent / modifyRangeLeftIndent / modifyRangeRightIndent / modifyRangeFirstLineIndent / modifyParagraphLineSpacing / modifyRangeLineSpacing
字符格式: modifyParagraphFontStyle / modifyRangeFontStyle / modifyParagraphHighlight / modifyRangeHighlight

- `param` (object, 可选): 命令参数对象，结构随 command 变化。速查：
- getFullContent / getParagraphsCount: 无需参数
- getParagraphContent: {n}
- getRangeContent: {begin, end}
- modifyParagraphContent: {n, str}
- modifyRangeContent: {begin, end, str}
- findContent: {findText, isAll}
- replaceContent: {findText, replaceText, isAll}
- modifyParagraphAlignment: {n, algMode}
- modifyRangeAlignment: {begin, end, algMode}
- modifyParagraph[Left|Right|FirstLine]Indent: {n, indent, unit}
- modifyRange[Left|Right|FirstLine]Indent: {begin, end, indent, unit}
- modifyParagraphLineSpacing: {n, spacingRule, spacingValue}
- modifyRangeLineSpacing: {begin, end, spacingRule, spacingValue}
- modifyParagraphFontStyle: {n, key, value}
- modifyRangeFontStyle: {begin, end, key, value}
- modifyParagraphHighlight: {n, highColor}
- modifyRangeHighlight: {begin, end, highColor}
各命令完整参数说明与枚举值见 wps 经验文档。


#### 返回值说明

```json
{"ok": true, "message": "success", "data": "..."}

```

---


## 工具速查表

| # | 工具名 | 分类 | 功能 | 必填参数 |
|---|--------|------|------|----------|
| 1 | `wps.export` | export | 统一导出在线文字文档 | `link_id`, `format` |
| 2 | `wps.export_image` | export | 将在线文字导出为图片 | `link_id`, `format` |
| 3 | `wps.query_export` | export | 统一查询异步导出结果 | `format`, `task_id` |
| 4 | `wps.core_execute` | execute | 在线文字原子操作入口，通过 command 指定操作类型 | `id`, `command` |

## Core Execute 使用指引

- 命令路由表与参数速查 → [execute.md](wps/execute.md)

## 典型用途

| 场景 | 说明 |
|------|------|
| 空白文档创建 | 新建在线文字后再进入后续编辑流程 |
| 文档导出 | 通过 `wps.export`、`wps.export_image`、`wps.query_export` 完成 |
| AP 生成 | 通过 `wps.export(format=ap)` 与 `wps.query_export(format=ap)` 完成 |
| 内容读写 | 通过 `wps.core_execute` → `getFullContent` / `modifyParagraphContent` 等 完成 |
| 查找替换 | 通过 `wps.core_execute` → `findContent` / `replaceContent` 等 完成 |
| 段落格式 | 通过 `wps.core_execute` → `modifyParagraphAlignment` / `modifyParagraphLineSpacing` 等 完成 |
| 字符样式 | 通过 `wps.core_execute` → `modifyParagraphFontStyle` / `modifyRangeHighlight` 等 完成 |
