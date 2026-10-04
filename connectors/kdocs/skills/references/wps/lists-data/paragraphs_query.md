# wps.lists.data

#### 功能说明

按段落查询列表信息

**幂等性**：是 — safe

> 返回段落当前列表信息 list_info：paragraph_index(段落索引)、list_type(列表类型枚举，如 1=无序/2=编号/3=大纲)、list_type_name(列表类型名称)、list_level_number(列表层级)、list_string(编号/符号文本)。非列表段落返回空。

#### 调用示例

段落查询：

```json
{
  "file_id": "<FILE_ID>",
  "scope": "paragraphs",
  "verb": "query",
  "paragraph_index": 1
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 paragraphs（按段落查询）。可选值：`paragraphs`
- `verb` (string, 必填): 动作，固定为 query（查询）。可选值：`query`
- `paragraph_index` (number, 必填): 段落索引，从 1 开始

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "list_info": {
      "paragraph_index": 1,
      "list_type": 0,
      "list_type_name": "wdListNoNumbering",
      "list_level_number": 1,
      "list_string": ""
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

