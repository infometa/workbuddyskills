# wps.lists.custom_bullet

## 1. wps.lists.custom_bullet

#### 功能说明

设置在线文字文档自定义项目符号。

> paragraph_index 为 1-based；可由 wps.texts.range（段落 → begin/end）或 wps.texts.search 定位后换算。

#### 调用示例

段落设置：

```json
{
  "file_id": "<FILE_ID>",
  "bullet_font_name": "smoke",
  "bullet_symbol": "smoke",
  "paragraph_index": 1
}
```

#### 参数说明

- `bullet_font_name` (string, 必填): 项目符号字体
- `bullet_symbol` (string, 必填): 项目符号
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `paragraph_index` (number, 必填): 段落索引
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
