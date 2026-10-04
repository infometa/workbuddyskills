# wps.fields.by_paragraph

## 1. wps.fields.by_paragraph

#### 功能说明

插入在线文字文档域的段落插入域。

**幂等性**：是 — safe

> paragraph_index 为 1-based；可由 wps.texts.range（段落 → begin/end）或 wps.texts.search 定位后换算。

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>",
  "field_code": "DATE",
  "paragraph_index": 1
}
```

#### 参数说明

- `field_code` (string, 可选): field code
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `paragraph_index` (number, 可选): 段落索引，从 1 开始
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "field": {
      "begin": 1,
      "code": " DATE DATE \\* MERGEFORMAT ",
      "end": 36,
      "index": 0,
      "result": "2026/9/3",
      "type": 31
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
