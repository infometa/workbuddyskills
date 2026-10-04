# wps.fields.by_range

## 1. wps.fields.by_range

#### 功能说明

插入在线文字文档域的区间插入域。

**幂等性**：是 — safe

> range.begin/range.end 为 0-based 字符区间；可由 wps.texts.search 返回的 ranges 回填。

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>",
  "field_code": "DATE",
  "range": {
    "begin": 1,
    "end": 5
  }
}
```

#### 参数说明

- `field_code` (string, 可选): field code
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `range` (object, 可选): range
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "field": {
      "begin": 2,
      "code": " DATE DATE \\* MERGEFORMAT ",
      "end": 37,
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
