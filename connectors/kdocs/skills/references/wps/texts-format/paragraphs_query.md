# wps.texts.format

#### 功能说明

按段落查询格式信息

**幂等性**：是 — safe

> 返回 format_info（段落当前实际生效的格式值）：paragraph_index(段落索引)、alignment(对齐枚举)、first_line_indent/left_indent/right_indent(首行/左/右缩进)、line_spacing/line_spacing_rule(行距及行距规则)、space_before/space_after(段前/段后间距)、outline_level(大纲级别)、keep_with_next/keep_together/page_break_before/widow_control(分页相关布尔)。
> 查询返回的是段落当前实际值，可直接用于「统一格式」「格式对比」等场景；写入请用 verb=update（paragraphs 或 ranges）。

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
    "format_info": {
      "paragraph_index": 1,
      "alignment": 3,
      "line_spacing": 12,
      "outline_level": 10
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

