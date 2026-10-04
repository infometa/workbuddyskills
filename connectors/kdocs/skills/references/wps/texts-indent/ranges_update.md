# wps.texts.indent

#### 功能说明

按字符区间设置缩进

**幂等性**：是 — safe

> 写操作报 500002 且读操作正常时，先排查文档保护态（wps.protection.disable 后重试），再排查参数；不要盲目重试。
> begin/end 为 0-based 字符区间（与 wps.texts.search 返回的 ranges 同口径，可直接回填）；begin=0 表示文档首字符。
> paragraph_style.indent 需对象，缺失报 paragraph_style.indent required。
> indent_type 与 unit 必须为字符串（proto string 字段）：传数字类型（如 3 而非 "3"）会报 400001 参数错误。
> indent_type 合法取值为数字字符串："1"=左缩进、"2"=右缩进、"3"=首行缩进。
> unit 合法取值为数字字符串："1"=磅(point)、"2"=字符(character)。
> 其它名称（如 first_line/firstLine/char）不被识别，会静默回落到默认值（indent_type→左缩进、unit→磅），不报错但不生效。
> indent_value 为缩进量数值，配合 unit 解释。

#### 调用示例

字符区间设置（首行缩进 2 字符）：

```json
{
  "file_id": "<FILE_ID>",
  "scope": "ranges",
  "begin": 1,
  "end": 12,
  "paragraph_style": {
    "indent": {
      "indent_type": "3",
      "indent_value": 2,
      "unit": "2"
    }
  }
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 ranges（按字符区间设置）。可选值：`ranges`
- `begin` (number, 可选): 区间起始位置（0-based 字符偏移，与 wps.texts.search 返回的 ranges 一致，可直接回填；0 表示文档首字符）
- `end` (number, 可选): 区间结束位置（0-based 字符偏移，不含该字符；与 wps.texts.search 返回的 ranges 一致，可直接回填）
- `paragraph_style` (object, 可选): 段落样式对象

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "paragraph_style": {
      "indent": {
        "indent_type": "3",
        "indent_value": 2,
        "unit": "2"
      }
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

