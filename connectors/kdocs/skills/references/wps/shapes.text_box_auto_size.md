# wps.shapes.text_box_auto_size

## 1. wps.shapes.text_box_auto_size

#### 功能说明

设置在线文字文档形状的文本框自动调整大小。

**幂等性**：是 — safe

> 须先 insert 文本框；shape_item 来自 wps.shapes.list 中文本框项。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "auto_size": 1,
  "shape_item": "6"
}
```

#### 参数说明

- `auto_size` (number, 可选): auto size
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `shape_item` (string, 可选): shape item
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
