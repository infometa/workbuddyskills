# wps.lists.remove

## 1. wps.lists.remove

#### 功能说明

移除在线文字文档范围列表格式。

> begin/end 为 0-based 字符区间；可由 wps.texts.search 返回的 ranges 回填。

#### 调用示例

字符区间设置：

```json
{
  "file_id": "<FILE_ID>",
  "begin": 1,
  "end": 12
}
```

#### 参数说明

- `begin` (number, 必填): 范围起点
- `end` (number, 必填): 范围终点
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL

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
