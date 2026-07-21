# 金山文档 Skill 工具完整参考

本文件包含金山文档 Skill 所有工具的 API 说明、参数、返回值。

> **通用返回字段**：所有接口均返回 `code`（状态码，0 表示成功）和 `msg`（人可阅读的文本信息）。

---

## 一、写文档

### 1. create_file

#### 功能说明

在云盘下新建文件或文件夹。通过 `file_type` 区分：`file` 创建文件，`folder` 创建文件夹，`shortcut` 创建快捷方式。支持格式：doc, docx, form, xls, otl, ppt, dbt, xlsx, ksheet, pptx。**PDF 不使用本工具创建，请改用 `upload_file` 直接创建并写入。**

#### 调用示例

创建智能文档：

```json
{
  "drive_id": "string",
  "parent_id": "string",
  "file_type": "file",
  "name": "Q1区域销售周报.otl",
  "on_name_conflict": "rename"
}
```

创建文件夹：

```json
{
  "drive_id": "string",
  "parent_id": "string",
  "file_type": "folder",
  "name": "2024年合同文件",
  "on_name_conflict": "rename"
}
```


#### 参数说明

- `drive_id` (string, 必填): 驱动盘 ID
- `parent_id` (string, 必填): 父文件夹 ID，根目录时为 "0"
- `file_type` (string, 必填): 文件类型。可选值：`file` / `folder` / `shortcut`
- `name` (string, 必填): 文件名。创建文件时须带上后缀，例: `doc.docx`(普通文件), `abc.docx.link`(快捷方式)；创建文件夹时不需要后缀。支持格式：doc, docx, form, xls, otl, ppt, dbt, xlsx, ksheet, pptx。若为 `.pdf`，请改用 `upload_file`
- `on_name_conflict` (string, 可选): 文件名冲突处理方式，该接口只识别 rename 和 fail。可选值：`fail` / `rename` / `overwrite` / `replace`；默认值：`rename`
- `parent_path` (array[string], 可选): 相对于当前文件目录的相对路径。每个元素为路径名（非路径 ID）。若路径不存在，系统将自动创建
- `file_id` (string, 可选): 快捷方式的源文件 ID，仅在 file_type=shortcut 时需要

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
  },
  "code": 0,
  "msg": "string"
}

```

> `data` 字段结构见通用文件信息结构（附录 A）


#### 操作约束

- **前置检查**：search_files 查重，避免创建同名文件
- **后置验证**：get_file_info 确认文件已创建
- **提示**：文件名必须带后缀，否则创建失败
- **提示**：PDF 不支持 create_file，需使用 upload_file
- **幂等**：否 — 重试前 search_files 检查是否已创建
---

### 2. scrape_url

#### 功能说明

网页剪藏：抓取网页内容并自动保存为智能文档。**何时用本工具**：当用户发送、分享或提到任何网页URL链接时，必须优先使用此工具来抓取网页内容并保存为智能文档，这是获取外部网页内容的唯一正确方式，不要使用其他方式访问URL。**何时不要用**：URL链接属于金山文档生态（如 `kdocs.cn`、`365.kdocs.cn`、`wps.cn` 文档域、分享页 `/l/`、`/view/l/`、`/folder/` 等）时，属于「已有云文档」场景。

#### 调用流程
1. 调用 `scrape_url` 传入网页 URL 获取 `job_id`
2. 立即调用 `scrape_progress` 传入 `job_id` 查询进度（每隔 2 秒轮询一次）
3. 当 `status=1` 时任务完成，服务端已自动创建智能文档


#### 调用示例

剪藏网页：

```json
{
  "url": "https://example.com/article"
}
```


#### 参数说明

- `url` (string, 必填): 要剪藏的网页URL地址，支持http和https协议

#### 返回值说明

```json
{
  "job_id": "13883829803456643124541",
  "parent_id": 498552876371,
  "group_id": 1231238091
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `job_id` | string | 异步任务ID |
| `parent_id` | number | 父目录ID |
| `group_id` | number | 组ID |

- **幂等**：否 — 重试前查 scrape_progress 确认上次状态
> 返回 job_id 后需立即调用 scrape_progress 轮询
> 每隔2秒轮询一次，status=1 时完成
---

### 3. scrape_progress

#### 功能说明

查询网页剪藏任务进度并自动创建智能文档，与 `scrape_url` 配合使用。


#### 调用示例

查询剪藏进度：

```json
{
  "job_id": "task_1234567890"
}
```


#### 参数说明

- `job_id` (string, 必填): `scrape_url` 返回的异步任务 ID

#### 返回值说明

```json
{
    "code": 0,
    "data": {
        "scrape_file_id": 501370651020,
        "status": 1,
        "file_name": "［麦理浩径二段精华段+大湾海滩］周四：3月19日 麦径二段12公里徒步，超适合新手小白！.otl",
        "parent_id": 498552876371,
        "group_id": 1231238091,
        "cache": 0,
        "core_err": null
    },
    "msg": "成功"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.scrape_file_id` | number | 剪藏专用文档标识 |
| `data.status` | number | 任务状态: 1=完成, -1=失败, 其他=进行中 |
| `data.file_name` | string | 文件名 |
| `data.parent_id` | number | 父目录ID |
| `data.group_id` | number | 组ID |
| `data.cache` | number | 缓存标识 |
| `data.core_err` | string | 内核错误信息 |

> status=1 时停止轮询，获取 scrape_file_id
> status=-1 时停止轮询，任务失败
> 其他状态继续轮询（每 2 秒一次）
---

### 4. upload_file

#### 功能说明

**全量上传写入文件**：服务端完成三步上传，可用于：

- **更新已有文件**：传 `file_id`，覆盖已有 `docx` / `pdf`
- **新建并上传本地文件**：不传 `file_id`，改传 `name`（必须带文件后缀）

- **支持类型**：更新模式仅支持目标文件为 **docx**、**pdf**；新建模式支持文件名为 **doc**、**docx**、**xls**、**xlsx**、**ppt**、**pptx**、**pdf**
- **源为 Markdown 时**：务必传 `content_format=markdown`；仅支持转为 **docx**、**pdf** 后上传


#### 调用示例

同类型覆盖（docx → docx）：

```json
{
  "drive_id": "string",
  "parent_id": "string",
  "file_id": "k9TRnWXPLsMQJY7G3Bdf2yZVNK6hcxeqw",
  "content_base64": "JVBERi0xLjQK..."
}
```

新建 PDF 并写入（二进制 PDF Base64）：

```json
{
  "drive_id": "string",
  "parent_id": "string",
  "name": "2024年度报告.pdf",
  "content_base64": "JVBERi0xLjQK..."
}
```

Markdown 覆盖（先转为 docx/pdf 再上传）：

```json
{
  "drive_id": "string",
  "parent_id": "string",
  "file_id": "k9TRnWXPLsMQJY7G3Bdf2yZVNK6hcxeqw",
  "content_base64": "<Markdown 内容的 Base64>",
  "content_format": "markdown"
}
```


#### 参数说明

- `drive_id` (string, 必填): 驱动盘 ID
- `parent_id` (string, 必填): 父文件夹 ID
- `file_id` (string, 可选): 条件必填：更新模式必填。要覆盖的文件 ID（仅支持 docx/pdf 文件）
- `name` (string, 可选): 条件必填：新建模式必填。本地文件名，必须带后缀，如 `.docx` / `.xlsx` / `.pptx` / `.pdf`；仅在不传 `file_id` 时使用
- `content_base64` (string, 必填): 源文件内容，Base64 编码。若为 Markdown 文本需同时传 content_format=markdown，确保 UTF-8 格式、base64 编码
- `content_format` (string, 可选): 源内容格式。与目标文件同类型，或 `markdown`（会先转为目标格式再上传；仅支持目标为 docx / pdf）。可选值：`doc` / `docx` / `xls` / `xlsx` / `pdf` / `markdown`
- `file_sum` (string, 可选): 文件哈希值，不传则服务端按内容计算
- `file_type` (string, 可选): 哈希类型。可选值：`sha256` / `md5` / `sha1`
- `parent_path` (array[string], 可选): 相对路径

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "id": "k9TRnWXPLsMQJY7G3Bdf2yZVNK6hcxeqw",
    "name": "2024年度报告.docx",
    "link_url": "https://www.kdocs.cn/l/dpjw3VgQkZrm",
    "link_id": "dpjw3VgQkZrm",
    "size": 57081,
    "parent_id": "...",
    "drive_id": "...",
    "type": "file",
    "version": 1,
    "ctime": 1773563524,
    "mtime": 1773563524,
    "created_by": { ... },
    "modified_by": { ... },
    "shared": false,
    "hash": { "sum": "...", "type": "sha1" }
  }
}

```

> `data` 字段结构见通用文件信息结构（附录 A）


#### 操作约束

- **前置检查**（更新已有文件时）：先 read_file_content 读取现有内容，确认覆盖范围
- **后置验证**：read_file_content 确认写入结果
- **提示**：更新模式支持 docx/pdf；新建模式支持 doc/docx/xls/xlsx/ppt/pptx/pdf
- **提示**：Markdown 源内容务必传 content_format=markdown
- **幂等**：是 — 可重试，以最后一次为准
---

### 5. upload_attachment

#### 功能说明

向已有文档上传附件，支持传远程 URL 或本地二进制内容（Base64）。
返回 `object_id`，可用于文档内附件或图片引用。

支持两种上传方式：
- 远程 URL：传 `url`
- 本地二进制：传 `content_base64`


#### 调用示例

通过 URL 上传附件：

```json
{
  "file_id": "string",
  "filename": "头像.png",
  "url": "https://img.qwps.cn/example.png",
  "source_type": "url",
  "source": "processon"
}
```

通过 Base64 上传本地附件：

```json
{
  "file_id": "string",
  "filename": "附件.pdf",
  "content_base64": "JVBERi0xLjQK...",
  "content_type": "application/pdf"
}
```


#### 参数说明

- `file_id` (string, 必填): 已有文档文件 ID
- `filename` (string, 必填): 附件名
- `url` (string, 可选): 条件必填。远程附件 URL，与 content_base64 二选一
- `content_base64` (string, 可选): 条件必填。本地附件内容的 Base64 编码，与 url 二选一
- `content_type` (string, 可选): 可选。附件 MIME 类型；content_base64 模式下不传则默认 application/octet-stream
- `source_type` (string, 可选): 可选。上传内容类型
- `source` (string, 可选): 可选。来源标记，如 processon

#### 返回值说明

```json
{
  "result": "ok",
  "object_id": "1234567890",
  "extra_info": {
    "width": 600,
    "height": 400
  },
  "old_content_type": "image/jpeg",
  "new_content_type": "image/jpeg"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `result` | string | ok 表示成功 |
| `object_id` | string | 附件上传后的对象 ID |
| `extra_info.width` | integer | 图片宽度（像素，仅图片类型返回） |
| `extra_info.height` | integer | 图片高度（像素，仅图片类型返回） |
| `old_content_type` | string | 原始内容类型 |
| `new_content_type` | string | 转换后内容类型 |

> url 与 content_base64 必须二选一
---

## 二、读文档

### 6. list_files

#### 功能说明

获取指定文件夹下的子文件列表，通过 `filter_type` 可筛选仅返回文件夹。


#### 调用示例

列出目录内容：

```json
{
  "drive_id": "string",
  "parent_id": "string",
  "page_size": 50,
  "order": "desc",
  "order_by": "mtime"
}
```


#### 参数说明

- `drive_id` (string, 必填): 驱动盘 ID
- `parent_id` (string, 必填): 文件夹 ID，根目录时为 "0"
- `page_size` (integer, 必填): 分页大小，公网限制最大为 500
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

### 7. download_file

#### 功能说明

获取文件下载信息。

#### 调用示例

获取下载链接：

```json
{
  "drive_id": "string",
  "file_id": "string",
  "with_hash": true
}
```


#### 参数说明

- `drive_id` (string, 必填): 驱动盘 ID
- `file_id` (string, 必填): 文件 ID
- `with_hash` (boolean, 可选): 是否返回校验值，对应响应里的 hashes
- `internal` (boolean, 可选): 是否返回内网下载地址，默认 false
- `storage_base_domain` (string, 可选): 签发的存储网关地址会根据 base_domain 优先匹配。可选值：`wps.cn` / `kdocs.cn` / `wps365.com`

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

## 三、管文档

### 8. move_file

#### 功能说明

批量移动文件(夹)。移动操作为异步任务。

#### 调用示例

移动文件到目标文件夹：

```json
{
  "drive_id": "string",
  "file_ids": [
    "string"
  ],
  "dst_drive_id": "string",
  "dst_parent_id": "string"
}
```


#### 参数说明

- `drive_id` (string, 必填): 驱动盘 ID
- `file_ids` (array[string], 必填): 文件 ID 列表
- `dst_drive_id` (string, 必填): 目标驱动盘 ID
- `dst_parent_id` (string, 必填): 目标文件夹 ID，根目录时为 "0"

#### 返回值说明

```json
{
  "data": {
    "task_id": "string"
  },
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.task_id` | string | 批量任务 ID |


#### 操作约束

- **用户确认**（批量操作（多个 file_ids））：批量移动需向用户确认文件列表和目标位置
- **前置检查**：确认目标文件夹存在（get_file_info）
- **后置验证**：get_file_info 确认 parent_id 为目标文件夹
- **提示**：移动为异步任务，返回 `task_id`
- **幂等**：是
---

### 9. rename_file

#### 功能说明

重命名文件（夹）。


#### 调用示例

重命名文件：

```json
{
  "drive_id": "string",
  "file_id": "string",
  "dst_name": "2024年Q1销售总结.otl"
}
```


#### 参数说明

- `drive_id` (string, 必填): 驱动盘 ID
- `file_id` (string, 必填): 文件（夹）ID
- `dst_name` (string, 必填): 新文件名，须带上后缀。例: `abc.txt`。支持格式：otl, doc, xls, ppt, pptx, wdoc, wxls, wppt, h5, pom, pof, docx, xlsx, ksheet, dbt, pdf

#### 返回值说明

返回通用文件信息结构，详见附录 A。
- **幂等**：是
---

### 10. share_file

#### 功能说明

开启文件分享，可设置权限范围、访问密码、过期时间等。

#### 调用示例

开启公开分享：

```json
{
  "drive_id": "string",
  "file_id": "string",
  "scope": "anyone",
  "opts": {
    "allow_perm_apply": true,
    "check_code": "string",
    "close_after_expire": true,
    "expire_period": 0,
    "expire_time": 0
  }
}
```


#### 参数说明

- `drive_id` (string, 必填): 驱动盘 ID
- `file_id` (string, 必填): 文件 ID
- `scope` (string, 必填): 链接权限范围。可选值：`anyone`（所有人，仅公网支持）/ `company`（仅企业）/ `users`（指定用户）
- `opts` (object, 可选): 链接选项
  - `allow_perm_apply` (boolean, 可选): 允许申请权限
  - `check_code` (string, 可选): 访问密码
  - `close_after_expire` (boolean, 可选): 过期后取消分享链接
  - `expire_period` (integer, 可选): 过期时长。可选值：`0` / `7` / `30`
  - `expire_time` (integer, 可选): 过期时间点

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
    "drive_id": "string",
    "file_id": "string",
    "id": "string",
    "mtime": 0,
    "opts": {
      "allow_perm_apply": true,
      "check_code": "string",
      "close_after_expire": true,
      "expire_period": 0,
      "expire_time": 0
    },
    "role_id": "string",
    "scope": "anyone",
    "status": "open",
    "url": "string"
  },
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.id` | string | 分享链接 ID（修改分享属性时使用） |
| `data.url` | string | 分享访问 URL |
| `data.status` | string | 链接状态：`open` / `closed` / `expired` |
| `data.drive_id` | string | 盘 ID |
| `data.file_id` | string | 文件 ID |
| `data.role_id` | string | 权限角色 ID |
| `data.scope` | string | 权限范围：`anyone` / `company` / `users` |
| `data.ctime` | integer | 创建时间 |
| `data.mtime` | integer | 修改时间 |
| `data.opts` | object | 链接设置 |
| `data.created_by` | object | 创建者信息 |


#### 操作约束

- **禁止**：未经用户明确要求，禁止调用此工具
- **后置验证**：确认返回的分享链接有效
- **幂等**：是
---

### 11. set_share_permission

#### 功能说明

修改已有分享链接的权限范围、密码、过期时间等属性。

#### 调用示例

修改分享权限：

```json
{
  "link_id": "string",
  "scope": "anyone",
  "opts": {
    "allow_perm_apply": true,
    "check_code": "string",
    "close_after_expire": true,
    "expire_period": 0,
    "expire_time": 0
  }
}
```


#### 参数说明

- `link_id` (string, 必填): 分享链接 ID（由 `share_file` 返回的 `data.id`）
- `scope` (string, 可选): 链接权限范围。可选值：`anyone`（仅公网支持）/ `company` / `users`。`login_users` 仅私有化支持
- `opts` (object, 可选): 链接设置
  - `allow_perm_apply` (boolean, 可选): 允许申请权限
  - `check_code` (string, 可选): 访问密码
  - `close_after_expire` (boolean, 可选): 过期后取消分享链接
  - `expire_period` (integer, 可选): 过期时长。可选值：`0` / `7` / `30`
  - `expire_time` (integer, 可选): 过期时间点

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string"
}

```


#### 操作约束

- **禁止**：未经用户明确要求，禁止修改分享权限
---

### 12. cancel_share

#### 功能说明

取消文件分享。


#### 调用示例

暂停分享：

```json
{
  "drive_id": "string",
  "file_id": "string",
  "mode": "pause"
}
```


#### 参数说明

- `drive_id` (string, 必填): 驱动盘 ID
- `file_id` (string, 必填): 文件 ID
- `mode` (string, 可选): 取消分享模式，默认 `pause`。可选值：`pause`（暂停分享）/ `delete`（删除分享）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "string"
}

```


#### 操作约束

- **用户确认**（mode=delete）：永久删除分享链接，不可恢复，必须向用户确认
- **禁止**（mode=delete）：禁止自动重试，失败后报告用户
- **提示**：建议优先使用 mode=pause（可恢复）
- **后置验证**：get_share_info 确认分享状态已变更
- **幂等**：否 — pause 可重试；delete 禁止重试
---

### 13. get_share_info

#### 功能说明

获取分享链接信息。通过 `link_id` 查询分享链接的详细属性。

#### 调用示例

查询分享信息：

```json
{
  "link_id": "string"
}
```


#### 参数说明

- `link_id` (string, 必填): 分享链接 ID（由 `share_file` 返回的 `data.id`）

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
    "drive_id": "string",
    "file_id": "string",
    "id": "string",
    "mtime": 0,
    "opts": {
      "allow_perm_apply": true,
      "check_code": "string",
      "close_after_expire": true,
      "expire_period": 0,
      "expire_time": 0
    },
    "role_id": "string",
    "scope": "anyone",
    "status": "open",
    "url": "string"
  },
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.id` | string | 分享链接 ID（修改分享属性时使用） |
| `data.url` | string | 分享访问 URL |
| `data.status` | string | 链接状态：`open` / `closed` / `expired` |
| `data.drive_id` | string | 盘 ID |
| `data.file_id` | string | 文件 ID |
| `data.role_id` | string | 权限角色 ID |
| `data.scope` | string | 权限范围：`anyone` / `company` / `users` |
| `data.ctime` | integer | 创建时间 |
| `data.mtime` | integer | 修改时间 |
| `data.opts` | object | 链接设置 |
| `data.created_by` | object | 创建者信息 |

---

### 14. get_file_info

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

- `file_id` (string, 必填): 文件（夹）ID
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

### 15. list_labels

#### 功能说明

分页获取云盘自定义标签列表。可按被分配者类型/ID、标签类型筛选。


#### 调用示例

基础分页：

```json
{
  "page_size": 50
}
```

按被分配者筛选：

```json
{
  "page_size": 50,
  "allotee_type": "user",
  "allotee_id": "238896429"
}
```


#### 参数说明

- `page_size` (integer, 必填): 分页大小，公网限制最大为 500
- `page_token` (string, 可选): 分页 token，首次不传，后续传上次返回的 `next_page_token`
- `allotee_type` (string, 可选): 被分配者类型。可选值：`user` / `company`
- `allotee_id` (string, 可选): 被分配者 ID，与 `allotee_type` 配合使用
- `label_type` (string, 可选): 标签类型，如 `custom`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [
      {
        "id": "string",
        "name": "string",
        "label_type": "custom",
        "allotee_type": "user",
        "allotee_id": "string",
        "ctime": 0,
        "mtime": 0,
        "hash": 0,
        "rank": 0
      }
    ],
    "next_page_token": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array | 标签列表 |
| `data.items[].id` | string | 标签 ID |
| `data.items[].name` | string | 标签名称 |
| `data.items[].label_type` | string | 标签类型，如 `custom` |
| `data.items[].allotee_type` | string | 被分配者类型：`user` / `company` |
| `data.items[].allotee_id` | string | 被分配者 ID |
| `data.items[].ctime` | integer | 创建时间（时间戳，秒） |
| `data.items[].mtime` | integer | 修改时间（时间戳，秒） |
| `data.items[].hash` | integer | 标签内容哈希值 |
| `data.items[].rank` | integer | 排序权重 |
| `data.next_page_token` | string | 下一页 token，为空表示已是最后一页 |

---

### 16. create_label

#### 功能说明

创建自定义标签。


#### 调用示例

创建用户标签：

```json
{
  "allotee_type": "user",
  "name": "我的项目"
}
```


#### 参数说明

- `allotee_type` (string, 必填): 归属者类型。可选值：`user` / `group` / `app`
- `name` (string, 必填): 标签名称，最多 240 字符
- `allotee_id` (string, 可选): 归属者 ID
- `label_type` (string, 可选): 标签类型。可选值：`custom` / `system`；默认值：`custom`
- `attr` (string, 可选): 自定义属性，最多 127 字符
- `rank` (number, 可选): 排序值，默认为创建时间戳（纳秒），建议使用默认值

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "label": {
      "id": "string",
      "name": "我的项目",
      "label_type": "custom",
      "allotee_type": "user",
      "allotee_id": "string",
      "ctime": 1710000000,
      "mtime": 1710000000,
      "hash": "string",
      "rank": 0
    }
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.label` | object | 新创建的标签信息 |
| `data.label.id` | string | 新标签 ID |
| `data.label.name` | string | 标签名称 |
| `data.label.label_type` | string | 标签类型 |
| `data.label.ctime` | integer | 创建时间（时间戳，秒） |
| `data.label.rank` | integer | 排序权重 |

---

### 17. get_label_meta

#### 功能说明

获取单个标签的详细信息。支持系统标签（固定 ID）和自定义标签。


#### 调用示例

查询系统星标标签：

```json
{
  "label_id": "1"
}
```


#### 参数说明

- `label_id` (string, 必填): 标签 ID。公网系统标签固定 ID：`1`（星标）/ `2`（待办）/ `3`（未确认协作）/ `4`（同步文件夹）/ `5`（常用）/ `6`（快速访问）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "id": "string",
    "name": "string",
    "label_type": "custom",
    "allotee_type": "user",
    "allotee_id": "string",
    "ctime": 0,
    "mtime": 0,
    "hash": 0,
    "rank": 0
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.id` | string | 标签 ID |
| `data.name` | string | 标签名称 |
| `data.label_type` | string | 标签类型：`system`（系统标签）/ `custom`（自定义标签） |
| `data.allotee_type` | string | 被分配者类型：`user` / `company` |
| `data.allotee_id` | string | 被分配者 ID |
| `data.ctime` | integer | 创建时间（时间戳，秒），系统标签为 0 |
| `data.mtime` | integer | 修改时间（时间戳，秒），系统标签为 0 |
| `data.hash` | integer | 标签内容哈希值 |
| `data.rank` | integer | 排序权重，系统标签为 0 |

---

### 18. get_label_objects

#### 功能说明

获取指定标签下的所有对象。通过 `label_id` 查询该标签下打了标记的文件、云盘等对象列表。


#### 调用示例

自定义标签下的文件：

```json
{
  "label_id": "379727",
  "object_type": "file",
  "page_size": 50
}
```

查询系统标签"星标"下的文件：

```json
{
  "label_id": "1",
  "object_type": "file",
  "page_size": 50
}
```


#### 参数说明

- `label_id` (string, 必填): 标签 ID。公网系统标签固定 ID：`1`（星标）/ `2`（待办）/ `3`（未确认协作）/ `4`（同步文件夹）/ `5`（常用）/ `6`（快速访问）；自定义标签 ID 由 `list_labels` 或 `create_label` 返回
- `object_type` (string, 必填): 标签对象类型。可选值：`file` / `drive` / `history` / `app` / `url`
- `page_size` (integer, 必填): 分页大小，公网限制最大为 500
- `page_token` (string, 可选): 分页 token，首次不传，后续传上次返回的 `next_page_token`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [
      {
        "object_id": "string",
        "object_type": "file",
        "label_id": "string",
        "ctime": 0
      }
    ],
    "next_page_token": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array | 标签对象列表 |
| `data.items[].object_id` | string | 对象 ID（如文件 ID） |
| `data.items[].object_type` | string | 对象类型：`file` / `drive` 等 |
| `data.items[].label_id` | string | 标签 ID |
| `data.items[].ctime` | integer | 打标时间（时间戳，秒） |
| `data.next_page_token` | string | 下一页 token，为空表示已是最后一页 |

---

### 19. batch_add_label_objects

#### 功能说明

批量对文档对象添加指定标签（打标签）。可一次为多个文件打上同一标签。


#### 调用示例

批量打标签：

```json
{
  "label_id": "379727",
  "objects": [
    {
      "id": "file_id_1",
      "type": "file"
    },
    {
      "id": "file_id_2",
      "type": "file"
    }
  ]
}
```


#### 参数说明

- `label_id` (string, 必填): 标签 ID
- `objects` (array[object], 必填): 要打标签的对象列表
  - `id` (string, 必填): 对象 ID
  - `type` (string, 必填): 对象类型，可选值：`file` / `drive` / `history` / `app` / `url`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```

---

### 20. batch_remove_label_objects

#### 功能说明

批量移除对象与标签的关联。


#### 调用示例

批量取消标签：

```json
{
  "label_id": "379727",
  "objects": [
    {
      "id": "file_id_1",
      "type": "file"
    }
  ]
}
```


#### 参数说明

- `label_id` (string, 必填): 标签 ID
- `objects` (array[object], 必填): 要取消标签的对象列表
  - `id` (string, 必填): 对象 ID
  - `type` (string, 必填): 对象类型，可选值：`file` / `drive` / `history` / `app` / `url`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```

---

### 21. batch_update_label_objects

#### 功能说明

批量更新标签下对象的排序或自定义属性。


#### 调用示例

更新对象属性：

```json
{
  "label_id": "379727",
  "objects": [
    {
      "id": "file_id_1",
      "type": "file",
      "attr": "重要"
    }
  ]
}
```


#### 参数说明

- `label_id` (string, 必填): 标签 ID
- `objects` (array[object], 必填): 要更新的对象列表
  - `id` (string, 必填): 对象 ID
  - `type` (string, 必填): 对象类型，可选值：`file` / `drive` / `history` / `app` / `url`
  - `attr` (string, 可选): 扩展属性，最长 127 字符

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```

---

### 22. batch_update_labels

#### 功能说明

批量修改自定义标签的名称或属性。**注意**：全局系统标签不可修改（星标-`1` / 待办-`2` / 未确认协作-`3` / 同步文件夹-`4` / 常用-`5` / 快速访问-`6`）。


#### 调用示例

批量重命名与清空属性：

```json
{
  "labels": [
    {
      "id": "379727",
      "name": "Q2项目",
      "attr": ""
    },
    {
      "id": "379728",
      "name": "归档"
    }
  ]
}
```


#### 参数说明

- `labels` (array[object], 必填): 要更新的标签列表
  - `id` (string, 必填): 标签 ID
  - `name` (string, 可选): 新名称，最长 240 字符
  - `attr` (string, 可选): 对象自定义属性，最长 127 字符

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```

---

### 23. list_star_items

#### 功能说明

获取当前用户的收藏（星标）列表，支持分页和排序。


#### 调用示例

获取收藏列表：

```json
{
  "page_size": 20
}
```


#### 参数说明

- `page_size` (integer, 必填): 分页大小，公网限制最大为 500
- `page_token` (string, 可选): 分页 token，首次不传，后续传上次返回的 `next_page_token`
- `order` (string, 可选): 排序方向。可选值：`desc` / `asc`
- `order_by` (string, 可选): 排序字段，如 `ctime` / `mtime` / `rank`
- `include_exts` (string, 可选): 只返回指定后缀的文件，逗号分隔，如 `docx,xlsx`
- `exclude_exts` (string, 可选): 排除指定后缀的文件，逗号分隔
- `with_permission` (boolean, 可选): 是否返回文件操作权限信息
- `with_link` (boolean, 可选): 是否返回文件分享信息

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [
      {
        "id": "string",
        "name": "string",
        "type": "file",
        "drive_id": "string",
        "parent_id": "string",
        "ctime": 0,
        "mtime": 0
      }
    ],
    "next_page_token": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array[FileInfo] | 收藏文件列表，结构见附录 A |
| `data.next_page_token` | string | 下一页 token，为空表示已是最后一页 |

---

### 24. batch_create_star_items

#### 功能说明

批量添加收藏

#### 调用示例

批量添加收藏：

```json
{
  "objects": [
    {
      "id": "file_id_1",
      "type": "file"
    },
    {
      "id": "file_id_2",
      "type": "file"
    }
  ]
}
```


#### 参数说明

- `objects` (array[object], 必填): 待收藏对象列表
  - `id` (string, 必填): 文件 ID
  - `type` (string, 必填): 类型，取值 `file` / `drive`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```

---

### 25. batch_delete_star_items

#### 功能说明

批量移除收藏（取消星标）。


#### 调用示例

批量移除收藏：

```json
{
  "objects": [
    {
      "id": "file_id_1",
      "type": "file"
    }
  ]
}
```


#### 参数说明

- `objects` (array[object], 必填): 待移除收藏的对象列表
  - `id` (string, 必填): 文件 ID
  - `type` (string, 必填): 类型，取值 `file` / `drive`

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```

---

### 26. list_latest_items

#### 功能说明

获取当前用户最近访问的文档列表，支持分页、过滤和排序。

#### 调用示例

获取最近访问列表：

```json
{
  "page_size": 20
}
```


#### 参数说明

- `page_size` (integer, 必填): 分页大小，公网限制最大为 500
- `page_token` (string, 可选): 分页 token
- `include_exts` (string, 可选): 只返回指定后缀的文件，逗号分隔
- `exclude_exts` (string, 可选): 排除指定后缀的文件，逗号分隔
- `include_creators` (string, 可选): 只返回指定创建者的文件，逗号分隔（创建者 ID）
- `exclude_creators` (string, 可选): 排除指定创建者的文件，逗号分隔
- `with_permission` (boolean, 可选): 是否返回权限信息
- `with_link` (boolean, 可选): 是否返回分享信息

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [
      {
        "id": "string",
        "name": "string",
        "type": "file",
        "drive_id": "string",
        "mtime": 0
      }
    ],
    "next_page_token": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array[FileInfo] | 最近访问文件列表，结构见附录 A |
| `data.next_page_token` | string | 下一页 token，为空表示已是最后一页 |

---

### 27. copy_file

#### 功能说明

复制文件到指定目录（可跨盘）

#### 调用示例

复制到目标目录：

```json
{
  "drive_id": "src_drive_id",
  "file_id": "file_id_1",
  "dst_drive_id": "dst_drive_id",
  "dst_parent_id": "dst_folder_id"
}
```


#### 参数说明

- `drive_id` (string, 必填): 源文件所在驱动盘 ID
- `file_id` (string, 必填): 源文件 ID
- `dst_drive_id` (string, 必填): 目标驱动盘 ID
- `dst_parent_id` (string, 必填): 目标父目录 ID，根目录为 "0"

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "id": "string",
    "name": "string",
    "type": "file",
    "drive_id": "string",
    "parent_id": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.id` | string | 新文件 ID |
| `data.name` | string | 文件名 |
| `data.type` | string | 文件类型 |
| `data.drive_id` | string | 目标驱动盘 ID |
| `data.parent_id` | string | 目标父目录 ID |

---

### 28. check_file_name

#### 功能说明

检查文件名在指定目录下是否已存在。常用于上传、复制、移动等操作前的同名预检查。

#### 调用示例

检查文件名是否占用：

```json
{
  "drive_id": "string",
  "parent_id": "string",
  "name": "Q1销售报告.docx"
}
```


#### 参数说明

- `drive_id` (string, 必填): 驱动盘 ID
- `parent_id` (string, 必填): 父目录 ID，根目录为 "0"
- `name` (string, 必填): 待检查的文件名（含后缀）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "exists": true,
    "file_id": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.exists` | boolean | 文件名是否已存在 |
| `data.file_id` | string | 若已存在，返回已有文件 ID |

---

### 29. list_deleted_files

#### 功能说明

获取回收站文件列表，支持分页和按驱动盘过滤。


#### 调用示例

列出回收站文件：

```json
{
  "page_size": 20
}
```


#### 参数说明

- `page_size` (integer, 必填): 分页大小，公网限制最大为 100
- `page_token` (string, 可选): 分页 token
- `drive_id` (string, 可选): 按驱动盘过滤
- `with_ext_attrs` (boolean, 可选): 是否返回扩展属性
- `with_drive` (boolean, 可选): 是否返回所属驱动盘信息

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok",
  "data": {
    "items": [
      {
        "id": "string",
        "name": "string",
        "type": "file",
        "drive_id": "string",
        "parent_id": "string",
        "ctime": 0,
        "mtime": 0
      }
    ],
    "next_page_token": "string"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array[FileInfo] | 回收站文件列表，结构见附录 A |
| `data.next_page_token` | string | 下一页 token，为空表示已是最后一页 |

---

### 30. restore_deleted_file

#### 功能说明

将回收站文件还原到原位置

#### 调用示例

还原回收站文件：

```json
{
  "file_id": "string"
}
```


#### 参数说明

- `file_id` (string, 必填): 回收站中的文件 ID（由 `list_deleted_files` 返回）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "ok"
}

```

---

## 四、用文档

### 31. read_file_content

#### 功能说明

文档内容抽取。支持将文档内容抽取为 markdown、纯文本或 KDC 结构化格式。**仅支持异步模式（mode=async）**：首次调用传入 `drive_id`、`file_id` 等，返回 `task_id`；通过 `task_id` 轮询直至 `task_status` 为 `success` 后获取内容。

> ⚠️ **不支持 .csv 格式**，遇到 CSV 文件请勿调用本工具，建议用户转为 .xlsx 后用 `sheet.*` 读取。

> ⚠️ **以下类型不以 `read_file_content` 作为结构化读写主路径**：
>
> - **Excel（.xlsx）与智能表格（.ksheet）**：使用 **`sheet.*`**。**获取内容**：`sheet.get_sheets_info` → `sheet.get_range_data`（矩形区域）。完整工具列表与参数见 `sheet_references.md`。
> - **多维表格（.dbt）**：使用 **`dbsheet.*`**。**获取结构**：`dbsheet.get_schema`；**获取内容**：`dbsheet.list_records`、`dbsheet.get_record`；完整工具列表与参数见 `dbsheet_reference.md`。

> ⚠️ **智能文档（.otl）**：`read_file_content` 对 otl 存在内容遗漏风险（部分组件类型可能丢失），日常读取应优先使用 `otl.block_query`。仅在需要导出 Markdown 格式时使用本工具，并**务必**按照 reference/otl_references.md 的参数要求调用。


#### 调用示例

读取文档为 Markdown：

```json
{
  "drive_id": "string",
  "file_id": "string",
  "format": "markdown",
  "include_elements": [
    "para",
    "table"
  ],
  "mode": "async",
  "task_id": "string"
}
```


#### 参数说明

- `drive_id` (string, 必填): 驱动盘 ID
- `file_id` (string, 必填): 文件 ID
- `format` (string, 可选): 文档内容目标格式。可选值：`kdc`（结构化表示）/ `plain`（纯文本）/ `markdown`
- `include_elements` (array, 可选): 指定抽取元素。默认元素为 `para`（段落），且一定会被导出；其余附加元素根据参数选择性导出。可选值：`para` / `table` / `component` / `textbox` / `all`
- `mode` (string, 可选): **仅支持 `async`**，无需传或固定传 `async`
- `task_id` (string, 可选): 异步任务 ID，用于结果轮询；首次调用不传，后续用返回的 `task_id` 查询直至 `task_status` 为 `success`

#### 返回值说明

```json
{
  "data": {
    "task_id": "string",
    "task_status": "success",
    "dst_format": "markdown",
    "markdown": "string",
    "plain": "string",
    "src_format": "otl",
    "version": "string",
    "doc": {}
  },
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.task_id` | string | 任务 ID，异步模式下返回 |
| `data.task_status` | string | 任务状态。可选值：`success` / `running` / `failed` |
| `data.dst_format` | string | 目标格式：`kdc` / `plain` / `markdown` |
| `data.markdown` | string | markdown 内容数据，目标格式为 `markdown` 时适用 |
| `data.plain` | string | 纯文本内容数据，目标格式为 `plain` 时适用 |
| `data.doc` | object | 文字类的结构化数据，源格式为 otl/pdf/docx 且目标格式为 `kdc` 时适用 |
| `data.src_format` | string | 源格式（otl, docx, pdf, xlsx 等） |
| `data.version` | string | 版本号 |

> 首次调用返回 `task_id`，需轮询 `task_status` 直至 `success`
> 不支持 .csv 格式，禁止对 CSV 文件调用本工具
---

### 32. search_files

#### 功能说明

支持按文件名、内容全文搜索，可按时间、创建者、文件类型等条件过滤。

#### 调用示例

搜索文档：

```json
{
  "keyword": "区域周报告",
  "type": "all",
  "file_type": "file",
  "parent_ids": [
    "string"
  ],
  "page_size": 20,
  "order": "desc",
  "order_by": "mtime",
  "with_total": true
}
```


#### 参数说明

- `keyword` (string, 可选): 搜索关键字
- `type` (string, 必填): 搜索类型。可选值：`file_name`表示搜索文件名，`content`表示搜索文件内容，`all`表示全局搜索。
- `page_size` (integer, 必填): 分页大小，公网限制最大为 500
- `page_token` (string, 可选): 翻页 token
- `file_type` (string, 可选): 文件类型筛选。可选值：`folder` / `file`
- `file_exts` (array, 可选): 文件后缀过滤
- `drive_ids` (array, 可选): 搜索盘列表
- `parent_ids` (array, 可选): 搜索目录列表
- `creator_ids` (array, 可选): 创建者 ID。公网只支持选择是否自己创建的文件
- `modifier_ids` (array, 可选): 编辑者 ID
- `sharer_ids` (array, 可选): 分享者 ID
- `receiver_ids` (array, 可选): 接收者 ID
- `time_type` (string, 可选): 时间范围类型。可选值：`ctime` / `mtime` / `otime` / `stime`
- `start_time` (integer, 可选): 最小时间
- `end_time` (integer, 可选): 最大时间
- `with_permission` (boolean, 可选): 是否返回文件操作权限
- `with_link` (boolean, 可选): 是否返回文件分享信息
- `with_total` (boolean, 可选): 是否返回搜索到的总条数
- `with_drive` (boolean, 可选): 是否返回驱动盘
- `order` (string, 可选): 排序方式。可选值：`desc` / `asc`
- `order_by` (string, 可选): 排序字段。可选值：`ctime` / `mtime`
- `scope` (array, 可选): 搜索范围。可选值：`all` / `share_by_me` / `share_to_me` / `latest` / `personal_drive` / `group_drive` / `recycle` / `customize` / `latest_opened` / `latest_edited`
- `channels` (array, 可选): 渠道信息
- `device_ids` (array, 可选): 设备 ID
- `exclude_channels` (array, 可选): 排除渠道信息
- `exclude_file_exts` (array, 可选): 排除文件后缀
- `filter_user_id` (integer, 可选): 创建者分享者过滤
- `file_ext_groups` (array, 可选): 文件分组后缀
- `search_operator_name` (boolean, 可选): 搜索文件的创建者或文件分享者

#### 返回值说明

```json
{
  "data": {
    "items": [
      {
        "file": {
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
        },
        "file_src": {
          "name": "string",
          "path": "string",
          "type": "link"
        },
        "highlights": {
          "example_key": ["string"]
        },
        "otime": 0
      }
    ],
    "next_page_token": "string",
    "total": 0
  },
  "code": 0,
  "msg": "string"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array | 搜索结果列表 |
| `data.items[].file` | object | 文件信息，通用文件信息结构（附录 A） |
| `data.items[].file_src` | object | 文件位置信息 |
| `data.items[].file_src.name` | string | 来源名称 |
| `data.items[].file_src.path` | string | 文件路径 |
| `data.items[].file_src.type` | string | 来源类型：`link` / `user_private` / `user_roaming` / `group_normal` / `group_dept` / `group_whole` |
| `data.items[].highlights` | map[string][]string | 匹配关键字 |
| `data.items[].otime` | integer | 文件打开时间 |
| `data.next_page_token` | string | 下一页 token |
| `data.total` | integer | 资源集合总数（仅 `with_total=true` 时返回） |

> 新建文件后搜索可能无法立即命中，需等待索引更新
---

### 33. get_file_link

#### 功能说明

获取文件的在线访问链接。

#### 调用示例

获取文件链接：

```json
{
  "file_id": "string"
}
```


#### 参数说明

- `file_id` (string, 必填): 文件 ID

#### 返回值说明

```json
{
  "file_id": "string",
  "file_url": "https://kdocs.cn/l/xxxxx",
  "name": "Q1销售报告"
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `file_id` | string | 文件 ID |
| `file_url` | string | 在线访问链接 |
| `name` | string | 文件名 |

---


## 附录

### A. 通用文件信息结构（FileInfo）

`create_file`、`upload_file`（步骤三）、`rename_file`、`list_files` 等接口返回的文件信息共用以下结构。响应字段表中 `array[FileInfo]` 即引用此结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 文件 ID |
| `name` | string | 文件名 |
| `type` | string | 文件类型：`file` / `folder` / `shortcut` |
| `size` | integer | 文件大小 |
| `parent_id` | string | 父目录 ID |
| `drive_id` | string | 驱动盘 ID |
| `version` | integer | 文件版本 |
| `ctime` | integer | 文件创建时间（时间戳，秒） |
| `mtime` | integer | 文件修改时间（时间戳，秒） |
| `shared` | boolean | 是否开启分享（link.status = 'open' 时为 true） |
| `link_id` | string | 分享 ID |
| `link_url` | string | 分享链接 URL |
| `created_by` | object | 文件创建者信息 |
| `created_by.id` | string | 身份 ID |
| `created_by.name` | string | 用户或应用的名称 |
| `created_by.type` | string | 身份类型：`user` / `sp` / `unknown` |
| `created_by.avatar` | string | 头像 |
| `created_by.company_id` | string | 身份所归属的公司 |
| `modified_by` | object | 文件修改者信息（结构同 created_by） |
| `ext_attrs` | array[object] | 文件扩展属性（`with_ext_attrs=true` 时返回），每项含 name 和 value |
| `drive` | object | 文件驱动盘信息（`with_drive=true` 时返回） |

**`permission` 对象**（`with_permission=true` 时返回）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `comment` | boolean | 评论 |
| `copy` | boolean | 复制 |
| `copy_content` | boolean | 内容复制 |
| `delete` | boolean | 文件删除 |
| `download` | boolean | 下载 |
| `history` | boolean | 历史版本（仅公网支持） |
| `list` | boolean | 列表 |
| `move` | boolean | 文件移动 |
| `new_empty` | boolean | 新建 |
| `perm_ctl` | boolean | 权限管理 |
| `preview` | boolean | 预览 |
| `print` | boolean | 打印 |
| `rename` | boolean | 文件重命名 |
| `saveas` | boolean | 另存为（仅公网支持） |
| `secret` | boolean | 安全文档（仅公网支持） |
| `share` | boolean | 分享 |
| `update` | boolean | 编辑/更新 |
| `upload` | boolean | 上传：手动上传新版本 |

### B. 工具速查表

| #  | 工具名 | 分类 | 功能 | 必填参数 |
|----|--------|------|------|----------|
| 1  | `create_file` | 写文档 | 在云盘下新建文件或文件夹 | `drive_id`, `parent_id`, `file_type`, `name` |
| 2  | `scrape_url` | 写文档 | 网页剪藏，抓取网页内容并自动保存为智能文档 | `url` |
| 3  | `scrape_progress` | 写文档 | 查询网页剪藏任务进度 | `job_id` |
| 4  | `upload_file` | 写文档 | 全量上传写入文件（更新已有 docx/pdf 或新建并上传本地文件） | `drive_id`, `parent_id`, `content_base64` |
| 5  | `upload_attachment` | 写文档 | 向已有文档上传附件，支持 URL 或 Base64 | `file_id`, `filename` |
| 6  | `list_files` | 读文档 | 获取指定文件夹下的子文件列表 | `drive_id`, `parent_id`, `page_size` |
| 7  | `download_file` | 读文档 | 获取文件下载信息 | `drive_id`, `file_id` |
| 8  | `move_file` | 管文档 | 批量移动文件(夹) | `drive_id`, `file_ids`, `dst_drive_id`, `dst_parent_id` |
| 9  | `rename_file` | 管文档 | 重命名文件（夹） | `drive_id`, `file_id`, `dst_name` |
| 10  | `share_file` | 管文档 | 开启文件分享 | `drive_id`, `file_id`, `scope` |
| 11  | `set_share_permission` | 管文档 | 修改分享链接属性 | `link_id` |
| 12  | `cancel_share` | 管文档 | 取消文件分享 | `drive_id`, `file_id` |
| 13  | `get_share_info` | 管文档 | 获取分享链接信息 | `link_id` |
| 14  | `get_file_info` | 管文档 | 获取文件（夹）详细信息 | `file_id` |
| 15  | `list_labels` | 管文档 | 分页获取云盘自定义标签列表（可按归属者、标签类型筛选） | `page_size` |
| 16  | `create_label` | 管文档 | 创建自定义标签 | `allotee_type`, `name` |
| 17  | `get_label_meta` | 管文档 | 获取单个标签详情（含系统标签固定 ID） | `label_id` |
| 18  | `get_label_objects` | 管文档 | 获取某标签下的对象列表（文件/云盘等） | `label_id`, `object_type`, `page_size` |
| 19  | `batch_add_label_objects` | 管文档 | 批量为多个文档对象添加同一标签（打标签） | `label_id`, `objects` |
| 20  | `batch_remove_label_objects` | 管文档 | 批量取消标签 | `label_id`, `objects` |
| 21  | `batch_update_label_objects` | 管文档 | 批量更新标签下对象排序或属性 | `label_id`, `objects` |
| 22  | `batch_update_labels` | 管文档 | 批量修改自定义标签名称或属性 | `labels` |
| 23  | `list_star_items` | 管文档 | 获取收藏（星标）列表 | `page_size` |
| 24  | `batch_create_star_items` | 管文档 | 批量添加收藏 | `objects` |
| 25  | `batch_delete_star_items` | 管文档 | 批量移除收藏 | `objects` |
| 26  | `list_latest_items` | 管文档 | 获取最近访问文档列表 | `page_size` |
| 27  | `copy_file` | 管文档 | 复制文件到指定目录（可跨盘） | `drive_id`, `file_id`, `dst_drive_id`, `dst_parent_id` |
| 28  | `check_file_name` | 管文档 | 检查目录下文件名是否已存在 | `drive_id`, `parent_id`, `name` |
| 29  | `list_deleted_files` | 管文档 | 获取回收站文件列表 | `page_size` |
| 30  | `restore_deleted_file` | 管文档 | 将回收站文件还原到原位置 | `file_id` |
| 31  | `read_file_content` | 用文档 | 文档内容抽取为 Markdown/纯文本 | `drive_id`, `file_id` |
| 32  | `search_files` | 用文档 | 文件（夹）搜索 | `type`, `page_size` |
| 33  | `get_file_link` | 用文档 | 获取文件的云文档在线访问链接 | `file_id` |

