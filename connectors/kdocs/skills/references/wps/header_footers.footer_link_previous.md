# wps.header_footers.footer_link_previous

## 1. wps.header_footers.footer_link_previous

#### 功能说明

设置在线文字文档页脚链接上一节。

**幂等性**：是 — safe

> 需要 section_index ≥ 2（第一节无上一节）；先插入分节符再设 link。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "enabled": true,
  "header_footer_type": 1,
  "section_index": 2
}
```

#### 参数说明

- `enabled` (boolean, 可选): 是否启用
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `header_footer_type` (number, 可选): header footer type
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
