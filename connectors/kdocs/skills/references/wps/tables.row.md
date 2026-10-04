# wps.tables.row

## 1. wps.tables.row

#### 功能说明

删除在线文字文档表格的行。

**幂等性**：是 — safe

> 破坏性 delete 前文档须有可用表格（wps.tables.count ≥ 1）。
> data delete 早于 all delete；merge/split 后表结构变化，后续操作可能需重新插表。

#### 调用示例

文档删除：

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
- `table_index` (number, 可选): 表格索引，从 1 开始
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "row": 1,
    "table_index": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
