# wps.content_controls.list

## 1. wps.content_controls.list

#### 功能说明

查询在线文字文档内容控件的列表。

**幂等性**：是 — safe

#### 调用示例

文档查询：

```json
{
  "file_id": "<FILE_ID>"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "count": 5,
    "items": [
      {
        "index": 1,
        "tag": "smoke-cc",
        "title": "SmokeCC",
        "type": 8,
        "value": "☐"
      },
      {
        "index": 2,
        "tag": "smoke-cc",
        "title": "SmokeCC",
        "type": 6,
        "value": ""
      },
      {
        "index": 3,
        "tag": "smoke-cc",
        "title": "SmokeCC",
        "type": 4,
        "value": "ke31smok"
      },
      {
        "index": 4,
        "tag": "smoke-cc",
        "title": "SmokeCC",
        "type": 0,
        "value": "0"
      },
      {
        "index": 5,
        "tag": "smoke-cc",
        "title": "SmokeCC",
        "type": 1,
        "value": "0"
      }
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
