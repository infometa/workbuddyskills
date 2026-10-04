# wps.texts.theme_color

## 1. wps.texts.theme_color

#### 功能说明

设置在线文字文档文本的主题色。

**幂等性**：是 — safe

> 写操作报 500002 且读操作正常时，先排查文档保护态（wps.protection.disable 后重试），再排查参数；不要盲目重试。
> theme_color_index 为 WdThemeColorIndex（JSAPI Font.TextColor.ObjectThemeColor）：0/2=深色主色1/2，1/3=浅色主色1/2，4~9=强调色1~6，10=超链接，11=已访问超链接，12/14=背景色1/2，13/15=文本色1/2，-1=无主题色。

#### 调用示例

段落设置：

```json
{
  "file_id": "<FILE_ID>",
  "paragraph_index": 1,
  "theme_color_index": 4
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `paragraph_index` (number, 必填): 段落索引，从 1 开始
- `theme_color_index` (number, 可选): 主题色索引 WdThemeColorIndex：0=深色主色1 / 1=浅色主色1 / 2=深色主色2 / 3=浅色主色2 / 4=强调色1 / 5=强调色2 / 6=强调色3 / 7=强调色4 / 8=强调色5 / 9=强调色6 / 10=超链接 / 11=已访问超链接 / 12=背景色1 / 13=文本色1 / 14=背景色2 / 15=文本色2 / -1=无主题色。
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
