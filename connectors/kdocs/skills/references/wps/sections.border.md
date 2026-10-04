# wps.sections.border

## 1. wps.sections.border

#### 功能说明

删除在线文字文档节的页面边框，恢复无边框态（line_style=0、line_width=9999999、art=0）。

**幂等性**：是 — safe

#### 调用示例

删除页面边框（恢复无边框）：

```json
{
  "file_id": "<FILE_ID>",
  "section_index": 1
}
```

#### 参数说明

- `break_type` (number, 可选): 兼作页面边框线型（WdLineStyle）：0=无边框（清除页面边框，默认）；1=单线；其他值按 WdLineStyle 枚举写入
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `section_index` (number, 必填): 节索引，从 1 开始
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "deleted_section": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
