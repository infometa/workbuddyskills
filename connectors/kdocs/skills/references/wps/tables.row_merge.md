# wps.tables.row_merge

## 1. wps.tables.row_merge

#### 功能说明

设置在线文字文档表格的合并行。

**幂等性**：是 — safe

> merge/split/sort 会改变表结构；操作前确认 wps.tables.count ≥ 1。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "row": 1,
  "table_index": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `row` (number, 可选): 行号
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
