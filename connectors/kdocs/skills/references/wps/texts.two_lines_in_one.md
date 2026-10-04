# wps.texts.two_lines_in_one

## 1. wps.texts.two_lines_in_one

#### 功能说明

设置在线文字文档文本的双行合一。

**幂等性**：是 — safe

> 写操作报 500002 且读操作正常时，先排查文档保护态（wps.protection.disable 后重试），再排查参数；不要盲目重试。
> begin/end 为 0-based 字符区间（与 wps.texts.search 返回的 ranges 同口径，可直接回填）；begin=0 表示文档首字符。
> 需传 two_lines_text；缺失报 missing text。
> 坐标时效：本工具按 begin/end 原位替换为目标字段，写入会使该位置之后的坐标整体偏移；批量场景每次写后必须重新 texts.search 定位。

#### 调用示例

字符区间设置：

```json
{
  "file_id": "<FILE_ID>",
  "begin": 1,
  "end": 12,
  "two_lines_text": "ab"
}
```

#### 参数说明

- `begin` (number, 可选): 区间起始位置（0-based 字符偏移，与 wps.texts.search 返回的 ranges 一致，可直接回填；0 表示文档首字符）
- `end` (number, 可选): 区间结束位置（0-based 字符偏移，不含该字符；与 wps.texts.search 返回的 ranges 一致，可直接回填）
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `two_lines_text` (string, 可选): two lines text
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
