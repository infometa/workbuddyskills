# wps.texts.font_gradient

## 1. wps.texts.font_gradient

#### 功能说明

设置在线文字文档指定字符区间文字的双色渐变填充（自定义起止两色）。

**幂等性**：是 — safe

> 写操作报 500002 且读操作正常时，先排查文档保护态（wps.protection.disable 后重试），再排查参数；不要盲目重试。
> begin/end 为 0-based 字符区间（与 wps.texts.search 返回的 ranges 同口径，可直接回填）；begin=0 表示文档首字符。
> fore_color/back_color 为对象：r/g/b 各 0-255 整数；渐变方向由 style/variant 决定。
> 当前 w9s 内核（2026-08-24 构建）对文字 Fill.TwoColorGradient 为未实现桩，调用会报 500410002 内核错误；内核绑定后本工具无需改动即可生效。

#### 调用示例

字符区间红→蓝渐变：

```json
{
  "file_id": "<FILE_ID>",
  "begin": 0,
  "end": 8,
  "fore_color": {
    "r": 255,
    "g": 0,
    "b": 0
  },
  "back_color": {
    "r": 0,
    "g": 0,
    "b": 255
  },
  "style": 1,
  "variant": 1
}
```

#### 参数说明

- `begin` (number, 必填): 区间起始位置（0-based 字符偏移，与 wps.texts.search 返回的 ranges 一致，可直接回填；0 表示文档首字符）
- `end` (number, 必填): 区间结束位置（0-based 字符偏移，不含该字符）
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `fore_color` (object, 必填): 起始色 RGB 对象：{r,g,b} 各 0-255 整数
- `back_color` (object, 必填): 结束色 RGB 对象：{r,g,b} 各 0-255 整数
- `style` (number, 可选): 渐变样式 MsoGradientStyle：1 水平 / 2 垂直 / 3 对角线向上 / 4 对角线向下 / 5 从角落 / 7 从中心。可选值：`1` / `2` / `3` / `4` / `5` / `7`；默认值：`1`
- `variant` (number, 可选): 渐变变体 1-4（style=7 从中心时 1-2）；默认值：`1`
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "content": "{\"begin\":0,\"end\":8,\"fill_type\":4,\"gradient_style\":1,\"gradient_variant\":1,\"fore_color\":255,\"back_color\":16711680}"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 渐变读回（content 为 JSON 字符串：fill_type/gradient_style/gradient_variant/fore_color/back_color/​begin/end） |
| `message` | string | 结果说明 |
