# wps.references.insert

## 1. wps.references.insert

#### 功能说明

在指定字符区间插入书签交叉引用（REF 域，指向 bookmark_name）。仅支持 reference_type=2（书签）；题注/标题/脚注等类型不支持，会报 400100 参数错误，请改用 bookmarks+hyperlinks 组合。

**幂等性**：是 — safe

> bookmark_name 在 reference_type=2 时必填；引用题注时填写 caption_label。
> 引用目标须已存在（题注/书签/标题等）；宜在 captions/bookmarks 之后调用。
> begin/end 为 0-based 字符区间；可由 wps.texts.search 返回的 ranges 回填。

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>",
  "begin": 1,
  "bookmark_name": "SmokeBookmark",
  "caption_label": "smoke",
  "end": 10,
  "insert_as_hyperlink": true,
  "reference_item": 1,
  "reference_kind": 1,
  "reference_type": 1,
  "separate_numbers": true
}
```

#### 参数说明

- `begin` (number, 必填): 插入位置起点（0-based）
- `bookmark_name` (string, 可选): 引用书签名称（reference_type=2 时必填）
- `caption_label` (string, 可选): 题注标签（引用题注时填写，如「图」「表」）
- `end` (number, 必填): 插入位置终点（0-based）
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `insert_as_hyperlink` (boolean, 可选): 是否作为超链接插入，默认 true
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `reference_item` (number, 可选): 引用项序号（1-based），默认 1
- `reference_kind` (number, 可选): WdReferenceKind，默认 -1（wdContentText）
- `reference_type` (number, 必填): WdReferenceType：0=编号项，1=标题，2=书签，3=脚注，4=尾注
- `separate_numbers` (boolean, 可选): 是否用分隔符分离编号与文本
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "field": {
      "code": " XE \"smoke index\" ",
      "index": 1,
      "result": "",
      "type": 4
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
