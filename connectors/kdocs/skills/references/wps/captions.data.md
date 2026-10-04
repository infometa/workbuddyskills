# wps.captions.data

## 1. wps.captions.data

#### 功能说明

插入题注。定位方式二选一：table_index（1-based 表格索引）或 begin/end（0-based 字符区间）。

**幂等性**：是 — safe

> table_index 与 begin/end 二选一
> 题注默认不居中：需要居中排版时，插入成功后追加调用 wps.texts.alignment 对题注段落设置居中（TC_117）。
> 题注自动编号跟随 wps.captions.label 的标签编号体系顺序递增，不会自动跟随章节编号（如「图 3-1」需另行方案：用 label 组合或手动写标题文字）。
> table_index 与 begin/end 二选一，不可同时传（会 400001）。
> 表题注：先保证文档有表（wps.tables.count ≥ 1），只传 table_index。
> 段落/区间题注：只传 begin/end，不要带 table_index。
> label 需先用 wps.captions.label 创建，否则报 missing label。
> begin/end 为 0-based 字符区间；可由 wps.texts.search 返回的 ranges 回填。

#### 调用示例

文档插入：

```json
{
  "file_id": "<FILE_ID>",
  "label": "smoke",
  "position": 1,
  "table_index": 1,
  "title": "SmokeCC"
}
```

#### 参数说明

- `begin` (number, 可选): 区间起始位置（0-based），与 index/table_index 三选一
- `end` (number, 可选): 区间结束位置，与 index/table_index 三选一
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `index` (number, 可选): 内嵌图片（InlineShape）索引，从 1 开始；与 table_index/begin/end 三选一
- `label` (string, 可选): 题注标签，如「图」「表」
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `position` (number, 可选): 插入位置：0=上方，1=下方
- `table_index` (number, 可选): 表格索引（1-based），与 begin/end 二选一
- `title` (string, 可选): 题注标题文字
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "begin": 186,
    "end": 318
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
