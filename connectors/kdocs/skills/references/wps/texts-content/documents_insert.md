# wps.texts.content

#### 功能说明

按文档插入文本内容

**幂等性**：是 — safe

> A/C gap: documents insert/delete TEXT_CONTENT

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>",
  "scope": "documents",
  "verb": "insert",
  "is_br": true,
  "text": "smoke example text"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 documents（按文档设置）。可选值：`documents`
- `verb` (string, 必填): 操作类型，固定为 insert（插入）。可选值：`insert`
- `is_br` (boolean, 可选): 是否插入换行
- `text` (string, 可选): 待插入文本

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

