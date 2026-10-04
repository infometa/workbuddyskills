# wps.comments.range_insert

## 1. wps.comments.range_insert

#### 功能说明

在在线文字文档字符区间插入批注。

> begin/end 为 0-based 字符区间；可直接回填 getAllCommentsInfo 的 scope.start/end 实现「与原批注完全相同的选区」。
> 需先定位：可由 wps.texts.search 返回的 ranges 或 wps.texts.range（段落 → begin/end）换算得到 begin/end。

#### 调用示例

字符区间插入：

```json
{
  "file_id": "<FILE_ID>",
  "begin": 1,
  "end": 74,
  "text": "smoke example text"
}
```

#### 参数说明

- `begin` (number, 必填): 字符区间起始
- `end` (number, 必填): 字符区间结束
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
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
      "index": 4,
      "is_reply": false,
      "scope_begin": 1,
      "scope_end": 44,
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
