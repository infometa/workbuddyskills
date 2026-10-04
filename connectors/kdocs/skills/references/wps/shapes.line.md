# wps.shapes.line

## 1. wps.shapes.line

#### 功能说明

插入在线文字文档形状的线条。

**幂等性**：是 — safe

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>"
}
```

#### 参数说明

- `begin` (number, 可选): 锚定起点（0-based，不传锚文档起始）
- `end` (number, 可选): 锚定终点（0-based，不传锚文档起始）
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "info": {
      "index": 4,
      "name": "Straight Connector 4",
      "type": 9
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
