# wps.tocs.figures

## 1. wps.tocs.figures

#### 功能说明

插入在线文字文档图表目录。

> 须先 insert 目录再 query/update/delete；无目录时 query 报 tableOfContents not found。

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>"
}
```

#### 参数说明

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
