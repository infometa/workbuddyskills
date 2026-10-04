# wps.comments.list

## 1. wps.comments.list

#### 功能说明

查询在线文字文档批注的列表。

**幂等性**：是 — safe

#### 调用示例

文档查询：

```json
{
  "file_id": "<FILE_ID>"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "comments": [
      {
        "author": "未知",
        "date": "2026-09-03 18:55:26",
        "index": 1,
        "is_reply": false,
        "scope_begin": 0,
        "scope_end": 28,
        "scope_text": "在此处键入公式。smoke example text",
        "text": "smoke comment anchor\r"
      },
      {
        "author": "未知",
        "date": "2026-09-03 18:55:26",
        "index": 2,
        "is_reply": false,
        "scope_begin": 0,
        "scope_end": 29,
        "scope_text": "在此处键入公式。smoke example text",
        "text": "smoke example text\r"
      },
      {
        "author": "未知",
        "date": "2026-09-03 18:55:25",
        "index": 3,
        "is_reply": false,
        "scope_begin": 1,
        "scope_end": 43,
        "scope_text": "在此处键入公式。smoke example text\r\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007",
        "text": "smoke example text\r"
      },
      {
        "author": "未知",
        "date": "2026-09-03 18:55:27",
        "index": 4,
        "is_reply": false,
        "scope_begin": 1,
        "scope_end": 44,
        "scope_text": "在此处键入公式。smoke example text\r\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007",
        "text": "smoke example text\r"
      }
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
