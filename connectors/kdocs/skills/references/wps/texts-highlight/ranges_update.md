# wps.texts.highlight

#### 功能说明

按字符区间设置高亮

**幂等性**：是 — safe

> 写操作报 500002 且读操作正常时，先排查文档保护态（wps.protection.disable 后重试），再排查参数；不要盲目重试。
> begin/end 为 0-based 字符区间（与 wps.texts.search 返回的 ranges 同口径，可直接回填）；begin=0 表示文档首字符。
> end 为绝对字符位（半开区间 [begin, end)，不含 end），写后仅 [begin, end) 落盘；非目标区间不会被波及。
> font_style 需传 highlight_color（如 yellow）；传 highlight 字段报 font_style.highlight_color required。
> highlight_color 接受颜色名（含 wd 前缀，如 wdPink/wdRed）或 WdColorIndex 数字，两种口径等价：black=1、blue=2、turquoise=3、brightGreen=4、pink=5、red=6、yellow=7、white=8、darkBlue=9、teal=10、green=11、violet=12、darkRed=13、darkYellow=14、gray50=15、gray25=16、auto=9999998；未知名称会静默按 0 处理（无高亮），建议回读确认。
> 回读 highlight_color 时 9999999 表示区间内混合（部分高亮、部分无）；写前建议先探基线——部分样张自带高亮，写后非目标区间的既有高亮属于样张基线而非写扩散。

#### 调用示例

字符区间设置：

```json
{
  "file_id": "<FILE_ID>",
  "scope": "ranges",
  "begin": 1,
  "end": 12,
  "font_style": {
    "highlight_color": "yellow"
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
- `font_style` (object, 可选): 字体样式对象

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "font_style": {
      "highlight_color": "7"
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

