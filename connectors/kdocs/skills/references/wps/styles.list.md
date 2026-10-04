# wps.styles.list

## 1. wps.styles.list

#### 功能说明

查询在线文字文档样式列表。

#### 调用示例

文档查询：

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
  "data": {
    "count": 15,
    "styles": [
      {
        "name": "正文",
        "type": "paragraph",
        "type_value": 1,
        "built_in": true
      },
      {
        "name": "标题 1",
        "type": "paragraph",
        "type_value": 1,
        "built_in": true
      },
      {
        "name": "标题 2",
        "type": "paragraph",
        "type_value": 1,
        "built_in": true
      },
      {
        "name": "标题 3",
        "type": "paragraph",
        "type_value": 1,
        "built_in": true
      },
      {
        "name": "标题 4",
        "type": "paragraph",
        "type_value": 1,
        "built_in": true
      },
      {
        "name": "标题 5",
        "type": "paragraph",
        "type_value": 1,
        "built_in": true
      },
      {
        "name": "标题 6",
        "type": "paragraph",
        "type_value": 1,
        "built_in": true
      },
      {
        "name": "标题 7",
        "type": "paragraph",
        "type_value": 1,
        "built_in": true
      },
      {
        "name": "标题 8",
        "type": "paragraph",
        "type_value": 1,
        "built_in": true
      },
      {
        "name": "标题 9",
        "type": "paragraph",
        "type_value": 1,
        "built_in": true
      },
      {
        "name": "批注文字",
        "type": "paragraph",
        "type_value": 1,
        "built_in": true
      },
      {
        "name": "普通表格",
        "type": "table",
        "type_value": 3,
        "built_in": true
      },
      {
        "name": "网格型",
        "type": "table",
        "type_value": 3,
        "built_in": true
      },
      {
        "name": "默认段落字体",
        "type": "character",
        "type_value": 2,
        "built_in": true
      },
      {
        "name": "SmokeStyleSlice",
        "type": "paragraph",
        "type_value": 1,
        "built_in": false
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
