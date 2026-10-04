# wps.tables.cell_merge

## 1. wps.tables.cell_merge

#### 功能说明

设置在线文字文档表格的合并单元格。

**幂等性**：是 — safe

> merge/split/sort 会改变表结构；操作前确认 wps.tables.count ≥ 1。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "end_col": 2,
  "end_row": 1,
  "start_col": 1,
  "start_row": 1,
  "table_index": 1
}
```

#### 参数说明

- `end_col` (number, 可选): 结束列
- `end_row` (number, 可选): 结束行
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `start_col` (number, 可选): 起始列
- `start_row` (number, 可选): 起始行
- `table_index` (number, 必填): 表格索引，从 1 开始
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

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
