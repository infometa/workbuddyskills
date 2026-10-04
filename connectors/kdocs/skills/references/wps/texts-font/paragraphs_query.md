# wps.texts.font

#### 功能说明

按段落查询字体信息

**幂等性**：是 — safe

> 返回 font_style_info（当前生效值，含段落级直接覆盖）：font_name(字体名)、font_size(磅值)、bold/italic/strike_through/double_strike_through/superscript/subscript(布尔)、color/color_index(数值颜色)、underline(数字枚举)、spacing(字距)、scaling(缩放百分比)。
> 若段落带直接字号覆盖（未走样式定义），本接口返回的是实际显示字号，可直接用于「放大一号」「统一字号」等场景。

#### 调用示例

段落查询：

```json
{
  "file_id": "<FILE_ID>",
  "scope": "paragraphs",
  "verb": "query",
  "paragraph_index": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 paragraphs（按段落查询）。可选值：`paragraphs`
- `verb` (string, 必填): 动作，固定为 query（查询）。可选值：`query`
- `paragraph_index` (number, 必填): 段落索引，从 1 开始

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "font_style_info": {
      "font_name": "Arial",
      "font_size": 10.5,
      "color": -16777216,
      "underline": "0",
      "scaling": 100
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

