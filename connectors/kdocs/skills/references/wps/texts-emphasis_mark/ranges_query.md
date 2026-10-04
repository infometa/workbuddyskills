# wps.texts.emphasis_mark

#### 功能说明

查询区间着重号（font_style_info）

**幂等性**：是 — safe

> JSAPI 依据 Font.EmphasisMark

#### 调用示例

查询区间着重号：

```json
{
  "file_id": "<FILE_ID>",
  "verb": "query",
  "begin": 23,
  "end": 36
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一
- `verb` (string, 必填): 操作类型，固定为 query（查询）。可选值：`query`
- `begin` (number, 可选): 区间起始位置（0-based 字符偏移，与 wps.texts.search 返回的 ranges 一致）
- `end` (number, 可选): 区间结束位置（0-based 字符偏移，不含该字符）

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "font_style_info": {
      "emphasis_mark": 2
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |

