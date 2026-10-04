# wps.footnote_endnotes.footnote_list

## 1. wps.footnote_endnotes.footnote_list

#### 功能说明

查询在线文字文档脚注列表。

**幂等性**：是 — safe

> 返回的 begin/end 为脚注引用标记在正文中的 0-based 字符位置，可直接回填到 wps.footnote_endnotes.footnote_by_range 的 range（begin/end）。

#### 调用示例

文档查询：

```json
{
  "file_id": "<FILE_ID>"
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "footnote_count": 1,
    "footnotes": [
      {
        "begin": 32,
        "end": 33,
        "index": 1,
        "reference": "",
        "text": "smoke footnote",
        "type": 0
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
