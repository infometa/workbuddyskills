# 在线文字（wps）工具完整参考文档

本文件包含金山文档 Skill 中在线文字（`wps.*`）工具的操作说明。该类工具面向在线编辑中的文字文档，适合创建空白文档、导出等场景。

---

## 通用说明

### 在线文字特点

- 面向在线文字文档，不是本地 `.docx` 文件直传接口
- 支持创建空白在线文档、导出为 DOCX / PDF / 图片 / AP
- 若只是读取正文内容，仍优先使用通用工具 `read_file_content`

### 何时使用 `wps.*`

- 需要新建一个空白在线文字文档
- 需要把在线文字导出为 DOCX、PDF、图片或 AP 文稿

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

### 选择建议

- 需要拿到 `.docx` 下载地址：用 `wps.export`，传 `format=docx`
- 需要导出图片：用 `wps.export_image`，传 `link_id` 和 `format=png/jpeg`
- 需要导出 PDF：先 `wps.export`，传 `format=pdf`；再按需用 `wps.query_export`
- 需要导出 AP：先 `wps.export`，传 `format=ap`；再用 `wps.query_export`

---

## 一、导出能力

### 1. wps.export

#### 功能说明

统一导出在线文字文档，按 `format` 分发到不同导出分支：

- `docx`：返回 DOCX 下载结果
- `pdf`：创建 PDF 导出任务
- `ap`：发起 AP 导出流程


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

- `link_id` (string, 必填): 在线文字文件链接 ID
- `format` (string, 必填): 导出格式。可选值：`docx` / `pdf` / `ap`
- `with_checksums` (string, 可选): `format=docx` 时可传，校验算法列表，如 `md5,sha256`
- `cid` (string, 可选): `format=docx` 时可传，分享链接 ID
- `from_page` (number, 可选): `format=pdf` 时可传，起始页码；默认值：`1`
- `to_page` (number, 可选): `format=pdf` 时可传，结束页码；默认值：`9999`
- `client_id` (string, 可选): 导出时可传的客户端标识
- `password` (string, 可选): `format=pdf` 时可传，源文档密码
- `store_type` (string, 可选): `format=pdf` 时可传，如 `ks3`、`cloud`
- `multipage` (number, 可选): `format=pdf` 时可传；默认值：`1`
- `opt_frame` (boolean, 可选): `format=pdf` 时可传；默认值：`true`
- `export_open_password` (string, 可选): `format=pdf` 时可传
- `export_modify_password` (string, 可选): `format=pdf` 时可传
- `name` (string, 可选): `format=ap` 时必填，AP 文稿名称，不含后缀

---

### 2. wps.export_image

#### 功能说明

将在线文字导出为 `png` 或 `jpeg` 图片。该接口走图片导出链路，入参必须使用 `link_id`，不能使用 `file_id`。


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

- `link_id` (string, 必填): 在线文字文件链接 ID
- `format` (string, 必填): 图片格式。可选值：`png` / `jpeg`
- `dpi` (number, 可选): 图片 DPI；默认值：`96`
- `water_mark` (boolean, 可选): 是否添加水印；默认值：`true`
- `from_page` (number, 可选): 起始页码；默认值：`1`
- `to_page` (number, 可选): 结束页码；默认值：`9999`
- `combine_long_pic` (boolean, 可选): 是否合并为长图；默认值：`true`
- `use_xva` (boolean, 可选): 是否启用 XVA 渲染
- `client_id` (string, 可选): 导出时可传的客户端标识
- `password` (string, 可选): 源文档密码
- `store_type` (string, 可选): 如 `ks3`、`cloud`

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
- `file_id` (string, 可选): `format=ap` 时必填，传 `wps.export` 返回的新 AP 文件 ID
- `extra_query` (object, 可选): `format=ap` 时可传，补充查询参数

---


## 工具速查表

| # | 工具名 | 分类 | 功能 | 必填参数 |
|---|--------|------|------|----------|
| 1 | `wps.export` | 导出能力 | 统一导出在线文字文档 | `link_id`, `format` |
| 2 | `wps.export_image` | 导出能力 | 将在线文字导出为图片 | `link_id`, `format` |
| 3 | `wps.query_export` | 导出能力 | 统一查询异步导出结果 | `format`, `task_id` |

## 典型用途

| 场景 | 说明 |
|------|------|
| 空白文档创建 | 新建在线文字后再进入后续编辑流程 |
| 文档导出 | 通过 `wps.export`、`wps.export_image`、`wps.query_export` 完成 |
| AP 生成 | 通过 `wps.export(format=ap)` 与 `wps.query_export(format=ap)` 完成 |
