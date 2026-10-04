# wps.images.data

## 1. wps.images.data

#### 功能说明

删除在线文字文档图片的数据。注意：这是删除操作（删除指定图片），不是读取图片；查询请用 wps.images.info / wps.images.list。

**幂等性**：是 — safe

> wps.images.data 是删除 verb：执行会删除文档中的图片，勿当作读回通道使用；查询图片信息用 wps.images.info / wps.images.list。

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `index` (number, 可选): 要删除的图片索引，从 1 开始（操作前先用 wps.images.list 确认序号）
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
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
