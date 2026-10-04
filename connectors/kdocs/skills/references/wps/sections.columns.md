# wps.sections.columns

## 1. wps.sections.columns

#### 功能说明

删除在线文字文档节的分栏。

**幂等性**：是 — safe

#### 调用示例

文档删除：

```json
{
  "file_id": "<FILE_ID>",
  "column_count": 1,
  "line_between": 1,
  "section_index": 1,
  "spacing": 1
}
```

#### 参数说明

- `column_count` (number, 可选): column count
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `line_between` (number, 可选): line between
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `section_index` (number, 必填): 节索引，从 1 开始
- `spacing` (number, 可选): spacing
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
