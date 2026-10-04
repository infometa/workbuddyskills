# wps.comments.delete

## 1. wps.comments.delete

#### 功能说明

删除在线文字文档指定批注。

> index 为 1-based，须先存在批注；可用 wps.comments.list 取真实 index。

#### 调用示例

文档删除：

```json
{
  "file_id": "<FILE_ID>",
  "index": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `index` (number, 可选): 批注索引，从 1 开始，默认 1
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "deleted_count": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
