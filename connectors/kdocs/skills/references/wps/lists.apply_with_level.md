# wps.lists.apply_with_level

## 1. wps.lists.apply_with_level

#### 功能说明

批量按级别为多个段落应用列表模板（ApplyListTemplateWithLevel，单次 JS 执行以保证编号续接）。

> 所有段落的 ApplyListTemplateWithLevel 必须在同一次请求的 items 里完成；拆成多次调用会导致列表重新编号、无法续接。
> items[].is_continue：首项默认不续接，后续项默认续接；可按项覆盖。
> 大纲场景常用 gallery_type=3，template_index 从 1 起。
> 后端 items 走 raw JSON，勿对 items 二次 JSON 字符串转义。
> 多列表文档：各独立列表请分块调用（每次 items 只传一个列表块的段落），编号天然块内独立从 1 开始；可用 wps.lists.blocks 先枚举块范围。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "gallery_type": 1,
  "items": [
    {
      "paragraph_index": 1,
      "level": 1
    },
    {
      "paragraph_index": 1,
      "level": 2
    }
  ],
  "template_index": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `gallery_type` (number, 可选): 列表库：1=无序, 2=编号, 3=大纲，默认 3
- `items` (array, 必填): 段落列表：paragraph_index、level(1-9)、可选 is_continue
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `template_index` (number, 可选): 模板索引，从 1 起，默认 1
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "results": [
      {
        "paragraph_index": 1,
        "list_level": 1,
        "list_string": ""
      },
      {
        "paragraph_index": 1,
        "list_level": 2,
        "list_string": ""
      }
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
