# wps.shapes.text_box

## 1. wps.shapes.text_box

#### 功能说明

插入在线文字文档形状的文本框。

**幂等性**：是 — safe

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>",
  "height": 50,
  "left": 72,
  "top": 72,
  "width": 100
}
```

#### 参数说明

- `begin` (number, 可选): 锚定起点（0-based，不传锚文档起始）
- `end` (number, 可选): 锚定终点（0-based，不传锚文档起始）
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `height` (number, 可选): 高度
- `left` (number, 可选): left
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `top` (number, 可选): top
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `width` (number, 可选): 宽度

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "info": {
      "height": 50,
      "index": 5,
      "left": 72,
      "name": "TextBox 5",
      "shape_item": "5",
      "top": 72,
      "type": 17,
      "width": 100
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
