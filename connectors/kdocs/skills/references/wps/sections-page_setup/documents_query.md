# wps.sections.page_setup

#### 功能说明

查询节的节页面设置

**幂等性**：是 — safe

> query 响应中 page_setup 字段为 snake_case（page_width/top_margin 等）；update 写侧 key 为 PascalCase（PageWidth/TopMargin 等），二者不同名，勿混用。

#### 调用示例

文档查询：

```json
{
  "file_id": "<FILE_ID>",
  "section_index": 1,
  "verb": "query"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): 操作类型，固定为 query（查询）。可选值：`query`
- `section_index` (number, 可选): 节索引，从 1 开始

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "page_setup": {
      "bottom_margin": 72,
      "footer_distance": 49.599998474121094,
      "header_distance": 42.54999923706055,
      "left_margin": 90,
      "lines_page": 36,
      "orientation": 0,
      "page_height": 841.9000244140625,
      "page_width": 595.2999877929688,
      "right_margin": 90,
      "section_index": 1,
      "section_start": 2,
      "text_columns": 1,
      "top_margin": 72,
      "vertical_alignment": 0
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

