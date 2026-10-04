# wps.texts.border

#### 功能说明

查询段落四边边框（border_info）

**幂等性**：是 — safe

> JSAPI 依据 Paragraph.Format.Borders.Item(wdBorderTop/...).LineStyle/Color/LineWidth
> lineWidth 口径（WdLineWidth 枚举）：2=0.25磅 / 4=0.5磅 / 6=0.75磅 / 8=1磅 / 12=1.5磅 / 18=2.25磅 / 24=3磅 / 36=4.5磅 / 48=6磅；无边框时 lineStyle=0、lineWidth=9999999（wdUndefined）。

#### 调用示例

查询段落边框：

```json
{
  "file_id": "<FILE_ID>",
  "verb": "query",
  "paragraph_index": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): 操作类型，固定为 query（查询）。可选值：`query`
- `paragraph_index` (number, 必填): 段落索引，从 1 开始

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "border_info": [
      {"side": -1, "line_style": 1, "line_width": 4, "color": -16777216},
      {"side": -3, "line_style": 5, "line_width": 4, "color": -16777216},
      {"side": -2, "line_style": 1, "line_width": 4, "color": -16777216},
      {"side": -4, "line_style": 1, "line_width": 4, "color": -16777216}
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

