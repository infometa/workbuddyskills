# wps.content_controls.rich_text

## 1. wps.content_controls.rich_text

#### 功能说明

插入在线文字文档内容控件的富文本。

**幂等性**：是 — safe

> 各类型 insert 的 range 区间勿重叠（checkbox/date_picker/dropdown/plain_text/rich_text 各占不同偏移）。

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>",
  "range": {
    "begin": 121,
    "end": 129
  },
  "tag": "smoke-cc",
  "title": "SmokeCC"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `range` (object, 可选): range
- `tag` (string, 可选): tag
- `title` (string, 可选): title
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "item": {
      "index": 4,
      "tag": "smoke-cc",
      "title": "SmokeCC",
      "type": 0,
      "value": "0"
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
