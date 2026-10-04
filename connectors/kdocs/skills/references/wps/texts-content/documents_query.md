# wps.texts.content

#### 功能说明

按文档查询文本内容

**幂等性**：是 — safe

> A/C gap: documents insert/delete TEXT_CONTENT

#### 调用示例

文档查询：

```json
{
  "file_id": "<FILE_ID>",
  "scope": "documents",
  "verb": "query"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 documents（按文档设置）。可选值：`documents`
- `verb` (string, 必填): 操作类型，固定为 query（查询）。可选值：`query`

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "content": "SMOKE_SLICE_ANCHOR_2026-09-03 baseline paragraph for slice smoke examples.\r\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r\u0007\r"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

