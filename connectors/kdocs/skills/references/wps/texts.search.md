# wps.texts.search

## 1. wps.texts.search

#### 功能说明

在在线文字文档中搜索文本。

**幂等性**：是 — safe

> 全文定位工具：按文本查找返回 0-based 字符区间（ranges）。在调用任何 ranges 类插入/设置工具（wps.texts.content、wps.bookmarks.insert、wps.hyperlinks.insert、wps.comments.range_insert、wps.fields.by_range 等）之前，宜先用本工具拿到 begin/end。
> 返回的 ranges 为 0-based 字符区间（begin/end）；可直接回填到各 ranges 类插入/设置工具（如 wps.texts.content / wps.bookmarks.insert / wps.comments.range_insert）的 begin/end 参数，实现「先定位再写入」。
> 找不到匹配文本时返回 code=0 且 ranges 为空数组（不是 500002 错误；曾经的 500002 行为已修复）；先确认文档内容与 find_text 一致再调用写入类工具。
> find_text 含 ^（如 2^10、a^pb 字面量）已支持：模板按 Word Find 转义规则将 ^ 转义为 ^^ 后查找，可正常命中对应 ranges；通配符模式固定关闭（按字面文本查找）。
> 本工具不索引 OMath 公式内部文本：按公式内容搜索返回空 ranges，核验公式请用 wps.formulas.math verb=query（见 wps.formulas.math 说明，TC_118）。
> 坐标时效：返回的 begin/end 为文档当前状态坐标；任何一次插入/删除/区间写（含 Fields.Add 类效果）都会使后续坐标失效，多次写入场景每次写后必须重新 search 取新坐标。

#### 调用示例

文档搜索：

```json
{
  "file_id": "<FILE_ID>",
  "find_text": "SMOKE_SLICE_ANCHOR_2026-09-03",
  "is_all": true
}
```

#### 参数说明

- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `find_text` (string, 必填): 查找文本
- `is_all` (boolean, 可选): 是否查找全部
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "ranges": [
      {
        "begin": 0,
        "end": 29
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
