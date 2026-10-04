# wps.formulas.math

#### 功能说明

查询文档公式列表

**幂等性**：是 — safe

> FORMULA_INFO proto 化专用 RPC（documents/formulas/query）与 MathFormulaInfo 字段；JSAPI 依据 Document.OMaths.Item(i).Range.Text / Type（WdOMathType）
> text 为公式的 linear 线性文本（BuildUp 后可能为专业格式内部文本），机器断言以 items 非空 + text 包含公式内容为准

#### 调用示例

查询全文档公式：

```json
{
  "file_id": "<FILE_ID>",
  "verb": "query"
}
```

查询指定段落公式：

```json
{
  "file_id": "<FILE_ID>",
  "verb": "query",
  "paragraph_index": 104
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): 操作类型，固定为 query（查询）。可选值：`query`
- `paragraph_index` (number, 可选): 段落索引，从 1 开始；缺省时返回全文档公式

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "count": 1,
    "items": [
      {"index": 1, "paragraph_index": 104, "type": 0, "text": "T=∑t_i", "begin": 1018, "end": 1025}
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

