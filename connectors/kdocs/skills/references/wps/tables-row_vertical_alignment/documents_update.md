# wps.tables.row_vertical_alignment

#### 功能说明

设置表格的行垂直对齐

**幂等性**：是 — safe

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "col": 1,
  "row": 1,
  "table_index": 1,
  "vertical_alignment": "center"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): HTTP 动作：query（查询） / update（设置）。可选值：`query` / `update`
- `col` (number, 可选): 列号
- `row` (number, 可选): 行号
- `table_index` (number, 必填): 表格索引，从 1 开始
- `vertical_alignment` (string, 可选): 垂直对齐方式

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "table_index": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

