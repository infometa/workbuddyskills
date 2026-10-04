# wps.styles.definition

#### 功能说明

删除样式定义

#### 调用示例

文档删除：

```json
{
  "file_id": "<FILE_ID>",
  "style_name": "SmokeStyleSlice",
  "verb": "delete"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `verb` (string, 必填): 操作类型，固定为 delete（删除）。可选值：`delete`
- `style_name` (string, 必填): 样式名称

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

