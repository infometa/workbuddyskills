# wps.hyperlinks.address

## 1. wps.hyperlinks.address

#### 功能说明

更新在线文字文档超链接地址。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "index": 1,
  "key": "Bold",
  "value": "true"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `index` (number, 必填): 索引，从 1 开始
- `key` (string, 可选): 属性名，默认 Address
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `value` (string, 必填): 新的超链接地址

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
