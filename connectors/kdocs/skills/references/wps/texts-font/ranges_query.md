# wps.texts.font

#### 功能说明

按字符区间查询字体信息

**幂等性**：是 — safe

> begin/end 为 0-based 字符区间（与 wps.texts.search 返回的 ranges 同口径，可直接回填）；begin=0 表示文档首字符。
> 返回 font_style_info（当前生效值）：font_name(字体名)、font_size(磅值)、bold/italic/strike_through/double_strike_through/superscript/subscript(布尔)、color_index(颜色名或数字)、highlight_color(高亮)、underline(数字枚举)、spacing(字距)、scaling(缩放百分比)。
> color_index 字段为 WdColorIndex 口径（颜色名或数字：0=自动/黑、2=蓝、6=红等，见 enums.md）；若为数字且取值超出 WdColorIndex 范围，则为 WdColor BGR 十进制（value = B*65536 + G*256 + R，蓝色=16711680、红色=255）。
> font_style_info.highlight_color 为读回回显；设置高亮不能走本工具的 update（报 400100），必须用 wps.texts.highlight。
> 字符区间上的直接字符格式（run 级覆盖）可被本接口读到，无需导出文档解析 XML。

#### 调用示例

字符区间查询：

```json
{
  "file_id": "<FILE_ID>",
  "scope": "ranges",
  "verb": "query",
  "begin": 1,
  "end": 12
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 ranges（按字符区间查询）。可选值：`ranges`
- `verb` (string, 必填): 动作，固定为 query（查询）。可选值：`query`
- `begin` (number, 必填): 区间起始位置（0-based 字符偏移，与 wps.texts.search 返回的 ranges 一致，可直接回填；0 表示文档首字符）
- `end` (number, 必填): 区间结束位置（0-based 字符偏移，不含该字符；与 wps.texts.search 返回的 ranges 一致，可直接回填）

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "font_style_info": {
      "font_name": "Arial",
      "font_size": 10.5,
      "underline": "0",
      "underline_color": 6,
      "emphasis_mark": 2,
      "gradient": {
        "fill_type": 1,
        "gradient_style": 1,
        "gradient_variant": 1,
        "fore_color": 255,
        "back_color": 16711680
      },
      "color_index": "0",
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

