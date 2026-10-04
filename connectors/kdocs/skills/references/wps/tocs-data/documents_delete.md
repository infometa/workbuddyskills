# wps.tocs.data

#### 功能说明

按文档删除目录

> all delete 清空后 data delete 会 not found；宜先测 data delete。

#### 调用示例

文档删除：

```json
{
  "file_id": "<FILE_ID>",
  "scope": "documents",
  "toc_index": 1,
  "verb": "delete"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `scope` (string, 必填): 操作范围，固定为 documents（按文档设置）。可选值：`documents`
- `verb` (string, 必填): 操作类型，固定为 delete（删除）。可选值：`delete`
- `toc_index` (number, 可选): 目录索引

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

