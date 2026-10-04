# wps.shapes.anchor

## 1. wps.shapes.anchor

#### 功能说明

查询在线文字文档浮动形状/图片的锚点段落（返回锚点段落的 1-based 段序号，对齐 JSAPI Shape.Anchor 所在段落）。

**幂等性**：是 — safe

#### 调用示例

文档查询：

```json
{
  "file_id": "<FILE_ID>",
  "shape_item": "3"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `shape_item` (string, 可选): shape item（顶层形状序号，如 "3"）
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "info": {
      "index": 3,
      "name": "Picture 7",
      "shape_item": "3",
      "type": 13,
      "anchor_paragraph": 3
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
