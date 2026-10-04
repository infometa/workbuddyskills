# 二、文档读取与下载

## 1. list_my_files

#### 功能说明

列出「我的云文档」根目录的直接子项。

#### 工具选择

- **适用**：浏览我的云文档根目录时
- **勿用**（改用 `list_files`）：浏览指定文件夹（已有 drive_id 与 parent_id）
- **勿用**（改用 `search_files`）：按关键词/类型找文件

> 无法解析默认云盘时返回 code 400001，data.next_actions 列出可接续工具（search_files / read_file / get_share_info）；按 next_actions 选择下一步，勿重复调用本工具

#### 调用示例

零参浏览我的云文档根目录：

```json
{}
```

指定分页大小：

```json
{
  "page_size": 50,
  "order": "desc",
  "order_by": "mtime"
}
```

#### 参数说明

- `page_size` (integer, 可选): 每页条数；建议 50；范围 1–500；未传时默认 50
- `page_token` (string, 可选): 分页 token，首次请求不传
- `order` (string, 可选): 排序方式。可选值：`desc` / `asc`
- `order_by` (string, 可选): 排序字段。可选值：`ctime` / `mtime` / `dtime` / `fname` / `fsize`
- `filter_exts` (string, 可选): 过滤扩展名，以英文逗号分隔，全部小写
- `filter_type` (string, 可选): 按文件类型筛选。可选值：`file` / `folder` / `shortcut`
- `with_permission` (boolean, 可选): 是否返回文件操作权限
- `with_ext_attrs` (boolean, 可选): 是否返回文件扩展属性

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "drive_id": "8001234567",
    "parent_id": "0",
    "drive_source": "special",
    "items": [
      {
        "id": "CmFqW8kR2nP5xL9vH3jT6aB1dE4gI7sM0",
        "name": "测试目录",
        "type": "folder",
        "drive_id": "8001234567",
        "parent_id": "0",
        "mtime": 1710000000
      }
    ],
    "next_page_token": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.drive_id` | string | 解析到的个人云文档 drive_id，可供后续 list_files / create_file_with_content / create_empty_file 接续 |
| `data.parent_id` | string | 恒为 "0"（根目录） |
| `data.drive_source` | string | special（主路径）或 latest_items（兜底） |
| `data.items` | array[FileInfo] | 文件列表，结构同 list_files，见附录 A |
| `data.next_page_token` | string | 下一页 token，为空表示已是最后一页 |


---

## 2. list_files

#### 功能说明

获取指定文件夹下的子文件列表，通过 `filter_type` 可筛选仅返回文件夹。

#### 工具选择

- **适用**：已有文件夹 id（parent_id），浏览指定文件夹子项时
- **适用**：团队文档库：先 list_doclibs 取 drive_id，再调本工具
- **勿用**（改用 `list_my_files`）：浏览我的云文档根目录
- **勿用**（改用 `search_files`）：按关键词/类型找文件

> 缺参或误用时返回 code 400001，data.next_actions 列出可接续工具（list_my_files / search_files / get_file_info / list_doclibs 等）；按 next_actions 选择下一步；**禁止用同一个 `parent_id` 原样重试本工具**，改 `search_files` 或从 `list_my_files` 重走
> 团队文档库浏览须先 `list_doclibs` 取 `drive_id`，再调本工具

#### 调用示例

列出测试目录（parent_id 取自 list_my_files 返回的文件夹 id）：

```json
{
  "drive_id": "8001234567",
  "parent_id": "CmFqW8kR2nP5xL9vH3jT6aB1dE4gI7sM0",
  "page_size": 50
}
```

仅缺 drive_id 时用 parent_id 补全：

```json
{
  "parent_id": "CmFqW8kR2nP5xL9vH3jT6aB1dE4gI7sM0"
}
```

#### 参数说明

- `drive_id` (string, 可选): 目标文件夹所在云盘 ID。parent_id 非 "0" 时可省略
- `parent_id` (string, 必填): 文件夹 ID。两种情况：浏览某文件夹时传该文件夹 ID；浏览个人云文档根不要传 "0"，改用 list_my_files
- `page_size` (integer, 可选): 每页条数；建议 50；范围 1–500；未传时默认 50；默认值：`50`
- `page_token` (string, 可选): 分页 token，首次请求不传
- `order` (string, 可选): 排序方式。可选值：`desc` / `asc`
- `order_by` (string, 可选): 排序字段。可选值：`ctime` / `mtime` / `dtime` / `fname` / `fsize`
- `filter_exts` (string, 可选): 过滤扩展名，以英文逗号分隔，全部小写
- `filter_type` (string, 可选): 按文件类型筛选。可选值：`file` / `folder` / `shortcut`
- `with_permission` (boolean, 可选): 是否返回文件操作权限
- `with_ext_attrs` (boolean, 可选): 是否返回文件扩展属性

| 你手上有什么 | `drive_id` / `parent_id` 怎么来 |
| --- | --- |
| 刚 `create_file_with_content` / `create_empty_file` 成功 | 用响应里的 `drive_id`、`parent_id` |
| 有文件节点 id、尚未列目录 | 先 `get_file_info` → 取 `drive_id`、`parent_id` |
| 要列根目录子项 | 用 `list_my_files`，不要用本工具 + `parent_id="0"` |
| 要列「测试目录」等子文件夹 | 先 `list_my_files` → 取文件夹 `items[].id` 作 `parent_id`（示例 id 见 list_my_files 返回值示例） |
| 已在某文件夹列过表 | 子文件夹用 `items[].id` 作 `parent_id`（不必再传 `drive_id`） |
| 仅缺 `drive_id`，有非根 `parent_id` | 只传 `parent_id`，服务端以其反查 `drive_id` |

#### 返回值说明

```json
{
  "data": {
    "items": [
      {
        "created_by": {
          "avatar": "string",
          "company_id": "string",
          "id": "string",
          "name": "string",
          "type": "user"
        },
        "ctime": 0,
        "drive_id": "string",
        "ext_attrs": [
          { "name": "string", "value": "string" }
        ],
        "id": "string",
        "link_id": "string",
        "link_url": "string",
        "modified_by": {
          "avatar": "string",
          "company_id": "string",
          "id": "string",
          "name": "string",
          "type": "user"
        },
        "mtime": 0,
        "name": "string",
        "parent_id": "string",
        "shared": true,
        "size": 0,
        "type": "folder",
        "version": 0
      }
    ],
    "next_page_token": "string"
  },
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array[FileInfo] | 文件列表，结构见附录 A |
| `data.next_page_token` | string | 下一页 token，为空表示已是最后一页 |


---

## 3. download_file

#### 功能说明

获取文件下载信息。

**`drive_id`**（非必填）：源文件所在云盘 ID。已传 url/link_id/file_id 时可省略。

#### 工具选择

- **适用**：获取独立文件的下载链接或下载地址
- **适用**：需要对已上传的二进制文件生成临时下载 URL
- **勿用**：目标文件类型是 .otl / .dbt / .ksheet — 这些在线文档类型不支持用 `download_file` 下载，请使用 `read_file`读取内容

> 不支持在线文档类型（.otl / .dbt / .ksheet）的下载。仅支持二进制文件（.docx / .xlsx / .pdf / .pptx / .jpg / .png 等）。读取在线文档内容请使用 `read_file` 工具

#### 调用示例

获取下载链接：

```json
{
  "drive_id": "string",
  "file_id": "string",
  "with_hash": true
}
```

file_id：

```json
{
  "file_id": "string",
  "with_hash": true
}
```

#### 参数说明

- `drive_id` (string, 可选): 源文件所在云盘 ID。已传 url/link_id/file_id 时可省略
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `with_hash` (boolean, 可选): 是否返回校验值，对应响应里的 hashes
- `internal` (boolean, 可选): 是否返回内网下载地址；默认值：`false`
- `storage_base_domain` (string, 可选): 签发的存储网关地址，根据 base_domain 优先匹配。可选值：`wps.cn` / `kdocs.cn` / `wps365.com`

#### 返回值说明

```json
{
  "data": {
    "hashes": [
      {
        "sum": "string",
        "type": "sha256"
      }
    ],
    "url": "string"
  },
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.url` | string | 下载地址。公网环境下一级域名为 wps.cn 或 kdocs.cn 时需携带登录凭据 |
| `data.hashes` | array | 文件散列值（仅 `with_hash=true` 时返回），公网可能返回 md5/sha1/sha256 中的一个或多个 |
| `data.hashes[].sum` | string | 哈希结果 |
| `data.hashes[].type` | string | 哈希类型：`sha256` / `md5` / `sha1` / `s2s` |


---

## 4. download_attachment

#### 功能说明

查询文档附件的下载信息。根据文件 ID 与附件 ID 获取附件下载链接、名称与大小；链接为有效期内可直接下载的 URL。

**下载已有附件**：从 `read_file`、`otl.block_query` 等接口的实际返回中获取目标附件的资源 ID，填入 `download_attachment.attachment_id`；已有 ID 时直接复用，`file_id` 使用附件所属文档 ID。

返回中已有目标附件的 `sourceKey` 时直接使用；OTL 节点中，文件附件（`type="WPSDocument"` 且 `attrs.viewType=4`）取 `attrs.wpsDocumentId`，图片（`type="picture"`）取 `attrs.sourceKey`。其他接口以实际返回的附件资源 ID 为准，不使用节点的块 ID。

> 返回的 download_url 有时效限制，应在获取后尽快使用
> 已上传附件也可使用 `upload_attachment` 返回的 `object_id`，文档标识须与上传时一致

#### 调用示例

获取附件下载信息：

```json
{
  "file_id": "<附件所属文档ID>",
  "attachment_id": "<目标附件的资源ID>"
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 附件所属文档的文件 ID
- `attachment_id` (string, 必填): 目标附件的资源 ID（如 sourceKey）；上传附件使用返回的 object_id

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "download_url": "https://cdn.example.com/attachments/abc123?token=xxx",
    "name": "设计稿.png",
    "size": 1048576
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.download_url` | string | 附件下载地址，有效期内可直接下载 |
| `data.name` | string | 附件文件名 |
| `data.size` | number | 附件大小（字节） |


---

## 5. get_file_info

#### 功能说明

获取文件（夹）信息。通过 `file_id` 获取单个文件或文件夹的详细信息，包含 `drive_id` 等关键字段，可用于获取其他接口所需的 `drive_id`。

#### 调用示例

获取文件信息：

```json
{
  "file_id": "string",
  "with_permission": true,
  "with_drive": true
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件（夹）ID
- `with_permission` (boolean, 可选): 是否返回文件操作权限
- `with_ext_attrs` (boolean, 可选): 是否返回文件扩展属性
- `with_drive` (boolean, 可选): 是否返回文件所在 drive 信息

#### 返回值说明

```json
{
  "data": {
    "created_by": {
      "avatar": "string",
      "company_id": "string",
      "id": "string",
      "name": "string",
      "type": "user"
    },
    "ctime": 0,
    "drive": {
      "allotee_id": "string",
      "allotee_type": "user",
      "company_id": "string",
      "created_by": {
        "avatar": "string",
        "company_id": "string",
        "id": "string",
        "name": "string",
        "type": "user"
      },
      "ctime": 0,
      "description": "string",
      "ext_attrs": [
        { "name": "string", "value": "string" }
      ],
      "id": "string",
      "mtime": 0,
      "name": "string",
      "quota": {
        "deleted": 0,
        "remaining": 0,
        "total": 0,
        "used": 0
      },
      "source": "string",
      "status": "inuse"
    },
    "drive_id": "string",
    "ext_attrs": [
      { "name": "string", "value": "string" }
    ],
    "id": "string",
    "link_id": "string",
    "link_url": "string",
    "modified_by": {
      "avatar": "string",
      "company_id": "string",
      "id": "string",
      "name": "string",
      "type": "user"
    },
    "mtime": 0,
    "name": "string",
    "parent_id": "string",
    "permission": {
      "comment": true,
      "copy": true,
      "copy_content": true,
      "delete": true,
      "download": true,
      "history": true,
      "list": true,
      "move": true,
      "new_empty": true,
      "perm_ctl": true,
      "preview": true,
      "print": true,
      "rename": true,
      "saveas": true,
      "secret": true,
      "share": true,
      "update": true,
      "upload": true
    },
    "shared": true,
    "size": 0,
    "type": "folder",
    "version": 0
  },
  "code": 0,
  "msg": "string"
}

```

返回通用文件信息结构，详见附录 A。当 `with_drive=true` 时额外返回 `drive` 对象（含盘的 id、name、quota 等信息）。


---

## 6. read_file

#### 功能说明

读取云文档正文，按文件类型自动返回 Markdown、纯文本或结构化数据。
覆盖文字、PDF、演示、智能文档、表格与多维表、纯文本、Markdown 与 CSV。

#### 工具选择

- **适用**：读取云文档正文内容（Markdown/纯文本/结构化摘要）时
- **勿用**：整表精细读取或海量表格/多维表/智能文档块级数据 — 表格用 sheet.*，多维表用 dbsheet.*，智能文档块级读取用 otl.*，不要用本工具代替
- **勿用**（改用 `pdf.split`）：PDF 拆页、合并、转格式等页级操作 — 页级操作用 pdf.*（如 split/merge/convert），不要用本工具代替
- **勿用**：WPS 文字文档导出为其他格式（如导出 PDF/图片） — 导出用 wps.*，本工具仅读取正文内容
- **勿用**（改用 `wpp.write_slide`）：增删/移动/复制幻灯片 — 幻灯片页级操作用 wpp.write_slide / wpp.read_slide，不要用本工具代替
- **勿用**（改用 `wpp.set_font_presentation`）：改演示文稿主题字体或配色 — 主题用 wpp.set_font_* / wpp.set_color_*（页级或整稿），不要用本工具代替
- **勿用**（改用 `wpp.export_pdf`）：演示文稿导出 PDF 或图片 — 导出用 wpp.export_pdf / wpp.export_image，不要用本工具代替

#### 调用约束

- **前置检查**：用户提供 URL/分享链时可直接传入 url 参数；否则通过 search_files 获取 file_id
- **禁止**：图片文件（.jpg/.jpeg/.png/.gif/.bmp/.svg/.webp 等）不支持读取正文

**幂等性**：是

> 首次请求返回 status=pending 时，携带该响应中的 task_id 和原读取参数再次请求，将返回文档全量内容
> 表格/多维表：未指定 sheet 时使用默认工作表；未传 sheet_range 时读默认首屏区域；单次返回数据有限
> PDF 复杂排版可能有精度损失，提取结果为近似文本
> 必须检查返回的 warnings 字段：内容可能未读全（如仅返回首屏、默认工作表等），warnings 会提示实际读取范围和建议
> 智能文档（.otl）：默认 Markdown 不含图片链接（![image]() 占位）；读取内嵌图片须 enable_upload_medias=true，或 otl.block_query → download_attachment

#### 调用示例

首次调用（通过链接读取）：

```json
{
  "url": "https://www.kdocs.cn/l/example"
}
```

异步轮询（首次请求返回 `status=pending`；携带其 `task_id` 再次请求，返回文档全量内容）：

```json
{
  "url": "https://www.kdocs.cn/l/example",
  "task_id": "90cacdde6ac0cfafa2c2d1f12fa70220"
}
```

读取表格指定区域：

```json
{
  "file_id": "EQfLmhXnmxMB7UQE4v3urx2YuK982rEbE",
  "sheet_name": "Sheet1",
  "sheet_range": {
    "row_from": 0,
    "row_to": 99,
    "col_from": 0,
    "col_to": 25
  }
}
```

读取演示文稿（pptx）：

```json
{
  "url": "https://www.kdocs.cn/l/example"
}
```

pptx 异步轮询（首次请求返回 `status=pending`；携带其 `task_id` 再次请求，返回文档全量内容）：

```json
{
  "url": "https://www.kdocs.cn/l/example",
  "task_id": "90cacdde6ac0cfafa2c2d1f12fa70220"
}
```

读取智能文档并导出内嵌图片 URL：

```json
{
  "link_id": "string",
  "enable_upload_medias": true
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 金山文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `task_id` (string, 可选): 任务 ID；返回 `status=pending` 时提供，下次请求须携带该 `task_id` 和原读取参数。
- `format` (string, 可选): 文档内容目标格式。可选值：`markdown` / `plain`（纯文本）/ `kdc`（结构化表示）。txt 默认 plain、可选 markdown/plain；md 默认 markdown、可选 markdown/plain/kdc；csv 默认 markdown、可选 markdown/kdc，不支持 plain；docx/doc/pdf/wps/otl（markdown|plain|kdc）；ppt/pptx（markdown|kdc）；xlsx/xls/et 传选区走 sheet_range，dbt 传选表走 dbsheet_records
- `enable_upload_medias` (boolean, 必填): 【文档类 docx/pdf/wps/doc/ppt/pptx/otl】是否将正文内图片等附件转为可下载 URL，默认为true；为true时抽取结果中附件会返回有效期内可下载的 URL。markdown / kdc 抽取路径生效
- `sheet_name` (string, 可选): 【表格类 xlsx/ksheet 等、多维表 dbt】工作表或数据表名称
- `sheet_id` (number, 可选): 【表格类、多维表】工作表或数据表 ID；与 sheet_name 同传时优先使用
- `sheet_range` (object, 可选): 【表格类】读取区域，0-based，起止均含；传入则走选区（默认首屏区域）；不传且 sheet_name/sheet_id 不传则 xlsx/xls/et 走 markdown
  - `row_from` (number): 起始行
  - `row_to` (number): 结束行
  - `col_from` (number): 起始列
  - `col_to` (number): 结束列

#### 返回值说明

```json
// status=ok（文档类 docx/pdf/otl）
{
  "code": 0,
  "data": {
    "status": "ok",
    "file_id": "nUaJ8MnXS1MKhbGG1VGdrxGJ7AygCANhG",
    "drive_id": "2101657290",
    "name": "报告.docx",
    "suffix": ".docx",
    "content_format": "markdown",
    "size": 982782,
    "content": "# 标题\n\n正文内容…"
  },
  "msg": "ok"
}

// status=pending（需携带 task_id 获取结果）
{
  "code": 0,
  "data": {
    "status": "pending",
    "task_id": "90cacdde6ac0cfafa2c2d1f12fa70220"
  },
  "msg": "ok"
}

// status=ok（表格类）
{
  "code": 0,
  "data": {
    "status": "ok",
    "file_id": "EQfLmhXnmxMB7UQE4v3urx2YuK982rEbE",
    "drive_id": "2101657290",
    "name": "数据.xlsx",
    "suffix": ".xlsx",
    "content_format": "sheet_range",
    "size": 982782,
    "content": {
      "sheets_info": { "detail": { "sheetsInfo": [{"sheetId": 1, "sheetIdx": 0, "sheetName": "Sheet1", "rowFrom": 0, "rowTo": 4, "colFrom": 0, "colTo": 2}] }, "result": "ok" },
      "range_data": { "detail": { "rangeData": [{"cellText": "姓名", "originRow": 0, "originCol": 0, "understandableType": {"type": "string", "value": "姓名"}}, {"cellText": "100", "originRow": 1, "originCol": 1, "understandableType": {"type": "double", "value": 100}}] }, "result": "ok" }
    },
    "warnings": ["未指定工作表名称，已默认读取第一张可解析的工作表；若需指定表请传入 sheet_name。"]
  },
  "msg": "ok"
}

// status=ok（演示文稿 ppt/pptx）
{
  "code": 0,
  "data": {
    "status": "ok",
    "file_id": "EQfLmhXnmxMB7UQE4v3urx2YuK982rEbE",
    "drive_id": "...",
    "name": "汇报.pptx",
    "suffix": ".pptx",
    "content_format": "kdc",
    "size": 982782,
    "content": {
      "slide_containers": [
        {
          "category": "slides",
          "slides": [
            {
              "name": "封面",
              "shape_tree": [
                {
                  "type": "textbox",
                  "textbox": {
                    "blocks": [
                      { "para": { "runs": [{ "text": "标题文字" }] } }
                    ]
                  }
                }
              ]
            }
          ]
        }
      ]
    }
  },
  "msg": "ok"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.status` | string | `ok` 内容就绪 / `pending` 需带本次返回的 task_id 获取结果 |
| `data.task_id` | string | 仅 status=pending 时返回；取得完整内容后不得再次使用 |
| `data.file_id` | string | 文件 ID |
| `data.drive_id` | string | 盘 ID |
| `data.name` | string | 文件名 |
| `data.suffix` | string | 文件后缀（如 .txt .md .csv .docx .xlsx .otl .pdf .ppt .pptx） |
| `data.content_format` | string | 内容格式标识，由服务端根据文件类型决定 |
| `data.content` | string|object | 正文内容，类型和结构由 content_format 决定 |
| `data.warnings` | array | 提示信息（仅在有提示时出现，如未指定工作表名称、建议用 otl.block_query 等） |
