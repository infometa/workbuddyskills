# wps.footnote_endnotes.footnote_by_paragraph

## 1. wps.footnote_endnotes.footnote_by_paragraph

#### 功能说明

插入在线文字文档脚注/尾注的段落插入脚注。

**幂等性**：是 — safe

> 脚注与尾注是两套数据；测 endnote_* 前须 endnote_by_paragraph 或 endnote_by_range insert。
> paragraph_index 为 1-based；可由 wps.texts.range（段落 → begin/end）或 wps.texts.search 定位后换算。

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>",
  "paragraph_index": 1,
  "text": "smoke example text"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `paragraph_index` (number, 可选): 段落索引，从 1 开始
- `text` (string, 可选): 文本内容
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "item": {
      "begin": 36,
      "end": 37,
      "index": 2,
      "reference": "",
      "text": "smoke example text",
      "type": 0
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
