# wps.comments.paragraph_insert

## 1. wps.comments.paragraph_insert

#### 功能说明

在在线文字文档指定段落插入批注。

> paragraph_index 为 1-based；需先定位：可由 wps.texts.range（段落 → begin/end）或 wps.texts.search 定位后换算得到段落号。

#### 调用示例

段落插入：

```json
{
  "file_id": "<FILE_ID>",
  "paragraph_index": 1,
  "text": "smoke example text"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `paragraph_index` (number, 必填): 段落索引，从 1 开始
- `text` (string, 必填): 批注文本
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "comment": {
      "author": "未知",
      "date": "",
      "index": 2,
      "is_reply": false,
      "scope_begin": 0,
      "scope_end": 29,
      "scope_text": "在此处键入公式。smoke example text",
      "text": "smoke example text\r"
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
