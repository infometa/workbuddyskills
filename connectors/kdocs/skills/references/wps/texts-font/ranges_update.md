# wps.texts.font

#### 功能说明

按字符区间设置字体

**幂等性**：是 — safe

> 写操作报 500002 且读操作正常时，先排查文档保护态（wps.protection.disable 后重试），再排查参数；不要盲目重试。
> begin/end 为 0-based 字符区间，begin=0 表示文档首字符。
> font_style 字段：font_name(字体名)、font_size(磅值)、bold/italic/strike_through/double_strike_through/superscript/subscript(布尔)、spacing(字距)、scaling(缩放百分比)。
> underline 只接受数字（WdUnderline：0=无、1=单线、2=仅词下划线、3=双线、4=点线、6=粗单线、7=虚线、9=点划、11=波浪线）；字符串如 single 不生效（解析为 0）。
> color_index 接受颜色名或数字：black/blue/red/yellow/green/white/auto 等，或 WdColorIndex 数字。

#### 调用示例

字符区间设置：

```json
{
  "file_id": "<FILE_ID>",
  "scope": "ranges",
  "verb": "update",
  "begin": 1,
  "end": 12,
  "font_style": {
    "bold": true
  }
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 ranges（按字符区间设置）。可选值：`ranges`
- `verb` (string, 必填): 动作，固定为 update（设置）。可选值：`update`
- `begin` (number, 可选): 区间起始位置（0-based）
- `end` (number, 可选): 区间结束位置（0-based）
- `font_style` (object, 可选): 字体样式对象

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "font_style": {
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

