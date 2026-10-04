# wps.tocs.data

#### 功能说明

按文档查询目录

> toc_index 为 1-based；无目录时 query 失败，须先 insert。

#### 调用示例

文档查询：

```json
{
  "file_id": "<FILE_ID>",
  "scope": "documents",
  "toc_index": 1,
  "verb": "query"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `scope` (string, 必填): 操作范围，固定为 documents（按文档设置）。可选值：`documents`
- `verb` (string, 必填): 操作类型，固定为 query（查询）。可选值：`query`
- `toc_index` (number, 可选): 目录索引

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "toc_info": {
      "toc_index": 1,
      "upper_level": 1,
      "lower_level": 1,
      "end": 31,
      "use_hyperlinks": true,
      "include_page_numbers": true,
      "right_align_page_numbers": true,
      "use_heading_styles": true
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

