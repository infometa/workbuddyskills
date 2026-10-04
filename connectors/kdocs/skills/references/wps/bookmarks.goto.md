# wps.bookmarks.goto

## 1. wps.bookmarks.goto

#### 功能说明

将在线文字文档选区跳转到指定书签（Selection.Goto wdGoToBookmark），并返回跳转后选中区间的位置与文本。

**幂等性**：否 — safe

#### 调用示例

文档跳转：

```json
{
  "file_id": "<FILE_ID>",
  "bookmark_name": "重点内容"
}
```

#### 参数说明

- `bookmark_name` (string, 必填): 书签名称
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "bookmark_name": "重点内容",
    "begin": 1402,
    "end": 1406,
    "text": "重点内容"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
