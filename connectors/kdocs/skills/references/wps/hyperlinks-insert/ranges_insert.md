# wps.hyperlinks.insert

#### 功能说明

按字符区间插入超链接

> 显示文字用 display_text；address 仅作跳转目标，勿把展示文本填在 address 里。
> ranges 定位传 begin/end；address 需为合法 URL，传错格式报 url does not contain /l/{link_id} or /p/{file_id}。
> begin/end 为 0-based 字符区间；可由 wps.texts.search 返回的 ranges 回填。

#### 调用示例

字符区间插入：

```json
{
  "file_id": "<FILE_ID>",
  "address": "https://example.com/smoke",
  "begin": 1,
  "display_text": "smoke link",
  "end": 74,
  "scope": "ranges"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 ranges（按字符区间设置）。可选值：`ranges`
- `address` (string, 必填): 超链接地址
- `begin` (number, 可选): 区间起点（scope=ranges 时必填）
- `display_text` (string, 必填): 显示文本
- `end` (number, 可选): 区间终点（scope=ranges 时必填）

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

