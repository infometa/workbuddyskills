# wps.tocs.format

## 1. wps.tocs.format

#### 功能说明

设置在线文字文档目录的格式。

**幂等性**：是 — safe

> toc_index 为 1-based；须先 insert 目录再 update。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "key": "Bold",
  "toc_index": 1,
  "value": "true"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `key` (string, 可选): 属性名
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `toc_index` (number, 可选): toc index
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `value` (string, 可选): 属性值

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "toc_index": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
