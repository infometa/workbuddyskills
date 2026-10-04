# wps.revisions.reject

## 1. wps.revisions.reject

#### 功能说明

拒绝指定修订。

**幂等性**：是 — safe

> 须先 wps.revisions.status enable=true 再改文产生修订。
> 单条 reject 宜在 accept_all/reject_all/all/by_author 等 bulk 操作之前。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "index": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `index` (number, 可选): 索引，从 1 开始
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "action": "Reject",
    "author": "未知",
    "index": 1,
    "text": "smoke revision editsmoke revision edit 2smoke revision editsmoke revision edit 2",
    "type": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
