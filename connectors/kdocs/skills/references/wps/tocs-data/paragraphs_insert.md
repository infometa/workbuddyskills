# wps.tocs.data

#### 功能说明

按段落插入目录

> paragraph_index 为 1-based；可由 wps.texts.range（段落 → begin/end）或 wps.texts.search 定位后换算。

#### 调用示例

段落插入：

```json
{
  "file_id": "<FILE_ID>",
  "lower_level": 1,
  "paragraph_index": 1,
  "position": "after",
  "scope": "paragraphs",
  "upper_level": 1,
  "verb": "insert",
  "text": "smoke example text"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL
- `scope` (string, 必填): 操作范围，固定为 paragraphs（按段落设置）。可选值：`paragraphs`
- `verb` (string, 必填): 操作类型，固定为 insert（插入）。可选值：`insert`
- `lower_level` (number, 可选): 结束标题级别
- `paragraph_index` (number, 可选): 段落序号（scope=paragraphs 时必填，从 1 起）
- `position` (string, 可选): 插入位置：before/after
- `upper_level` (number, 可选): 起始标题级别

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "toc_index": 1
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

