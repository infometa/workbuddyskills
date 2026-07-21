# 二、文档读取与下载

## 1. list_files

#### 功能说明

获取指定文件夹下的子文件列表，通过 `filter_type` 可筛选仅返回文件夹。



#### 调用示例

列出根目录内容：

```json
{
  "drive_id": "8001234567",
  "parent_id": "0",
  "page_size": 50,
  "order": "desc",
  "order_by": "mtime"
}
```


#### 参数说明

- `drive_id` (string, 必填): 云盘 ID
- `parent_id` (string, 必填): 父目录 ID，根目录时为 "0"
- `page_size` (integer, 必填): 每页条数；建议 50；范围 1–500
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

## 2. download_file

#### 功能说明

获取文件下载信息。

**`drive_id`**（非必填）：

- **有明确的 drive_id** 必传。
- **没有**：不传。



> 不支持在线文档类型的下载，仅支持上传的二进制文件（.docx / .xlsx / .pdf / .pptx 等）。获取在线文档内容的替代方案：.otl → `read_file_content` 或 `otl.block_query`；.ksheet/.xlsx → `sheet.*`；.dbt → `dbsheet.*`

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

- `drive_id` (string, 可选): 目标云盘 ID
- `file_id` (string, 必填): 文件 ID
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

## 3. get_file_info

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

## 4. read_file_content

#### 功能说明

文档内容抽取。支持将文档内容抽取为 markdown、纯文本或 KDC 结构化格式。

**调用方式**：首次调用传入 `drive_id` 及 `file_id` / `link_id`（二选一），**不传 `task_id`**：
- 若返回 `task_status=success`：内容已就绪，直接使用，**无需再次轮询**。
- 若返回 `task_status=running`：使用返回的 `task_id` 继续轮询，直至 `task_status` 为 `success`。

> **`file_id` 与 `link_id` 二选一必填**：通过文件直接访问时传 `file_id`；通过分享链接访问时传 `link_id`。两者不可同时为空。

**类型适用范围**：不支持 .csv 格式。Excel（.xlsx）与智能表格（.ksheet）应使用 `sheet.*`，多维表格（.dbt）应使用 `dbsheet.*`，智能文档（.otl）日常读取优先使用 `otl.block_query`（本工具对 otl 存在内容遗漏风险）。



#### 操作约束

- **禁止**：禁止对 .csv 文件调用本工具
- **提示**：Excel/智能表格用 `sheet.*`，多维表格用 `dbsheet.*`，智能文档日常读取优先 `otl.block_query`

**幂等性**：是

> 首次调用（不传 `task_id`）若返回 `task_status=success`，此时内容已就绪，无需再次轮询；若返回 `task_status=running`，再携带 `task_id` 轮询
> `file_id` 与 `link_id` 二选一必填，两者均为空时请求无效
> 避免重复提交：同一 `file_id`（或 `link_id`）+ `format` + `include_elements` 在已有 `running` 任务时，优先继续使用原 `task_id` 轮询

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

- `drive_id` (string, 必填): 云盘 ID
- `file_id` (string, 二选一必填: `file_id` / `link_id`): 文件 ID。与 `link_id` 二选一传入
- `link_id` (string, 二选一必填: `file_id` / `link_id`): 分享链接 ID。与 `file_id` 二选一传入；通过分享链接访问文件时使用
- `format` (string, 可选): 文档内容目标格式。可选值：`kdc`（结构化表示）/ `plain`（纯文本）/ `markdown`
- `include_elements` (array, 可选): 指定抽取元素。默认元素为 `para`（段落），且一定会被导出；其余附加元素根据参数选择性导出。可选值：`para` / `table` / `component` / `textbox` / `all`
- `enable_upload_medias` (boolean, 可选): 是否将文档中的多媒体附件上传云存储，默认 false；为 true 时抽取结果中附件(比如图片)会返回有效期内可下载的 URL, 只有当format=markdown或者kdc才生效
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


---

