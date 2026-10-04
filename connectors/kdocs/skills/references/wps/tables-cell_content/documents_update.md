# wps.tables.cell_content

#### 功能说明

设置表格的单元格内容

**幂等性**：是 — safe

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "col": 1,
  "row": 1,
  "table_index": 1,
  "text": "smoke cell",
  "verb": "update"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): 操作类型，固定为 update（更新）。可选值：`update`
- `col` (number, 可选): 列号
- `row` (number, 可选): 行号
- `table_index` (number, 可选): 表格索引，从 1 开始
- `text` (string, 可选): 文本内容

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "col": 1,
    "text": "smoke cell"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

