# wps.texts.builtin_properties

#### 功能说明

设置文本的内置文档属性（标题、作者等）

**幂等性**：是 — safe

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "verb": "update",
  "author": "smoke",
  "keywords": "smoke",
  "subject": "smoke",
  "title": "SmokeCC"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): 操作类型，固定为 update（更新）。可选值：`update`
- `author` (string, 可选): author
- `keywords` (string, 可选): keywords
- `subject` (string, 可选): subject
- `title` (string, 可选): title

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "properties": {
      "author": "smoke",
      "keywords": "smoke",
      "subject": "smoke",
      "title": "SmokeCC"
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

