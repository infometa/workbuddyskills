# wps.texts.structure

## 1. wps.texts.structure

#### 功能说明

批量查询在线文字文档段落结构（样式名/类型/大纲级别）。

> 批量查询段落结构（一次最多 100 段），返回每段的 style_name（样式名）、type/type_value（样式类型）、outline_level（大纲级别：0=正文，1-9=标题级别），用于构建文档结构树/大纲。
> 单段样式查询用 wps.texts.style；字符格式（字号/加粗/颜色）用 wps.texts.font scope=paragraphs/ranges verb=query。
> 一次最多查 100 段；段落索引 1-based。outline_level 用于构建结构树：0=正文，1-9=标题级别（Heading1-9）。
> 返回顺序与请求 paragraph_indexes 一致；无效索引会被内核截断到最大段落数。

#### 调用示例

段落batch_query：

```json
{
  "file_id": "<FILE_ID>",
  "paragraph_indexes": [
    1,
    2,
    3
  ]
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `paragraph_indexes` (array, 必填): 段落索引数组（1-based，1-100 个）
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "structures": [
      {
        "paragraph_index": 1,
        "style_name": "正文",
        "type": "paragraph",
        "type_value": 1,
        "built_in": true,
        "outline_level": 10
      },
      {
        "paragraph_index": 2,
        "style_name": "正文",
        "type": "paragraph",
        "type_value": 1,
        "built_in": true,
        "outline_level": 10
      },
      {
        "paragraph_index": 3,
        "style_name": "正文",
        "type": "paragraph",
        "type_value": 1,
        "built_in": true,
        "outline_level": 10
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
