# wps.bookmarks.rename

## 1. wps.bookmarks.rename

#### 功能说明

重命名在线文字文档书签。

> rename 后须用 new_bookmark_name 或 wps.bookmarks.list 刷新后再 query/update/delete。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "bookmark_name": "SmokeBookmark_0903",
  "new_bookmark_name": "SmokeBookmark_0903_Renamed"
}
```

#### 参数说明

- `bookmark_name` (string, 必填): 原书签名称
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `new_bookmark_name` (string, 必填): 新书签名称
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
