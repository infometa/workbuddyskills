# wps.sections.grid_layout

## 1. wps.sections.grid_layout

#### 功能说明

设置在线文字文档节的网格排版。

**幂等性**：是 — safe

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "chars_line": 1,
  "layout_mode": 1,
  "lines_page": 1,
  "section_index": 1
}
```

#### 参数说明

- `chars_line` (number, 可选): chars line
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `layout_mode` (number, 可选): layout mode
- `lines_page` (number, 可选): lines page
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `section_index` (number, 可选): 节索引，从 1 开始
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
