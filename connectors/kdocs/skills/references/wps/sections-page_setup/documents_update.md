# wps.sections.page_setup

#### 功能说明

设置节的节页面设置

**幂等性**：是 — safe

> key 仅接受 PageSetup 的 PascalCase 属性（PageWidth/PageHeight/Orientation/TopMargin/BottomMargin/LeftMargin/RightMargin/Gutter/HeaderDistance/FooterDistance/SectionStart/VerticalAlignment/LinesPage）；其它 key（如 Bold）不报错但不生效。
> 先设 Orientation 再设宽高/边距：Orientation 会联动交换宽高与上下左右边距（0=纵向、1=横向）。
> value 为数值（长度/边距单位磅）；query/update 响应中的 page_setup 字段为 snake_case，写侧 key 为 PascalCase，二者不同名。

#### 调用示例

文档设置（横向 A4：先 Orientation 后宽高）：

```json
{
  "file_id": "<FILE_ID>",
  "key": "Orientation",
  "section_index": 1,
  "value": 1,
  "verb": "update"
}
```

文档设置（页宽）：

```json
{
  "file_id": "<FILE_ID>",
  "key": "PageWidth",
  "section_index": 1,
  "value": 595.3,
  "verb": "update"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): 操作类型，固定为 update（更新）。可选值：`update`
- `key` (string, 可选): 属性名（PascalCase，仅接受 PageSetup 属性）：PageWidth / PageHeight / Orientation（0=纵向、1=横向）/ TopMargin / BottomMargin / LeftMargin / RightMargin / Gutter / HeaderDistance / FooterDistance / SectionStart / VerticalAlignment / LinesPage；其它 key 无效。注意先设 Orientation 再设宽高/边距（Orientation 会联动交换宽高与上下左右边距）。可选值：`PageWidth` / `PageHeight` / `Orientation` / `TopMargin` / `BottomMargin` / `LeftMargin` / `RightMargin` / `Gutter` / `HeaderDistance` / `FooterDistance` / `SectionStart` / `VerticalAlignment` / `LinesPage`
- `section_index` (number, 可选): 节索引，从 1 开始
- `value` (number, 可选): 属性值（数值；长度/边距单位为磅）

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "page_setup": {
      "bottom_margin": 72,
      "footer_distance": 49.599998474121094,
      "gutter": 1,
      "header_distance": 42.54999923706055,
      "left_margin": 90,
      "lines_page": 1,
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

