# wps.revisions.status

#### 功能说明

修订模式开关读回

**幂等性**：是 — safe

> 读回值为当前修订模式开关状态，用于写入后的独立确证。

#### 调用示例

状态查询：

```json
{
  "file_id": "<FILE_ID>",
  "verb": "query"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): 操作类型，固定为 query（查询）。可选值：`query`

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {"status": true}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

