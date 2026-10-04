# otl.block_query

## 1. otl.block_query

#### 功能说明

查询指定块的结构与内容，适合在更新前先读取目标块信息。

> 查询得到的块类型和属性具体含义可参考 `references/otl/node.md`

#### 调用示例

查询文档根块（获取文档完整内容）：

```json
{
  "file_id": "string",
  "params": {
    "blockIds": [
      "doc"
    ]
  }
}
```

查询指定块（blockId 来自查询文档根块的返回结果）：

```json
{
  "file_id": "string",
  "params": {
    "blockIds": [
      "目标blockId"
    ]
  }
}
```

#### 参数说明

- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 智能文档 URL
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 智能文档分享链接 ID
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 智能文档 ID
- `params` (object, 必填): 查询参数对象
  - `blockIds` (array, 常用): 要查询的块 ID 列表

#### 返回值说明

```json
{
  "code": 0,
  "data": {
    "detail": {
      "name": "block.query",
      "params": { "blockIds": ["doc"] },
      "result": {
        "blocks": [
          {
            "attrs": { "cover": {} },
            "content": [
              {
                "id": "qFtRDQ",
                "type": "title",
                "attrs": { "align": 1 },
                "content": [{ "content": "文档标题", "type": "text" }]
              },
              {
                "id": "Vm4Bd7",
                "type": "heading",
                "attrs": { "align": 1, "level": 1 },
                "content": [{ "content": "第一章", "type": "text" }]
              },
              {
                "id": "J4PleN",
                "type": "paragraph",
                "attrs": { "align": 1 },
                "content": [{ "content": "正文内容", "type": "text" }]
              }
            ]
          }
        ]
      }
    }
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.detail.result.blocks` | array | 块数组，根块的 content 包含所有子块 |
