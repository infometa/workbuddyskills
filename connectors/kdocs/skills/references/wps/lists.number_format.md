# wps.lists.number_format

## 1. wps.lists.number_format

#### 功能说明

为段落设置自定义编号格式（NumberStyle + NumberFormat），如中文「一、二、三…」（number_style=39，number_format="%1、"）。

> paragraph_index 为 1-based；可由 wps.texts.range（段落 → begin/end）或 wps.texts.search 定位后换算。

#### 调用示例

段落设置：

```json
{
  "file_id": "<FILE_ID>",
  "font_name": "Arial",
  "level": 1,
  "number_format": "smoke",
  "number_style": 1,
  "paragraph_index": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `font_name` (string, 可选): 编号字体，可选
- `level` (number, 可选): 列表级别 1-9，默认 1
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `number_format` (string, 必填): 编号格式，如 "%1、"
- `number_style` (number, 必填): NumberStyle 枚举，39=中文数字
- `paragraph_index` (number, 必填): 段落索引，从 1 起
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL

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
