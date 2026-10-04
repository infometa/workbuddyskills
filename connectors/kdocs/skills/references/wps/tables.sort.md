# wps.tables.sort

## 1. wps.tables.sort

#### 功能说明

设置在线文字文档表格的排序。

**幂等性**：是 — safe

> merge/split/sort 会改变表结构；操作前确认 wps.tables.count ≥ 1。
> 前置约束：表格含合并单元格时引擎显式拒绝（code=500002 sort fail, there may be merged cells）；form 型表单样张不适用 sort。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "col": 1,
  "order": "smoke",
  "sort_order": 1,
  "sort_type": 1,
  "table_index": 1
}
```

#### 参数说明

- `col` (number, 可选): 列号
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `order` (string, 可选): 排序方向：asc/desc
- `sort_order` (number, 可选): 排序顺序枚举
- `sort_type` (number, 可选): 排序字段类型
- `table_index` (number, 必填): 表格索引，从 1 开始
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

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
