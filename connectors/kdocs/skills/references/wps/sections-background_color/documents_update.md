# wps.sections.background_color

#### 功能说明

设置页面背景色

**幂等性**：是 — safe

> value 为 OLE RGB long（B*65536+G*256+R）或 "#RRGGBB" 字符串；WdColorIndex 不适用
> 背景仅在 Web 版式视图可见（JSAPI Document.Background.Fill 语义）
> 写侧执行 doc.Save() 落盘为异步生效，通常约 1 分钟内可被 query 读回

#### 调用示例

设置浅黄背景：

```json
{
  "file_id": "<FILE_ID>",
  "value": "#FFFDE7"
}
```

设置浅黄背景（RGB long）：

```json
{
  "file_id": "<FILE_ID>",
  "value": "15203839"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): query 查询 / update 设置（query 返回 background 专用字段）。可选值：`query` / `update`
- `value` (string, 可选): 颜色值口径：number 为 OLE RGB long（B*65536+G*256+R）；字符串为 CSS 十六进制 "#RRGGBB"（推荐）。WdColorIndex 数值不适用（会被按 RGB long 解释，如 wdYellow=7 写出近黑色）。浅黄推荐 "#FFFDE7"（OLE RGB=15203839）

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

