# wps.fields.data

#### 功能说明

查询域的域数据

**幂等性**：是 — safe

> wps.indexes.entry 之后 fields.list 会多 XE 域；以 list 实时结果为准。
> 返回的 begin/end 为域在正文中的 0-based 字符位置，可直接回填到 wps.fields.by_range 的 range（begin/end）。

#### 调用示例

文档查询：

```json
{
  "file_id": "<FILE_ID>",
  "index": 1,
  "verb": "query"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): 操作类型，固定为 query（查询）。可选值：`query`
- `index` (number, 可选): 索引，从 1 开始

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
      "index": 1,
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

