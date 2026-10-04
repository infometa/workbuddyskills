# wps.sections.line_numbering

## 1. wps.sections.line_numbering

#### 功能说明

设置在线文字文档节的行号。

**幂等性**：是 — safe

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "line_numbering_active": true,
  "line_numbering_count_by": 1,
  "line_numbering_restart_mode": 1,
  "line_numbering_start": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `line_numbering_active` (boolean, 可选): line numbering active
- `line_numbering_count_by` (number, 可选): line numbering count by
- `line_numbering_restart_mode` (number, 可选): line numbering restart mode
- `line_numbering_start` (number, 可选): line numbering start
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
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
