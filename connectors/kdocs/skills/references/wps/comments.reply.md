# wps.comments.reply

## 1. wps.comments.reply

#### 功能说明

回复在线文字文档批注。

> index 为 1-based，须先存在批注；可用 wps.comments.list 取真实 index。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "author": "smoke",
  "index": 1,
  "text": "smoke example text"
}
```

#### 参数说明

- `author` (string, 可选): 批注作者
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `index` (number, 可选): 批注索引，从 1 开始，默认 1
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `text` (string, 必填): 回复内容
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "comment": {
      "author": "",
      "date": "",
      "index": 0,
      "is_reply": false,
      "scope_begin": 19,
      "scope_end": 19,
      "scope_text": "",
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
