# 十一、文件历史版本

## 1. list_file_versions

#### 功能说明

获取文件的历史版本记录，支持分页。版本记录按修改时间倒序排列。

#### 调用示例

获取历史版本第一页（含备注）：

```json
{
  "file_id": "f_abc123",
  "page_size": 20,
  "with_comment": true
}
```

翻页：

```json
{
  "file_id": "f_abc123",
  "page_size": 20,
  "page_token": "NEXT_PAGE_TOKEN",
  "with_comment": true
}
```

#### 参数说明

- `drive_id` (string, 可选): 源文件所在云盘 ID。已传 url/link_id/file_id 时可省略
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `page_size` (integer, 可选): 每页版本条数，范围 1–500；默认值：`50`
- `page_token` (string, 可选): 分页 token，首次不传，后续传上次返回的 `next_page_token`
- `with_comment` (boolean, 可选): 是否返回版本备注
- `with_ext_attrs` (boolean, 可选): 是否返回版本扩展属性

#### 返回值说明

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "items": [
      {
        "version": 18,
        "id": "h_001",
        "size": 204800,
        "mtime": "2026-06-04T17:30:00+08:00",
        "modified_by": { "name": "张三" },
        "comment": "修正第三章数据"
      },
      {
        "version": 12,
        "id": "h_002",
        "size": 198400,
        "mtime": "2026-06-03T10:00:00+08:00",
        "modified_by": { "name": "李四" },
        "comment": ""
      }
    ],
    "next_page_token": ""
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.items` | array | 当前页版本记录列表 |
| `data.items[].version` | integer | 版本 ID；用于 drive.get_file_version_download 的 version_num 参数 |
| `data.items[].id` | string | 历史记录 ID（history_id） |
| `data.items[].size` | integer | 该版本文件大小（字节） |
| `data.items[].mtime` | string | 该版本修改时间（ISO 8601） |
| `data.items[].modified_by` | object | 修改者信息，含 `name` |
| `data.items[].comment` | string | 版本备注（with_comment=true 时返回） |
| `data.items[].ext_attrs` | object | 版本扩展属性（with_ext_attrs=true 时返回） |
| `data.next_page_token` | string | 下一页游标；为空表示已到末页 |


---

## 2. get_file_version_download

#### 功能说明

获取文件指定历史版本的临时下载地址（`data.url`）。

> data.url 过期（403/401）时需重新调用本接口获取新 url
> version_num 无效时接口直接返回业务错误

#### 调用示例

获取版本 18 的下载信息：

```json
{
  "file_id": "f_abc123",
  "version_num": 18
}
```

指定 drive_id 获取版本下载信息：

```json
{
  "drive_id": "d_xyz",
  "file_id": "f_abc123",
  "version_num": 12
}
```

#### 参数说明

- `drive_id` (string, 可选): 源文件所在云盘 ID。已传 url/link_id/file_id 时可省略
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 ID
- `version_num` (integer, 必填): 版本号（来自 list_file_versions 返回的 items[].version）

#### 返回值说明

```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "url": "https://kcos.kdocs.cn/download/...?token=xxx&expires=1748000000",
    "name": "季度复盘.docx",
    "hashes": {
      "md5": "d41d8cd98f00b204e9800998ecf8427e"
    }
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.url` | string | 临时下载地址；有效期较短，获取后应立即发起 GET 请求下载，仍需携带登录凭据 |
| `data.name` | string | 文件名（含扩展名），可直接用于本地保存 |
| `data.hashes` | object | 文件哈希信息（如 md5），可用于完整性校验 |
