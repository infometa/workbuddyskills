# wps.hyperlinks.insert

#### 功能说明

按段落插入超链接

> 显示文字用 display_text；address 仅作跳转目标，勿把展示文本填在 address 里。
> paragraphs 定位传 paragraph_index + position（before/after）；paragraph_index 可由 wps.texts.range 或 wps.texts.search 定位后换算。

#### 调用示例

段落插入：

```json
{
  "file_id": "<FILE_ID>",
  "address": "https://example.com/smoke",
  "display_text": "smoke link",
  "paragraph_index": 1,
  "scope": "paragraphs",
  "text": "smoke example text"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 paragraphs（按段落设置）。可选值：`paragraphs`
- `address` (string, 必填): 超链接地址
- `display_text` (string, 必填): 显示文本
- `paragraph_index` (number, 可选): 段落序号（scope=paragraphs 时必填，从 1 起）

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

