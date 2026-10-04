# wps.texts.underline_color

#### 功能说明

设置文本的下划线颜色

**幂等性**：是 — safe

> 写操作报 500002 且读操作正常时，先排查文档保护态（wps.protection.disable 后重试），再排查参数；不要盲目重试。
> underline_color 为 WdColor BGR 十进制（value = B*65536 + G*256 + R）：蓝色=16711680、红色=255、绿色=32768、auto（自动/随文字颜色）的数值口径为 -16777216（WdColor 自动值，读回时也以此值表示自动/随字色，TC_017）；与 WdColorIndex（1=黑、2=蓝）不是同一口径，勿混用。

#### 调用示例

字符区间下划线设为蓝色：

```json
{
  "file_id": "<FILE_ID>",
  "begin": 1,
  "end": 12,
  "underline_color": 16711680
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): HTTP 动作：query（查询）/ update（更新）。可选值：`query` / `update`
- `begin` (number, 可选): 区间起始位置（0-based 字符偏移，与 wps.texts.search 返回的 ranges 一致，可直接回填；0 表示文档首字符）
- `end` (number, 可选): 区间结束位置（0-based 字符偏移，不含该字符；与 wps.texts.search 返回的 ranges 一致，可直接回填）
- `underline_color` (number, 可选): 下划线颜色，WdColor BGR 十进制：value = B*65536 + G*256 + R（如蓝色=16711680、红色=255、自动=-16777216；勿用 WdColorIndex）。

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "font_style": {
      "underline": "0"
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

