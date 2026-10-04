# wps.shapes.paragraph_font

## 1. wps.shapes.paragraph_font

#### 功能说明

设置在线文字文档形状内段落字体样式。

**幂等性**：是 — safe

> shape_item 应来自 wps.shapes.list 中文本框（type=17）的 shape_item。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "key": "Bold",
  "shape_item": "1.2",
  "shape_paragraph_index": 1,
  "value": "true"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `key` (string, 可选): 属性名
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `shape_item` (string, 可选): shape item
- `shape_paragraph_index` (number, 可选): shape paragraph index
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `value` (string, 可选): 属性值

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "info": {
      "index": 0,
      "name": "",
      "shape_item": "1.2",
      "type": 0
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
