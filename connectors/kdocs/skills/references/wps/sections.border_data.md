# wps.sections.border_data

## 1. wps.sections.border_data

#### 功能说明

查询在线文字文档节的边框数据。

**幂等性**：是 — safe

> SECTION_BORDER_DATA proto 化专用字段 border_data；JSAPI 依据 Section.Borders.Item(wdBorderTop/...).LineStyle/LineWidth/Color/ArtStyle

#### 调用示例

文档查询：

```json
{
  "file_id": "<FILE_ID>",
  "section_index": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `section_index` (number, 可选): 节索引，从 1 开始
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "border_data": [
      {"side": -1, "line_style": 1, "line_width": 12, "color": -16777216, "art": 1},
      {"side": -3, "line_style": 1, "line_width": 12, "color": -16777216, "art": 1},
      {"side": -2, "line_style": 1, "line_width": 12, "color": -16777216, "art": 1},
      {"side": -4, "line_style": 1, "line_width": 12, "color": -16777216, "art": 1}
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
