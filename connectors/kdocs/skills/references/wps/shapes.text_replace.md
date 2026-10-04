# wps.shapes.text_replace

## 1. wps.shapes.text_replace

#### 功能说明

设置在线文字文档形状内文本查找替换。

**幂等性**：是 — safe

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "find_text": "SMOKE_SLICE_ANCHOR_2026-09-03",
  "replace_text": "SMOKE",
  "shape_item": "1.2"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `find_text` (string, 可选): find text
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `replace_text` (string, 可选): replace text
- `shape_item` (string, 可选): shape item
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "info": {
      "index": 0,
      "name": "",
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
