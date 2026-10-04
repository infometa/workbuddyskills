# wps.shapes.text

#### 功能说明

设置形状文本

**幂等性**：是 — safe

> 文本类 update 应用 wps.shapes.list 中文本框类型（type=17）的 shape_item。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "verb": "update",
  "shape_item": "6",
  "text": "smoke example text"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): 操作类型，固定为 update（更新）。可选值：`update`
- `shape_item` (string, 可选): shape item
- `text` (string, 可选): 文本内容

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "info": {
      "index": 4,
      "name": "TextBox 6",
      "text": "smoke example text\r",
      "type": 17
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

