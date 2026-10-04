# wps.tables.cell_font

#### 功能说明

查询单元格字体信息

**幂等性**：是 — safe

> 返回 font_style_info（单元格当前实际生效的字体值）：font_name(字体名)、font_size(磅值)、bold/italic/strike_through/double_strike_through/superscript/subscript(布尔)、color/color_index(数值颜色)、underline(数字枚举)、spacing(字距)、scaling(缩放百分比)。

#### 调用示例

单元格查询：

```json
{
  "file_id": "<FILE_ID>",
  "verb": "query",
  "table_index": 1,
  "row": 1,
  "col": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): 操作类型，固定为 query（查询）。可选值：`query`
- `col` (number, 可选): 列号
- `row` (number, 可选): 行号
- `table_index` (number, 必填): 表格索引，从 1 开始

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "font_style_info": {
      "font_name": "Arial",
      "font_size": 22,
      "bold": true
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

