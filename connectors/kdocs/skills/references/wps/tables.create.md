# wps.tables.create

## 1. wps.tables.create

#### 功能说明

在在线文字文档末尾新建指定行列数的空表格。

**幂等性**：否 — unsafe

> 仅支持在文档末尾追加；如需在指定位置插入，暂用其他通道。
> 新建为空表格（无边框样式保证），可再用 wps.tables.borders/cell_content 等加工。
> rows/cols 必须为正整数。

#### 调用示例

文档末尾新建空表格：

```json
{
  "file_id": "<FILE_ID>",
  "rows": 3,
  "cols": 4
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `rows` (number, 必填): 新建表格的行数（>=1）
- `cols` (number, 必填): 新建表格的列数（>=1）

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "cols": 7,
    "rows": 22,
    "table_index": 2
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
