# wps.footnote_endnotes.endnote_by_range

## 1. wps.footnote_endnotes.endnote_by_range

#### 功能说明

插入在线文字文档脚注/尾注的区间插入尾注。

**幂等性**：是 — safe

> 脚注与尾注是两套数据；测 endnote_* 前须 endnote_by_paragraph 或 endnote_by_range insert。

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>",
  "range": {
    "begin": 1,
    "end": 5
  },
  "text": "smoke example text"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `range` (object, 可选): range
- `text` (string, 可选): 文本内容
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "item": {
      "begin": 5,
      "end": 6,
      "index": 1,
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
