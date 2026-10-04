# wps.comments.add

## 1. wps.comments.add

#### 功能说明

在在线文字文档中插入批注。

> 定位批注正文用 range（begin/end）或 paragraph_index 二选一；与 getAllCommentsInfo 的 scope.start/end 回填可实现「与原批注完全相同的选区」。

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>",
  "author": "smoke",
  "begin": 1,
  "end": 74,
  "paragraph_index": 1,
  "text": "smoke example text"
}
```

#### 参数说明

- `author` (string, 可选): 批注作者
- `begin` (number, 可选): 字符区间起始（scope=ranges 时必填）
- `end` (number, 可选): 字符区间结束（scope=ranges 时必填）
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `paragraph_index` (number, 可选): 段落索引，从 1 开始（scope=paragraphs 时必填）
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
      "scope_begin": 1,
      "scope_end": 42,
      "scope_text": "在此处键入公式。smoke example text\r\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007",
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
