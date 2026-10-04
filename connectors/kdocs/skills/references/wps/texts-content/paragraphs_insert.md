# wps.texts.content

#### 功能说明

按段落插入文本内容

**幂等性**：是 — safe

> A/C gap: documents insert/delete TEXT_CONTENT
> 必须传 position（before/after）；缺失时报 unresolved placeholder in rendered js。
> position=after 为行内追加语义：文本追加在目标段落末尾，不会新起段落（TC_137 教训）；若需要新起段落，请改用 wps.texts.content ranges_insert 并在文本中带 \r（回车）作为段落分隔。

#### 调用示例

段落插入：

```json
{
  "file_id": "<FILE_ID>",
  "scope": "paragraphs",
  "verb": "insert",
  "paragraph_index": 1,
  "position": "after",
  "text": "smoke example text"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `scope` (string, 必填): 操作范围，固定为 paragraphs（按段落设置）。可选值：`paragraphs`
- `verb` (string, 必填): 操作类型，固定为 insert（插入）。可选值：`insert`
- `paragraph_index` (number, 可选): 段落索引，从 1 开始
- `position` (string, 可选): 插入位置：before/after
- `text` (string, 可选): 待插入文本

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

