# wps.tables.split

## 1. wps.tables.split

#### 功能说明

设置在线文字文档表格的拆分表格。

**幂等性**：是 — safe

> merge/split/sort 会改变表结构；操作前确认 wps.tables.count ≥ 1。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "split_at_row": 1,
  "table_index": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `split_at_row` (number, 可选): 拆分表格所在行
- `table_index` (number, 必填): 表格索引，从 1 开始
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "tables_count": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
