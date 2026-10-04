# wps.bookmarks.insert

#### 功能说明

按字符区间插入书签

> 书签名用 bookmark_name；后续 query/update/delete 以 list 返回的真实名为准。
> begin/end 为 0-based 字符区间；可由 wps.texts.search 返回的 ranges 回填。

#### 调用示例

字符区间插入：

```json
{
  "file_id": "<FILE_ID>",
  "begin": 1,
  "bookmark_name": "SmokeBookmark_0903",
  "end": 74,
  "scope": "ranges"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 ranges（按字符区间设置）。可选值：`ranges`
- `begin` (number, 可选): 区间起点（scope=ranges 时必填）
- `bookmark_name` (string, 必填): 书签名称
- `end` (number, 可选): 区间终点（scope=ranges 时必填）

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "bookmark_name": "SmokeBookmark_0903",
    "begin": 1,
    "end": 74
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

