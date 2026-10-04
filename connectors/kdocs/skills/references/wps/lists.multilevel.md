# wps.lists.multilevel

## 1. wps.lists.multilevel

#### 功能说明

对字符区间应用大纲多级列表模板（先 RemoveNumbers 再 ApplyListTemplate，固定 gallery=3）。

> begin/end 为 0-based 字符区间；可由 wps.texts.search 返回的 ranges 回填。

#### 调用示例

字符区间设置：

```json
{
  "file_id": "<FILE_ID>",
  "begin": 1,
  "end": 12,
  "is_continue": true,
  "level": 1,
  "template_index": 1
}
```

#### 参数说明

- `begin` (number, 必填): 区间起点（0-based）
- `end` (number, 必填): 区间终点
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id
- `is_continue` (boolean, 可选): 是否续接上一列表
- `level` (number, 可选): 列表级别 1-9，默认 1
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id
- `template_index` (number, 可选): 大纲列表模板索引，从 1 起，默认 1
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL

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
